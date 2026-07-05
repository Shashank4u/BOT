"""Auto-trading control endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.auto_trading import (
    AutoTradingRunResponse,
    AutoTradingScanResultSchema,
    AutoTradingSettingsUpdate,
    AutoTradingStatusSchema,
)
from app.services.auto_trader_service import AutoTraderService

router = APIRouter(prefix="/auto-trading", tags=["Auto Trading"])


def get_auto_trader_service(db: DbSession) -> AutoTraderService:
    return AutoTraderService(db)


AutoTraderSvc = Annotated[AutoTraderService, Depends(get_auto_trader_service)]


@router.get("/status", response_model=AutoTradingStatusSchema)
async def auto_trading_status(svc: AutoTraderSvc) -> AutoTradingStatusSchema:
    """Current auto-trading state, active strategies, and last scan info."""
    return AutoTradingStatusSchema(**await svc.get_status())


@router.post("/start", response_model=AutoTradingStatusSchema)
async def start_auto_trading(svc: AutoTraderSvc) -> AutoTradingStatusSchema:
    """Enable auto-trading. Active strategies will be scanned on the interval."""
    await svc.set_enabled(True)
    await svc._session.commit()
    return AutoTradingStatusSchema(**await svc.get_status())


@router.post("/stop", response_model=AutoTradingStatusSchema)
async def stop_auto_trading(svc: AutoTraderSvc) -> AutoTradingStatusSchema:
    """Disable auto-trading. Open positions are not closed automatically."""
    await svc.set_enabled(False)
    await svc._session.commit()
    return AutoTradingStatusSchema(**await svc.get_status())


@router.patch("/settings", response_model=AutoTradingStatusSchema)
async def update_auto_trading_settings(
    body: AutoTradingSettingsUpdate, svc: AutoTraderSvc
) -> AutoTradingStatusSchema:
    """Update scan interval (60–3600s) and minimum signal confidence."""
    await svc.update_settings(
        interval_seconds=body.interval_seconds,
        min_confidence=body.min_confidence,
    )
    await svc._session.commit()
    return AutoTradingStatusSchema(**await svc.get_status())


@router.post("/run-once", response_model=AutoTradingRunResponse)
async def run_auto_trading_once(svc: AutoTraderSvc) -> AutoTradingRunResponse:
    """Run a single scan immediately (for testing)."""
    results = await svc.run_scan()
    await svc._session.commit()
    placed = sum(1 for r in results if r.executed)
    return AutoTradingRunResponse(
        scanned=len(results),
        orders_placed=placed,
        results=[AutoTradingScanResultSchema(**r.to_dict()) for r in results],
    )
