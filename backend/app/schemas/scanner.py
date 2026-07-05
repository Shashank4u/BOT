"""Market scanner schemas."""

from typing import Any

from pydantic import BaseModel, Field

from app.trading.types import Timeframe


class ScannerRunRequest(BaseModel):
    symbols: list[str] | None = None
    timeframe: Timeframe = Timeframe.H1
    strategy_type: str = "ema_cross"
    scan_type: str = "full"
    save: bool = True


class ScannerResultItem(BaseModel):
    symbol: str
    timeframe: str
    price: float | None = None
    signal: str = "hold"
    confidence: float = 0.0
    score: float = 0.0
    reasons: list[str] = []
    patterns: list[dict[str, Any]] = []
    indicators: dict[str, Any] = {}
    strategy_type: str | None = None
    error: str | None = None


class ScannerSummarySchema(BaseModel):
    total: int
    buy_signals: int
    sell_signals: int
    top_symbol: str | None
    top_score: float


class ScannerRunResponse(BaseModel):
    id: int | None
    scan_type: str
    timeframe: str
    strategy_type: str
    symbols: list[str]
    results: list[ScannerResultItem]
    summary: ScannerSummarySchema


class ScannerListItem(BaseModel):
    id: int
    scan_type: str
    symbol_count: int
    summary: dict[str, Any]
    created_at: str
