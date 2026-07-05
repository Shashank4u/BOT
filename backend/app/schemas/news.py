"""News and economic calendar schemas."""

from typing import Any

from pydantic import BaseModel, Field


class EconomicEventSchema(BaseModel):
    id: int | None = None
    event_id: str
    title: str
    country: str
    currency: str
    impact: str
    event_time: str
    forecast: str | None = None
    previous: str | None = None
    actual: str | None = None


class NewsSyncResponse(BaseModel):
    fetched: int
    created: int


class TradingPauseStatusSchema(BaseModel):
    symbol: str
    paused: bool
    reason: str | None
    pause_trading_during_news: bool
    impact_filter: list[str] | None = None
    upcoming_events: list[EconomicEventSchema] = []


class NewsSettingsUpdate(BaseModel):
    pause_trading_during_news: bool | None = None
    news_impact_filter: list[str] | None = Field(
        default=None, description="Impact levels to pause on: high, medium, low"
    )
