"""Order execution service — risk checks, MT5 execution, DB recording."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import RiskViolationError
from app.core.logging import get_logger
from app.models.account import AccountType, TradingAccount
from app.models.trade import Order, OrderStatus, OrderType, Trade, TradeStatus
from app.models.user import User
from app.repositories.trade_repository import OrderRepository, TradeRepository
from app.notifications.service import NotificationService
from app.services.market_data import MarketDataService
from app.services.risk_service import RiskService
from app.trading.connection import get_provider
from app.trading.execution.order_executor import OrderExecutor
from app.trading.risk.calculator import pip_size
from app.trading.types import OrderRequest, OrderSide

logger = get_logger(__name__)


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._trades = TradeRepository(session)
        self._orders = OrderRepository(session)
        self._risk = RiskService(session)
        self._market = MarketDataService()
        self._executor = OrderExecutor()
        self._notify = NotificationService(session)

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def _get_or_create_account(self) -> TradingAccount:
        user_id = await self._owner_id()
        result = await self._session.execute(
            select(TradingAccount).where(TradingAccount.user_id == user_id).limit(1)
        )
        account = result.scalar_one_or_none()
        if account:
            return account

        settings = get_settings()
        account = TradingAccount(
            user_id=user_id,
            name="Demo Account",
            broker="XM",
            account_type=AccountType.DEMO.value,
            mt5_login=settings.mt5_login or 12345678,
            mt5_server=settings.mt5_server,
            encrypted_password="mock",
            balance=Decimal("10000"),
            equity=Decimal("10000"),
        )
        self._session.add(account)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def place_market_order(self, data: dict) -> dict:
        user_settings = await self._risk.get_settings()
        self._risk._manager.check_live_trading_allowed(user_settings)

        account = await self._get_or_create_account()
        provider = get_provider()
        if not provider.get_status().connected:
            provider.connect()

        account_info = provider.get_account_info()
        symbol = data["symbol"].upper()
        side = OrderSide(data["side"])
        lot_size = data["lot_size"]

        # Optional SL from pips
        sl, tp = data.get("stop_loss"), data.get("take_profit")
        if data.get("stop_loss_pips") and not sl:
            tick = provider.get_tick(symbol)
            price = tick.ask if side == OrderSide.BUY else tick.bid
            pip = pip_size(symbol)
            pips = data["stop_loss_pips"]
            sl = price - pips * pip if side == OrderSide.BUY else price + pips * pip

        if not data.get("skip_risk_check"):
            sl_pips = data.get("stop_loss_pips", 20)
            check = await self._risk.check_trade(
                symbol, lot_size, sl_pips, account_info.balance
            )
            if not check.allowed:
                await self._notify.notify_risk_alert(check.violations)
                raise RiskViolationError(check.violations)

        request = OrderRequest(
            symbol=symbol,
            side=side,
            lot_size=lot_size,
            stop_loss=sl,
            take_profit=tp,
            magic_number=data.get("magic_number", 100001),
            comment=(data.get("entry_reason") or "")[:31],
        )

        db_order = Order(
            account_id=account.id,
            symbol=symbol,
            order_type=(
                OrderType.MARKET_BUY.value if side == OrderSide.BUY else OrderType.MARKET_SELL.value
            ),
            lot_size=Decimal(str(lot_size)),
            stop_loss=Decimal(str(sl)) if sl else None,
            take_profit=Decimal(str(tp)) if tp else None,
            magic_number=data.get("magic_number", 100001),
        )
        await self._orders.create_order(db_order)

        result = self._executor.place_market(request)

        if result.success:
            db_order.status = OrderStatus.FILLED.value
            db_order.mt5_ticket = result.ticket
            trade = Trade(
                account_id=account.id,
                strategy_id=data.get("strategy_id"),
                mt5_ticket=result.ticket,
                symbol=symbol,
                direction=side.value,
                status=TradeStatus.OPEN.value,
                lot_size=Decimal(str(lot_size)),
                entry_price=Decimal(str(result.price)),
                stop_loss=Decimal(str(sl)) if sl else None,
                take_profit=Decimal(str(tp)) if tp else None,
                magic_number=data.get("magic_number", 100001),
                opened_at=datetime.now(UTC),
                entry_reason=data.get("entry_reason"),
            )
            await self._trades.create_trade(trade)
            db_order.trade_id = trade.id
            await self._orders.update_order(db_order)

            logger.info("Trade opened: %s %s %.2f @ %.5f", side.value, symbol, lot_size, result.price)
            await self._notify.notify_trade_opened(trade)
            return self._result_dict(result, db_order.id, trade.id)
        else:
            db_order.status = OrderStatus.REJECTED.value
            db_order.error_message = result.message
            db_order.retry_count = 3
            await self._orders.update_order(db_order)
            return self._result_dict(result, db_order.id, None)

    async def close_trade(self, trade_id: int, data: dict) -> dict:
        trade = await self._trades.get_trade(trade_id)
        if not trade or trade.status != TradeStatus.OPEN.value:
            raise ValueError(f"Open trade {trade_id} not found")
        if not trade.mt5_ticket:
            raise ValueError("Trade has no MT5 ticket")

        result = self._executor.close(trade.mt5_ticket, data.get("lot_size"))
        if result.success:
            trade.status = TradeStatus.CLOSED.value
            trade.exit_price = Decimal(str(result.price))
            trade.closed_at = datetime.now(UTC)
            trade.exit_reason = data.get("exit_reason")
            pip = pip_size(trade.symbol)
            diff = (
                float(trade.exit_price) - float(trade.entry_price)
                if trade.direction == "buy"
                else float(trade.entry_price) - float(trade.exit_price)
            )
            trade.profit_loss = Decimal(str(round(diff * float(trade.lot_size) * 100000, 2)))
            await self._trades.update_trade(trade)
            await self._notify.notify_trade_closed(trade)
        return self._result_dict(result, None, trade_id)

    async def list_trades(self, status: str | None = None) -> list[Trade]:
        account = await self._get_or_create_account()
        return await self._trades.list_trades(account.id, status)

    async def list_orders(self) -> list[Order]:
        account = await self._get_or_create_account()
        return await self._orders.list_orders(account.id)

    async def get_positions(self) -> list:
        provider = get_provider()
        if not provider.get_status().connected:
            provider.connect()
        return provider.get_positions()

    def _result_dict(self, result, order_id, trade_id) -> dict:
        return {
            "success": result.success,
            "order_id": order_id,
            "trade_id": trade_id,
            "mt5_ticket": result.ticket,
            "symbol": result.symbol,
            "side": result.side,
            "lot_size": result.lot_size,
            "price": result.price,
            "stop_loss": result.stop_loss,
            "take_profit": result.take_profit,
            "message": result.message,
            "is_demo": result.is_demo,
        }
