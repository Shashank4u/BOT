"""Backtest business logic."""

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.market import BacktestRun
from app.models.user import User
from app.repositories.backtest_repository import BacktestRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.market_data import MarketDataService
from app.trading.backtest.runner import BacktestRunner, WARMUP_BARS
from app.trading.strategies.samples import STRATEGY_TYPES
from app.trading.strategies.types import StrategyConfig
from app.trading.types import Timeframe

logger = get_logger(__name__)


class BacktestService:
    def __init__(
        self,
        session: AsyncSession,
        market: MarketDataService | None = None,
    ) -> None:
        self._session = session
        self._market = market or MarketDataService()
        self._runner = BacktestRunner()
        self._repo = BacktestRepository(session)
        self._strategy_repo = StrategyRepository(session)

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def run_backtest(self, data: dict[str, Any]) -> dict[str, Any]:
        user_id = await self._owner_id()
        symbol = data["symbol"].upper()
        timeframe = Timeframe(data.get("timeframe", "H1"))
        bar_count = int(data.get("bar_count", 500))
        initial_balance = float(data.get("initial_balance", 10000))

        config, strategy_id, strategy_name = await self._resolve_config(data, user_id)

        fetch_count = bar_count + WARMUP_BARS + 10
        bars = self._market.get_ohlc(symbol, timeframe, fetch_count)
        if len(bars) < WARMUP_BARS + 10:
            raise ValueError(f"Insufficient OHLC data for {symbol} — got {len(bars)} bars")

        result = self._runner.run(
            config=config,
            symbol=symbol,
            bars=bars,
            initial_balance=initial_balance,
            bar_count=bar_count,
        )

        run = BacktestRun(
            strategy_id=strategy_id or 0,
            user_id=user_id,
            symbol=symbol,
            timeframe=timeframe.value,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_balance=Decimal(str(initial_balance)),
            final_balance=Decimal(str(result.metrics.final_balance)),
            total_trades=result.metrics.total_trades,
            winning_trades=result.metrics.winning_trades,
            losing_trades=result.metrics.losing_trades,
            profit_factor=Decimal(str(result.metrics.profit_factor))
            if result.metrics.profit_factor is not None
            else None,
            sharpe_ratio=Decimal(str(result.metrics.sharpe_ratio))
            if result.metrics.sharpe_ratio is not None
            else None,
            max_drawdown=Decimal(str(result.metrics.max_drawdown)),
            expectancy=Decimal(str(result.metrics.expectancy)),
            average_win=Decimal(str(result.metrics.average_win)),
            average_loss=Decimal(str(result.metrics.average_loss)),
            results_json=result.to_dict(),
        )

        result_dict = result.to_dict()

        if strategy_id:
            saved = await self._repo.create(run)
            summary = self._run_summary(saved, strategy_name, result_dict)
            return {
                **summary,
                "trades": result_dict["trades"],
                "equity_curve": result_dict["equity_curve"],
                "results_json": result_dict,
                "disclaimer": result_dict["disclaimer"],
            }

        return {
            "id": 0,
            "strategy_id": None,
            "strategy_name": strategy_name,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "initial_balance": initial_balance,
            "final_balance": result.metrics.final_balance,
            "metrics": result.metrics.to_dict(),
            "total_trades": result.metrics.total_trades,
            "created_at": result.end_date.isoformat(),
            "trades": result_dict["trades"],
            "equity_curve": result_dict["equity_curve"],
            "results_json": result_dict,
            "disclaimer": result_dict["disclaimer"],
        }

    async def _resolve_config(
        self, data: dict[str, Any], user_id: int
    ) -> tuple[StrategyConfig, int | None, str]:
        if data.get("strategy_id"):
            strategy = await self._strategy_repo.get_by_id(data["strategy_id"], user_id)
            if not strategy:
                raise ValueError(f"Strategy {data['strategy_id']} not found")
            config = StrategyConfig.from_model(strategy)
            if data.get("timeframe"):
                config.timeframe = Timeframe(data["timeframe"]).value
            return config, strategy.id, strategy.name

        strategy_type = data.get("strategy_type", "ema_cross")
        template = STRATEGY_TYPES.get(strategy_type)
        if not template:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        config = StrategyConfig(
            name=template["name"],
            strategy_type=strategy_type,
            symbols=[data.get("symbol", "EURUSD").upper()],
            timeframe=Timeframe(data.get("timeframe", "H1")).value,
            params=data.get("params") or template["entry_conditions"]["params"],
            stop_loss_pips=template.get("stop_loss_pips"),
            take_profit_pips=template.get("take_profit_pips"),
            max_risk_percent=template.get("max_risk_percent", 1.0),
            max_trades=template.get("max_trades", 3),
            magic_number=template.get("magic_number", 100001),
        )
        return config, None, template["name"]

    async def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        user_id = await self._owner_id()
        runs = await self._repo.list_runs(user_id, limit)
        return [self._run_summary(r, r.strategy.name if r.strategy else None) for r in runs]

    async def get_run(self, run_id: int) -> dict[str, Any]:
        user_id = await self._owner_id()
        run = await self._repo.get_by_id(run_id, user_id)
        if not run:
            raise ValueError(f"Backtest run {run_id} not found")
        name = run.strategy.name if run.strategy else None
        summary = self._run_summary(run, name)
        results = run.results_json or {}
        return {
            **summary,
            "trades": results.get("trades", []),
            "equity_curve": results.get("equity_curve", []),
            "results_json": results,
            "disclaimer": results.get(
                "disclaimer",
                "Backtest results are simulated. Past performance does not guarantee future results.",
            ),
        }

    async def export_run(self, run_id: int) -> dict[str, Any]:
        detail = await self.get_run(run_id)
        return {
            "export_format": "json",
            "run_id": run_id,
            "exported_at": detail.get("created_at"),
            **detail,
        }

    def _run_summary(
        self,
        run: BacktestRun,
        strategy_name: str | None,
        results: dict | None = None,
    ) -> dict[str, Any]:
        results = results or run.results_json or {}
        metrics = results.get("metrics", {})
        return {
            "id": run.id,
            "strategy_id": run.strategy_id if run.strategy_id else None,
            "strategy_name": strategy_name,
            "symbol": run.symbol,
            "timeframe": run.timeframe,
            "start_date": run.start_date.isoformat(),
            "end_date": run.end_date.isoformat(),
            "initial_balance": float(run.initial_balance),
            "final_balance": float(run.final_balance),
            "metrics": metrics
            or {
                "total_trades": run.total_trades,
                "winning_trades": run.winning_trades,
                "losing_trades": run.losing_trades,
                "win_rate": round(run.winning_trades / run.total_trades * 100, 2)
                if run.total_trades
                else 0,
                "total_pnl": float(run.final_balance - run.initial_balance),
                "profit_factor": float(run.profit_factor) if run.profit_factor else None,
                "sharpe_ratio": float(run.sharpe_ratio) if run.sharpe_ratio else None,
                "max_drawdown": float(run.max_drawdown) if run.max_drawdown else 0,
                "expectancy": float(run.expectancy) if run.expectancy else 0,
                "average_win": float(run.average_win) if run.average_win else 0,
                "average_loss": float(run.average_loss) if run.average_loss else 0,
                "final_balance": float(run.final_balance),
                "return_percent": round(
                    (float(run.final_balance) - float(run.initial_balance))
                    / float(run.initial_balance)
                    * 100,
                    2,
                ),
            },
            "total_trades": run.total_trades,
            "created_at": run.created_at.isoformat(),
        }
