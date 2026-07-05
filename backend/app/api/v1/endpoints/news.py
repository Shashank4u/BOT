"""Economic calendar and news endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.news import (
    EconomicEventSchema,
    NewsSettingsUpdate,
    NewsSyncResponse,
    TradingPauseStatusSchema,
)
from app.services.news_service import NewsService
from app.services.risk_service import RiskService

router = APIRouter(prefix="/news", tags=["News"])


def get_news_service(db: DbSession) -> NewsService:
    return NewsService(db)


def get_risk_service(db: DbSession) -> RiskService:
    return RiskService(db)


NewsSvc = Annotated[NewsService, Depends(get_news_service)]
RiskSvc = Annotated[RiskService, Depends(get_risk_service)]


@router.post("/sync", response_model=NewsSyncResponse)
async def sync_calendar(svc: NewsSvc, days_ahead: int = 7) -> NewsSyncResponse:
    """Sync economic calendar events (mock data in dev)."""
    result = await svc.sync_calendar(days_ahead)
    await svc._session.commit()
    return NewsSyncResponse(**result)


@router.get("/calendar", response_model=list[EconomicEventSchema])
async def get_calendar(
    svc: NewsSvc,
    hours_ahead: int = Query(default=168, le=336),
    impact: str | None = Query(default=None, description="Comma-separated: high,medium,low"),
    currency: str | None = None,
) -> list[EconomicEventSchema]:
    """Get economic calendar events."""
    impact_list = [i.strip() for i in impact.split(",")] if impact else None
    events = await svc.list_events(hours_ahead=hours_ahead, impact=impact_list, currency=currency)
    return [EconomicEventSchema(**e) for e in events]


@router.get("/high-impact", response_model=list[EconomicEventSchema])
async def get_high_impact_events(
    svc: NewsSvc, hours_ahead: int = 48
) -> list[EconomicEventSchema]:
    """Get upcoming high-impact economic events."""
    events = await svc.high_impact_events(hours_ahead)
    return [EconomicEventSchema(**e) for e in events]


@router.get("/pause-status/{symbol}", response_model=TradingPauseStatusSchema)
async def trading_pause_status(symbol: str, svc: NewsSvc) -> TradingPauseStatusSchema:
    """Check if trading is paused for a symbol due to nearby news."""
    status = await svc.trading_pause_status(symbol)
    return TradingPauseStatusSchema(**status)


@router.patch("/settings")
async def update_news_settings(body: NewsSettingsUpdate, risk: RiskSvc) -> dict:
    """Update news-related trading settings."""
    data = body.model_dump(exclude_unset=True)
    settings = await risk.update_settings(data)
    await risk._session.commit()
    return {
        "pause_trading_during_news": settings.pause_trading_during_news,
        "news_impact_filter": settings.news_impact_filter,
    }
