"""Historical bar replay and strategy backtest runner."""

from dataclasses import dataclass
from datetime import datetime

from app.core.logging import get_logger
from app.trading.backtest.metrics import calculate_trade_pnl, compute_metrics
from app.trading.backtest.types import BacktestResult, BacktestTrade
from app.trading.risk.calculator import calculate_lot_size
from app.trading.strategies.engine import StrategyEngine
from app.trading.strategies.types import SignalAction, StrategyConfig
from app.trading.types import OHLCBar

logger = get_logger(__name__)

WARMUP_BARS = 100


@dataclass
class _OpenPosition:
    direction: str
    entry_price: float
    entry_time: datetime
    lot_size: float
    stop_loss: float | None
    take_profit: float | None


class BacktestRunner:
    """
    Replays OHLC bars and simulates strategy signals with SL/TP exits.
    Uses the same StrategyEngine as live evaluation for consistency.
    """

    def __init__(self) -> None:
        self._engine = StrategyEngine()

    def run(
        self,
        config: StrategyConfig,
        symbol: str,
        bars: list[OHLCBar],
        initial_balance: float = 10000.0,
        bar_count: int | None = None,
    ) -> BacktestResult:
        if len(bars) < WARMUP_BARS + 10:
            raise ValueError(f"Need at least {WARMUP_BARS + 10} bars for backtest")

        balance = initial_balance
        trades: list[BacktestTrade] = []
        equity_curve: list[dict] = [{"time": bars[WARMUP_BARS].time.isoformat(), "equity": balance}]
        position: _OpenPosition | None = None

        start_idx = WARMUP_BARS
        end_idx = len(bars) if bar_count is None else min(len(bars), start_idx + bar_count)

        for i in range(start_idx, end_idx):
            bar = bars[i]
            window = bars[: i + 1]

            if position is not None:
                closed = self._check_exit(position, bar, symbol)
                if closed:
                    trade, exit_price, exit_reason = closed
                    balance += trade.profit_loss
                    trades.append(trade)
                    position = None
                    equity_curve.append({"time": bar.time.isoformat(), "equity": round(balance, 2)})

            if position is None:
                signal = self._engine.evaluate(config, symbol, window)
                if signal.action in (SignalAction.BUY, SignalAction.SELL):
                    sl_pips = config.stop_loss_pips or 20
                    sizing = calculate_lot_size(balance, config.max_risk_percent, sl_pips, symbol)
                    position = _OpenPosition(
                        direction=signal.action.value,
                        entry_price=bar.close,
                        entry_time=bar.time,
                        lot_size=sizing.lot_size,
                        stop_loss=signal.stop_loss,
                        take_profit=signal.take_profit,
                    )

        if position is not None:
            last_bar = bars[end_idx - 1]
            pnl = calculate_trade_pnl(
                symbol, position.direction, position.entry_price, last_bar.close, position.lot_size
            )
            trades.append(
                BacktestTrade(
                    direction=position.direction,
                    entry_price=position.entry_price,
                    exit_price=last_bar.close,
                    entry_time=position.entry_time,
                    exit_time=last_bar.time,
                    lot_size=position.lot_size,
                    profit_loss=pnl,
                    exit_reason="end_of_data",
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                )
            )
            balance += pnl
            equity_curve.append({"time": last_bar.time.isoformat(), "equity": round(balance, 2)})

        metrics = compute_metrics(trades, equity_curve, initial_balance)

        logger.info(
            "Backtest %s %s: %d trades, P/L=%.2f, PF=%s",
            symbol,
            config.strategy_type,
            metrics.total_trades,
            metrics.total_pnl,
            metrics.profit_factor,
        )

        return BacktestResult(
            symbol=symbol.upper(),
            timeframe=config.timeframe,
            initial_balance=initial_balance,
            start_date=bars[start_idx].time,
            end_date=bars[end_idx - 1].time,
            metrics=metrics,
            trades=trades,
            equity_curve=equity_curve,
        )

    def _check_exit(
        self,
        position: _OpenPosition,
        bar: OHLCBar,
        symbol: str,
    ) -> tuple[BacktestTrade, float, str] | None:
        """Check if SL or TP was hit on this bar."""
        if position.direction == "buy":
            if position.stop_loss and bar.low <= position.stop_loss:
                exit_price = position.stop_loss
                reason = "stop_loss"
            elif position.take_profit and bar.high >= position.take_profit:
                exit_price = position.take_profit
                reason = "take_profit"
            else:
                return None
        else:
            if position.stop_loss and bar.high >= position.stop_loss:
                exit_price = position.stop_loss
                reason = "stop_loss"
            elif position.take_profit and bar.low <= position.take_profit:
                exit_price = position.take_profit
                reason = "take_profit"
            else:
                return None

        pnl = calculate_trade_pnl(
            symbol, position.direction, position.entry_price, exit_price, position.lot_size
        )
        trade = BacktestTrade(
            direction=position.direction,
            entry_price=position.entry_price,
            exit_price=exit_price,
            entry_time=position.entry_time,
            exit_time=bar.time,
            lot_size=position.lot_size,
            profit_loss=pnl,
            exit_reason=reason,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
        )
        return trade, exit_price, reason
