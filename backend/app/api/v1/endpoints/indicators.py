"""Technical indicator API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.indicators import (
    IndicatorMetaSchema,
    IndicatorResultSchema,
    IndicatorSnapshotResponse,
    IndicatorsResponse,
)
from app.services.indicator_service import IndicatorService, get_indicator_service
from app.trading.indicators.registry import parse_indicator_names
from app.trading.types import Timeframe

router = APIRouter(prefix="/indicators", tags=["Indicators"])

IndicatorSvc = Annotated[IndicatorService, Depends(get_indicator_service)]

DEFAULT_SET = "rsi,ema,macd,atr,bbands"


@router.get("", response_model=list[IndicatorMetaSchema])
async def list_indicators(svc: IndicatorSvc) -> list[IndicatorMetaSchema]:
    """List all supported indicators with default parameters."""
    return [IndicatorMetaSchema(**item) for item in svc.list_indicators()]


@router.get("/{symbol}", response_model=IndicatorsResponse)
async def compute_indicators(
    symbol: str,
    svc: IndicatorSvc,
    names: str = Query(
        default=DEFAULT_SET,
        description="Comma-separated indicators, e.g. rsi,ema,macd,atr",
    ),
    timeframe: Timeframe = Timeframe.H1,
    count: int = Query(default=200, ge=30, le=5000),
) -> IndicatorsResponse:
    """
    Compute technical indicators for a symbol.
    Fetches OHLC from MT5, calculates indicators, returns full series + latest values.
    """
    try:
        indicator_list = parse_indicator_names(names)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = svc.compute_for_symbol(
            symbol=symbol,
            indicators=indicator_list,
            timeframe=timeframe,
            count=count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IndicatorsResponse(
        symbol=result["symbol"],
        timeframe=result["timeframe"],
        bars_used=result["bars_used"],
        indicators={
            name: IndicatorResultSchema(**data)
            for name, data in result["indicators"].items()
        },
    )


@router.get("/{symbol}/snapshot", response_model=IndicatorSnapshotResponse)
async def indicator_snapshot(
    symbol: str,
    svc: IndicatorSvc,
    names: str = Query(default=DEFAULT_SET),
    timeframe: Timeframe = Timeframe.H1,
    count: int = Query(default=200, ge=30, le=5000),
) -> IndicatorSnapshotResponse:
    """Latest indicator values only — lightweight for mobile dashboard."""
    try:
        indicator_list = parse_indicator_names(names)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = svc.snapshot(symbol, indicator_list, timeframe, count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IndicatorSnapshotResponse(
        symbol=result["symbol"],
        timeframe=result["timeframe"],
        snapshot=result["snapshot"],
    )
