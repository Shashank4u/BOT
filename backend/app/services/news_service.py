"""News and economic calendar service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.news_repository import NewsRepository
from app.services.risk_service import RiskService
from app.trading.news import get_calendar_provider
from app.trading.news.guard import is_trading_paused


class NewsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NewsRepository(session)
        self._risk = RiskService(session)
        self._provider = get_calendar_provider()

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def sync_calendar(self, days_ahead: int = 7) -> dict[str, int]:
        """Fetch mock calendar events and cache new ones in database."""
        events = self._provider.fetch_events(days_ahead=days_ahead)
        created = await self._repo.upsert_events(events)
        return {"fetched": len(events), "created": created}

    async def list_events(
        self,
        hours_ahead: int = 168,
        impact: list[str] | None = None,
        currency: str | None = None,
    ) -> list[dict[str, Any]]:
        await self.sync_calendar()
        events = await self._repo.list_events(
            hours_ahead=hours_ahead, impact=impact, currency=currency
        )
        return [self._event_dict(e) for e in events]

    async def high_impact_events(self, hours_ahead: int = 48) -> list[dict[str, Any]]:
        return await self.list_events(hours_ahead=hours_ahead, impact=["high"])

    async def trading_pause_status(self, symbol: str) -> dict[str, Any]:
        """Check if trading is paused for a symbol due to news."""
        settings = await self._risk.get_settings()
        if not settings.pause_trading_during_news:
            return {
                "symbol": symbol.upper(),
                "paused": False,
                "reason": None,
                "pause_trading_during_news": False,
            }

        impact_filter = settings.news_impact_filter or ["high"]
        if isinstance(impact_filter, str):
            impact_filter = [impact_filter]

        await self.sync_calendar()
        events = await self._repo.list_events(
            hours_ahead=24, hours_back=1, impact=impact_filter
        )
        paused, reason = is_trading_paused(symbol, events, impact_filter)

        return {
            "symbol": symbol.upper(),
            "paused": paused,
            "reason": reason,
            "pause_trading_during_news": True,
            "impact_filter": impact_filter,
            "upcoming_events": [
                self._event_dict(e)
                for e in events[:5]
            ],
        }

    async def check_symbol_allowed(self, symbol: str) -> tuple[bool, str | None]:
        """Return (allowed, violation_reason) for order placement."""
        status = await self.trading_pause_status(symbol)
        if status["paused"]:
            return False, status["reason"]
        return True, None

    def _event_dict(self, event) -> dict[str, Any]:
        return {
            "id": event.id,
            "event_id": event.event_id,
            "title": event.title,
            "country": event.country,
            "currency": event.currency,
            "impact": event.impact,
            "event_time": event.event_time.isoformat(),
            "forecast": event.forecast,
            "previous": event.previous,
            "actual": event.actual,
        }
