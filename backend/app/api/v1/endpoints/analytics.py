"""Trading analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.analytics import (
    AnalyticsOverviewSchema,
    DailyPnlSchema,
    EquityCurveSchema,
    HeatmapSchema,
    PnlBySymbolSchema,
    WinRateSchema,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(db: DbSession) -> AnalyticsService:
    return AnalyticsService(db)


AnalyticsSvc = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get("/overview", response_model=AnalyticsOverviewSchema)
async def analytics_overview(svc: AnalyticsSvc, days: int = 30) -> AnalyticsOverviewSchema:
    """Performance summary for the selected period."""
    return AnalyticsOverviewSchema(**await svc.overview(days))


@router.get("/equity-curve", response_model=EquityCurveSchema)
async def equity_curve(svc: AnalyticsSvc, days: int = 30) -> EquityCurveSchema:
    """Equity curve data for charting."""
    return EquityCurveSchema(**await svc.equity_curve(days))


@router.get("/pnl-by-symbol", response_model=PnlBySymbolSchema)
async def pnl_by_symbol(svc: AnalyticsSvc, days: int = 30) -> PnlBySymbolSchema:
    """Profit/loss breakdown by symbol."""
    return PnlBySymbolSchema(**await svc.pnl_by_symbol(days))


@router.get("/daily-pnl", response_model=DailyPnlSchema)
async def daily_pnl(svc: AnalyticsSvc, days: int = 30) -> DailyPnlSchema:
    """Daily P/L series for bar charts."""
    return DailyPnlSchema(**await svc.daily_pnl(days))


@router.get("/win-rate", response_model=WinRateSchema)
async def win_rate(svc: AnalyticsSvc, days: int = 30) -> WinRateSchema:
    """Win rate statistics."""
    return WinRateSchema(**await svc.win_rate(days))


@router.get("/heatmap", response_model=HeatmapSchema)
async def performance_heatmap(svc: AnalyticsSvc, days: int = 30) -> HeatmapSchema:
    """Session heatmap (day x hour) and symbol performance."""
    return HeatmapSchema(**await svc.heatmap(days))
