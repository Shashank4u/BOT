"""Strategy business logic — CRUD, evaluation, sample seeding."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.strategy import Strategy, StrategyStatus
from app.models.user import User
from app.repositories.strategy_repository import StrategyRepository
from app.services.market_data import MarketDataService
from app.trading.strategies.engine import StrategyEngine
from app.trading.strategies.samples import SAMPLE_STRATEGIES, STRATEGY_TYPES
from app.trading.strategies.types import StrategyConfig, StrategySignal
from app.trading.types import Timeframe

logger = get_logger(__name__)

MIN_BARS = 100


class StrategyService:
    """Manage strategies and evaluate signals."""

    def __init__(
        self,
        session: AsyncSession,
        market: MarketDataService | None = None,
    ) -> None:
        self._session = session
        self._repo = StrategyRepository(session)
        self._market = market or MarketDataService()
        self._engine = StrategyEngine()

    async def _get_owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("Owner user not found — run bootstrap first")
        return user.id

    def list_sample_templates(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s["name"],
                "description": s["description"],
                "strategy_type": s["strategy_type"],
                "symbols": s["symbols"],
                "timeframes": s["timeframes"],
                "indicators": s["indicators"],
                "stop_loss_pips": s["stop_loss_pips"],
                "take_profit_pips": s["take_profit_pips"],
                "max_risk_percent": s["max_risk_percent"],
                "max_trades": s["max_trades"],
            }
            for s in SAMPLE_STRATEGIES
        ]

    async def list_strategies(self) -> list[Strategy]:
        user_id = await self._get_owner_id()
        return await self._repo.list_all(user_id)

    async def get_strategy(self, strategy_id: int) -> Strategy:
        user_id = await self._get_owner_id()
        strategy = await self._repo.get_by_id(strategy_id, user_id)
        if strategy is None:
            raise ValueError(f"Strategy {strategy_id} not found")
        return strategy

    async def create_strategy(self, data: dict[str, Any]) -> Strategy:
        user_id = await self._get_owner_id()
        strategy = Strategy(
            user_id=user_id,
            name=data["name"],
            description=data.get("description"),
            status=StrategyStatus.DRAFT.value,
            is_sample=False,
            symbols=data.get("symbols", []),
            timeframes=data.get("timeframes", ["H1"]),
            indicators=STRATEGY_TYPES.get(data["strategy_type"], {}).get("indicators", []),
            entry_conditions={"type": data["strategy_type"], "params": data.get("params", {})},
            exit_conditions=[],
            stop_loss_pips=data.get("stop_loss_pips"),
            take_profit_pips=data.get("take_profit_pips"),
            max_risk_percent=data.get("max_risk_percent", 1.0),
            max_trades=data.get("max_trades", 3),
            magic_number=data.get("magic_number", 100001),
        )
        return await self._repo.create(strategy)

    async def update_strategy(self, strategy_id: int, data: dict[str, Any]) -> Strategy:
        strategy = await self.get_strategy(strategy_id)
        if data.get("name") is not None:
            strategy.name = data["name"]
        if data.get("description") is not None:
            strategy.description = data["description"]
        if data.get("status") is not None:
            strategy.status = data["status"]
        if data.get("symbols") is not None:
            strategy.symbols = data["symbols"]
        if data.get("timeframes") is not None:
            strategy.timeframes = data["timeframes"]
        if data.get("params") is not None:
            entry = strategy.entry_conditions or {}
            entry["params"] = data["params"]
            strategy.entry_conditions = entry
        if data.get("stop_loss_pips") is not None:
            strategy.stop_loss_pips = data["stop_loss_pips"]
        if data.get("take_profit_pips") is not None:
            strategy.take_profit_pips = data["take_profit_pips"]
        if data.get("max_risk_percent") is not None:
            strategy.max_risk_percent = data["max_risk_percent"]
        if data.get("max_trades") is not None:
            strategy.max_trades = data["max_trades"]
        return await self._repo.update(strategy)

    async def delete_strategy(self, strategy_id: int) -> None:
        strategy = await self.get_strategy(strategy_id)
        if strategy.is_sample:
            raise ValueError("Cannot delete sample strategies — pause or archive instead")
        await self._repo.delete(strategy)

    async def seed_samples(self) -> dict[str, int]:
        user_id = await self._get_owner_id()
        created, skipped = 0, 0

        for sample in SAMPLE_STRATEGIES:
            existing = await self._repo.get_by_name(sample["name"], user_id)
            if existing:
                skipped += 1
                continue

            strategy = Strategy(
                user_id=user_id,
                name=sample["name"],
                description=sample["description"],
                status=StrategyStatus.PAUSED.value,
                is_sample=True,
                symbols=sample["symbols"],
                timeframes=sample["timeframes"],
                indicators=sample["indicators"],
                entry_conditions={
                    "type": sample["strategy_type"],
                    "params": sample["entry_conditions"]["params"],
                },
                exit_conditions=[],
                stop_loss_pips=sample["stop_loss_pips"],
                take_profit_pips=sample["take_profit_pips"],
                max_risk_percent=sample["max_risk_percent"],
                max_trades=sample["max_trades"],
                magic_number=sample["magic_number"],
            )
            await self._repo.create(strategy)
            created += 1

        await self._session.commit()
        logger.info("Seeded %d sample strategies (%d skipped)", created, skipped)
        return {"created": created, "skipped": skipped}

    async def evaluate_strategy(
        self,
        strategy_id: int,
        symbol: str,
        timeframe: Timeframe | None = None,
    ) -> StrategySignal:
        strategy = await self.get_strategy(strategy_id)
        config = StrategyConfig.from_model(strategy)
        if timeframe:
            config.timeframe = timeframe.value
        return self._evaluate(config, symbol)

    def evaluate_by_type(
        self,
        strategy_type: str,
        symbol: str,
        timeframe: Timeframe = Timeframe.H1,
        params: dict[str, Any] | None = None,
    ) -> StrategySignal:
        template = STRATEGY_TYPES.get(strategy_type)
        if template is None:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        config = StrategyConfig(
            name=template["name"],
            strategy_type=strategy_type,
            symbols=template["symbols"],
            timeframe=timeframe.value,
            params=params or template["entry_conditions"]["params"],
            stop_loss_pips=template.get("stop_loss_pips"),
            take_profit_pips=template.get("take_profit_pips"),
            max_risk_percent=template.get("max_risk_percent", 1.0),
            max_trades=template.get("max_trades", 3),
            magic_number=template.get("magic_number", 100001),
        )
        return self._evaluate(config, symbol, timeframe)

    def _evaluate(
        self,
        config: StrategyConfig,
        symbol: str,
        timeframe: Timeframe | None = None,
    ) -> StrategySignal:
        tf = timeframe or Timeframe(config.timeframe)
        bars = self._market.get_ohlc(symbol, tf, MIN_BARS + 60)
        bars = bars[-MIN_BARS:]

        logger.info(
            "Evaluating strategy '%s' (%s) on %s %s",
            config.name,
            config.strategy_type,
            symbol,
            tf.value,
        )
        return self._engine.evaluate(config, symbol, bars)


def strategy_to_response(strategy: Strategy) -> dict[str, Any]:
    entry = strategy.entry_conditions or {}
    return {
        "id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "status": strategy.status,
        "is_sample": strategy.is_sample,
        "strategy_type": entry.get("type", "unknown"),
        "symbols": strategy.symbols if isinstance(strategy.symbols, list) else [],
        "timeframes": strategy.timeframes if isinstance(strategy.timeframes, list) else [],
        "params": entry.get("params", {}),
        "stop_loss_pips": strategy.stop_loss_pips,
        "take_profit_pips": strategy.take_profit_pips,
        "max_risk_percent": strategy.max_risk_percent,
        "max_trades": strategy.max_trades,
        "magic_number": strategy.magic_number,
    }
