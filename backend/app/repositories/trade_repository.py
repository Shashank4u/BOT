"""Trade and order data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Order, Trade, TradeStatus


class TradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_trades(
        self, account_id: int, status: str | None = None, limit: int = 100
    ) -> list[Trade]:
        q = select(Trade).where(Trade.account_id == account_id)
        if status:
            q = q.where(Trade.status == status)
        q = q.order_by(Trade.opened_at.desc()).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def list_closed_trades(
        self, account_id: int, since=None, limit: int = 1000
    ) -> list[Trade]:
        q = select(Trade).where(
            Trade.account_id == account_id,
            Trade.status == TradeStatus.CLOSED.value,
        )
        if since is not None:
            q = q.where(Trade.closed_at >= since)
        q = q.order_by(Trade.closed_at.asc()).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count_open_for_strategy(self, account_id: int, strategy_id: int) -> int:
        result = await self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.strategy_id == strategy_id,
                Trade.status == TradeStatus.OPEN.value,
            )
        )
        return len(list(result.scalars().all()))

    async def count_open_for_symbol(
        self, account_id: int, symbol: str, direction: str | None = None
    ) -> int:
        q = select(Trade).where(
            Trade.account_id == account_id,
            Trade.symbol == symbol.upper(),
            Trade.status == TradeStatus.OPEN.value,
        )
        if direction:
            q = q.where(Trade.direction == direction)
        result = await self._session.execute(q)
        return len(list(result.scalars().all()))

    async def list_open_for_strategy_symbol(
        self, account_id: int, strategy_id: int, symbol: str
    ) -> list[Trade]:
        result = await self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.strategy_id == strategy_id,
                Trade.symbol == symbol.upper(),
                Trade.status == TradeStatus.OPEN.value,
            )
        )
        return list(result.scalars().all())

    async def count_open(self, account_id: int) -> int:
        result = await self._session.execute(
            select(Trade).where(
                Trade.account_id == account_id,
                Trade.status == TradeStatus.OPEN.value,
            )
        )
        return len(list(result.scalars().all()))

    async def create_trade(self, trade: Trade) -> Trade:
        self._session.add(trade)
        await self._session.flush()
        await self._session.refresh(trade)
        return trade

    async def get_trade(self, trade_id: int) -> Trade | None:
        result = await self._session.execute(select(Trade).where(Trade.id == trade_id))
        return result.scalar_one_or_none()

    async def update_trade(self, trade: Trade) -> Trade:
        await self._session.flush()
        await self._session.refresh(trade)
        return trade


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_orders(self, account_id: int, limit: int = 100) -> list[Order]:
        result = await self._session.execute(
            select(Order)
            .where(Order.account_id == account_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_order(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.flush()
        await self._session.refresh(order)
        return order

    async def get_order(self, order_id: int) -> Order | None:
        result = await self._session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def update_order(self, order: Order) -> Order:
        await self._session.flush()
        await self._session.refresh(order)
        return order
