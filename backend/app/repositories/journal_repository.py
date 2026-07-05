"""Trade journal data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.trade import Trade, TradeJournal


class JournalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_journals(self, limit: int = 100) -> list[TradeJournal]:
        result = await self._session.execute(
            select(TradeJournal)
            .options(selectinload(TradeJournal.trade))
            .order_by(TradeJournal.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_trade_id(self, trade_id: int) -> TradeJournal | None:
        result = await self._session.execute(
            select(TradeJournal)
            .options(selectinload(TradeJournal.trade))
            .where(TradeJournal.trade_id == trade_id)
        )
        return result.scalar_one_or_none()

    async def get_trade(self, trade_id: int) -> Trade | None:
        result = await self._session.execute(select(Trade).where(Trade.id == trade_id))
        return result.scalar_one_or_none()

    async def create(self, journal: TradeJournal) -> TradeJournal:
        self._session.add(journal)
        await self._session.flush()
        await self._session.refresh(journal)
        return journal

    async def update(self, journal: TradeJournal) -> TradeJournal:
        await self._session.flush()
        await self._session.refresh(journal)
        return journal

    async def delete(self, journal: TradeJournal) -> None:
        await self._session.delete(journal)
