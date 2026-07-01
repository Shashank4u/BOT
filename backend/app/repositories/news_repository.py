"""Economic event data access."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import EconomicEvent


class NewsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_events(self, events: list[dict]) -> int:
        count = 0
        for event in events:
            existing = await self._session.execute(
                select(EconomicEvent).where(EconomicEvent.event_id == event["event_id"])
            )
            if existing.scalar_one_or_none():
                continue
            self._session.add(
                EconomicEvent(
                    event_id=event["event_id"],
                    title=event["title"],
                    country=event["country"],
                    currency=event["currency"],
                    impact=event["impact"],
                    event_time=event["event_time"],
                    forecast=event.get("forecast"),
                    previous=event.get("previous"),
                    actual=event.get("actual"),
                )
            )
            count += 1
        await self._session.flush()
        return count

    async def list_events(
        self,
        hours_ahead: int = 168,
        hours_back: int = 24,
        impact: list[str] | None = None,
        currency: str | None = None,
    ) -> list[EconomicEvent]:
        now = datetime.now(UTC)
        start = now - timedelta(hours=hours_back)
        end = now + timedelta(hours=hours_ahead)

        q = (
            select(EconomicEvent)
            .where(EconomicEvent.event_time >= start, EconomicEvent.event_time <= end)
            .order_by(EconomicEvent.event_time)
        )
        if impact:
            q = q.where(EconomicEvent.impact.in_([i.lower() for i in impact]))
        if currency:
            q = q.where(EconomicEvent.currency == currency.upper())

        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_upcoming(self, hours: int = 24) -> list[EconomicEvent]:
        return await self.list_events(hours_ahead=hours, hours_back=0)
