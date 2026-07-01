"""Market scanner endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.schemas.scanner import ScannerListItem, ScannerRunRequest, ScannerRunResponse
from app.services.scanner_service import ScannerService

router = APIRouter(prefix="/scanner", tags=["Scanner"])


def get_scanner_service(db: DbSession) -> ScannerService:
    return ScannerService(db)


ScannerSvc = Annotated[ScannerService, Depends(get_scanner_service)]


@router.post("/run", response_model=ScannerRunResponse)
async def run_scan(body: ScannerRunRequest, svc: ScannerSvc) -> ScannerRunResponse:
    """Scan multiple symbols for signals, patterns, and scores."""
    result = await svc.run_scan(
        symbols=body.symbols,
        timeframe=body.timeframe,
        strategy_type=body.strategy_type,
        scan_type=body.scan_type,
        save=body.save,
    )
    if result.get("id"):
        await svc._session.commit()
    return ScannerRunResponse(**result)


@router.get("/runs", response_model=list[ScannerListItem])
async def list_scans(svc: ScannerSvc, limit: int = 20) -> list[ScannerListItem]:
    """List past scanner runs."""
    scans = await svc.list_scans(limit)
    return [ScannerListItem(**s) for s in scans]


@router.get("/runs/{scan_id}", response_model=ScannerRunResponse)
async def get_scan(scan_id: int, svc: ScannerSvc) -> ScannerRunResponse:
    """Get a saved scanner run with full results."""
    try:
        detail = await svc.get_scan(scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ScannerRunResponse(
        id=detail["id"],
        scan_type=detail["scan_type"],
        timeframe=detail.get("timeframe", "H1"),
        strategy_type=detail.get("strategy_type", "ema_cross"),
        symbols=detail["symbols"],
        results=detail["results"],
        summary=detail["summary"],
    )
