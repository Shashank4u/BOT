"""Backtesting API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.schemas.backtest import (
    BacktestDetailResponse,
    BacktestRunRequest,
    BacktestRunResponse,
)
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


def get_backtest_service(db: DbSession) -> BacktestService:
    return BacktestService(db)


BacktestSvc = Annotated[BacktestService, Depends(get_backtest_service)]


@router.post("/run", response_model=BacktestDetailResponse)
async def run_backtest(body: BacktestRunRequest, svc: BacktestSvc) -> BacktestDetailResponse:
    """
    Run a strategy backtest on historical/simulated OHLC data.
    Provide strategy_id for a saved strategy, or strategy_type for ad-hoc runs.
    """
    if not body.strategy_id and not body.strategy_type:
        raise HTTPException(
            status_code=400,
            detail="Provide strategy_id or strategy_type",
        )
    try:
        result = await svc.run_backtest(body.model_dump())
        if result.get("id") and result["id"] > 0:
            await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BacktestDetailResponse(**result)


@router.get("/runs", response_model=list[BacktestRunResponse])
async def list_backtest_runs(svc: BacktestSvc, limit: int = 50) -> list[BacktestRunResponse]:
    """List past backtest runs."""
    runs = await svc.list_runs(limit)
    return [BacktestRunResponse(**r) for r in runs]


@router.get("/runs/{run_id}", response_model=BacktestDetailResponse)
async def get_backtest_run(run_id: int, svc: BacktestSvc) -> BacktestDetailResponse:
    """Get full backtest run details including trades and equity curve."""
    try:
        result = await svc.get_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BacktestDetailResponse(**result)


@router.get("/runs/{run_id}/export")
async def export_backtest_run(run_id: int, svc: BacktestSvc) -> dict[str, Any]:
    """Export backtest results as JSON."""
    try:
        return await svc.export_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
