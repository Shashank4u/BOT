"""Pattern detection API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.patterns import (
    PatternMetaSchema,
    PatternMatchSchema,
    PatternScanResponse,
    PatternSummarySchema,
    RecentPatternsResponse,
)
from app.services.pattern_service import PatternService, get_pattern_service
from app.trading.patterns.registry import parse_categories, parse_pattern_names
from app.trading.types import Timeframe

router = APIRouter(prefix="/patterns", tags=["Patterns"])

PatternSvc = Annotated[PatternService, Depends(get_pattern_service)]


@router.get("", response_model=list[PatternMetaSchema])
async def list_patterns(svc: PatternSvc) -> list[PatternMetaSchema]:
    """List all supported candlestick and chart patterns."""
    return [PatternMetaSchema(**item) for item in svc.list_patterns()]


@router.get("/{symbol}", response_model=PatternScanResponse)
async def scan_patterns(
    symbol: str,
    svc: PatternSvc,
    timeframe: Timeframe = Timeframe.H1,
    count: int = Query(default=200, ge=30, le=5000),
    names: str | None = Query(
        default=None,
        description="Comma-separated pattern names to filter, e.g. hammer,doji,double_top",
    ),
    categories: str | None = Query(
        default=None,
        description="Filter by category: candlestick, chart, or both",
    ),
    lookback: int = Query(default=100, ge=30, le=500),
) -> PatternScanResponse:
    """
    Scan OHLC data for candlestick and chart patterns.
    Returns all matches with confidence scores and descriptions.
    """
    pattern_list = None
    category_list = None

    if names:
        try:
            pattern_list = parse_pattern_names(names)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if categories:
        try:
            category_list = parse_categories(categories)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = svc.scan_symbol(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            patterns=pattern_list,
            categories=category_list,
            lookback=lookback,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PatternScanResponse(
        symbol=result["symbol"],
        timeframe=result["timeframe"],
        bars_scanned=result["bars_scanned"],
        patterns=[PatternMatchSchema(**p) for p in result["patterns"]],
        summary=PatternSummarySchema(**result["summary"]),
    )


@router.get("/{symbol}/recent", response_model=RecentPatternsResponse)
async def scan_recent_patterns(
    symbol: str,
    svc: PatternSvc,
    timeframe: Timeframe = Timeframe.H1,
    count: int = Query(default=200, ge=30, le=5000),
    recent_bars: int = Query(default=10, ge=1, le=50),
    categories: str | None = None,
) -> RecentPatternsResponse:
    """Patterns detected only in the most recent N bars — for live monitoring."""
    category_list = None
    if categories:
        try:
            category_list = parse_categories(categories)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = svc.scan_recent(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            recent_bars=recent_bars,
            categories=category_list,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RecentPatternsResponse(
        symbol=result["symbol"],
        timeframe=result["timeframe"],
        recent_bars=result["recent_bars"],
        patterns=[PatternMatchSchema(**p) for p in result["patterns"]],
    )
