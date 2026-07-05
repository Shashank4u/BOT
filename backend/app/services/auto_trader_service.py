"""Auto-trading service — evaluate active strategies and place orders."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RiskViolationError
from app.core.logging import get_logger
from app.models.auto_trading import AutoTradingConfig
from app.models.strategy import Strategy
from app.models.user import User
from app.repositories.auto_trading_repository import AutoTradingRepository
from app.repositories.strategy_repository import StrategyRepository
from app.repositories.trade_repository import TradeRepository
from app.services.order_service import OrderService
from app.services.strategy_service import StrategyService
from app.trading.connection import get_provider
from app.trading.risk.calculator import calculate_lot_size
from app.trading.strategies.types import SignalAction
from app.trading.types import Timeframe

logger = get_logger(__name__)


@dataclass
class ScanResultItem:
    strategy_id: int
    strategy_name: str
    symbol: str
    action: str
    confidence: float
    executed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "executed": self.executed,
            "message": self.message,
        }


class AutoTraderService:
    """Run one auto-trading scan cycle across all active strategies."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._config_repo = AutoTradingRepository(session)
        self._strategy_repo = StrategyRepository(session)
        self._strategy_svc = StrategyService(session)
        self._order_svc = OrderService(session)
        self._trades = TradeRepository(session)

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def get_config(self) -> AutoTradingConfig:
        return await self._config_repo.get_or_create()

    async def set_enabled(self, enabled: bool) -> AutoTradingConfig:
        config = await self.get_config()
        config.enabled = enabled
        config.last_message = "Auto-trading started" if enabled else "Auto-trading stopped"
        if enabled:
            config.last_error = None
        return await self._config_repo.update(config)

    async def update_settings(
        self, interval_seconds: int | None = None, min_confidence: float | None = None
    ) -> AutoTradingConfig:
        config = await self.get_config()
        if interval_seconds is not None:
            config.interval_seconds = interval_seconds
        if min_confidence is not None:
            config.min_confidence = min_confidence
        return await self._config_repo.update(config)

    async def get_status(self) -> dict[str, Any]:
        config = await self.get_config()
        user_id = await self._owner_id()
        active = await self._strategy_repo.count_active(user_id)
        return {
            "enabled": config.enabled,
            "interval_seconds": config.interval_seconds,
            "min_confidence": config.min_confidence,
            "bot_status": self._bot_status(config, active),
            "active_strategies": active,
            "last_scan_at": config.last_scan_at,
            "last_message": config.last_message,
            "last_error": config.last_error,
            "orders_placed_last_scan": config.orders_placed_last_scan,
        }

    def _bot_status(self, config: AutoTradingConfig, active_strategies: int) -> str:
        if config.last_error:
            return "error"
        if not config.enabled:
            return "idle"
        if active_strategies == 0:
            return "waiting"
        return "running"

    async def run_scan(self) -> list[ScanResultItem]:
        """Evaluate all active strategies and execute qualifying signals."""
        config = await self.get_config()
        user_id = await self._owner_id()
        strategies = await self._strategy_repo.list_active(user_id)
        results: list[ScanResultItem] = []
        orders_placed = 0

        if not strategies:
            config.last_scan_at = datetime.now(UTC)
            config.last_message = "No active strategies — activate one in Strategies tab"
            config.orders_placed_last_scan = 0
            await self._config_repo.update(config)
            return results

        account = await self._order_svc._get_or_create_account()
        provider = get_provider()
        if not provider.get_status().connected:
            provider.connect()
        balance = provider.get_account_info().balance

        for strategy in strategies:
            symbols = strategy.symbols if isinstance(strategy.symbols, list) else ["EURUSD"]
            timeframes = (
                strategy.timeframes if isinstance(strategy.timeframes, list) else ["H1"]
            )
            for symbol in symbols:
                for tf_str in timeframes:
                    item = await self._process_symbol(
                        strategy, symbol.upper(), tf_str, config, account.id, balance
                    )
                    results.append(item)
                    if item.executed:
                        orders_placed += 1

        config.last_scan_at = datetime.now(UTC)
        config.orders_placed_last_scan = orders_placed
        config.last_error = None
        config.last_message = (
            f"Scan complete — {len(results)} evaluations, {orders_placed} orders placed"
        )
        await self._config_repo.update(config)
        logger.info(config.last_message)
        return results

    async def _process_symbol(
        self,
        strategy: Strategy,
        symbol: str,
        tf_str: str,
        config: AutoTradingConfig,
        account_id: int,
        balance: float,
    ) -> ScanResultItem:
        base = ScanResultItem(
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            symbol=symbol,
            action="hold",
            confidence=0.0,
            executed=False,
            message="",
        )

        try:
            tf = Timeframe(tf_str)
        except ValueError:
            base.message = f"Invalid timeframe: {tf_str}"
            return base

        try:
            signal = await self._strategy_svc.evaluate_strategy(strategy.id, symbol, tf)
        except Exception as exc:
            base.message = f"Evaluation failed: {exc}"
            return base

        base.action = signal.action.value
        base.confidence = signal.confidence

        if signal.action == SignalAction.HOLD:
            base.message = "Hold — no action"
            return base

        if signal.confidence < config.min_confidence:
            base.message = (
                f"Signal below min confidence ({signal.confidence:.2f} < {config.min_confidence})"
            )
            return base

        if signal.action in (SignalAction.BUY, SignalAction.SELL):
            return await self._try_open_trade(
                strategy, symbol, signal, config, account_id, balance, base
            )

        if signal.action == SignalAction.CLOSE_LONG:
            return await self._try_close_trades(
                strategy, symbol, "buy", base, "Auto-close long signal"
            )

        if signal.action == SignalAction.CLOSE_SHORT:
            return await self._try_close_trades(
                strategy, symbol, "sell", base, "Auto-close short signal"
            )

        base.message = f"Unhandled action: {signal.action.value}"
        return base

    async def _try_open_trade(
        self,
        strategy: Strategy,
        symbol: str,
        signal,
        config: AutoTradingConfig,
        account_id: int,
        balance: float,
        base: ScanResultItem,
    ) -> ScanResultItem:
        side = signal.action.value
        open_same = await self._trades.count_open_for_symbol(account_id, symbol, side)
        if open_same > 0:
            base.message = f"Already have open {side} on {symbol}"
            return base

        open_for_strategy = await self._trades.count_open_for_strategy(account_id, strategy.id)
        if open_for_strategy >= strategy.max_trades:
            base.message = f"Strategy max trades reached ({strategy.max_trades})"
            return base

        sl_pips = strategy.stop_loss_pips or 20
        tp_pips = strategy.take_profit_pips
        lot_result = calculate_lot_size(
            balance, strategy.max_risk_percent, sl_pips, symbol
        )
        lot_size = max(0.01, round(lot_result.lot_size, 2))

        entry_reason = (
            f"Auto-trade: {strategy.name} — {', '.join(signal.reasons[:2])}"
        )[:200]

        try:
            result = await self._order_svc.place_market_order(
                {
                    "symbol": symbol,
                    "side": side,
                    "lot_size": lot_size,
                    "stop_loss_pips": sl_pips,
                    "take_profit_pips": tp_pips,
                    "strategy_id": strategy.id,
                    "magic_number": strategy.magic_number,
                    "entry_reason": entry_reason,
                }
            )
        except RiskViolationError as exc:
            base.message = f"Risk blocked: {', '.join(exc.violations)}"
            return base
        except Exception as exc:
            base.message = f"Order failed: {exc}"
            return base

        if result.get("success"):
            base.executed = True
            base.message = f"Opened {side} {lot_size} lots @ {result.get('price')}"
        else:
            base.message = result.get("message", "Order rejected")

        return base

    async def _try_close_trades(
        self,
        strategy: Strategy,
        symbol: str,
        direction: str,
        base: ScanResultItem,
        exit_reason: str,
    ) -> ScanResultItem:
        account = await self._order_svc._get_or_create_account()
        trades = await self._trades.list_open_for_strategy_symbol(
            account.id, strategy.id, symbol
        )
        to_close = [t for t in trades if t.direction == direction]
        if not to_close:
            base.message = f"No open {direction} trades to close"
            return base

        closed = 0
        for trade in to_close:
            try:
                result = await self._order_svc.close_trade(
                    trade.id, {"exit_reason": exit_reason}
                )
                if result.get("success"):
                    closed += 1
            except Exception as exc:
                base.message = f"Close failed: {exc}"
                return base

        base.executed = closed > 0
        base.message = f"Closed {closed} {direction} trade(s)"
        return base
