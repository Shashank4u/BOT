"""AI assistant request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SignalExplainRequest(BaseModel):
    strategy_name: str
    strategy_type: str
    symbol: str
    timeframe: str = "H1"
    action: str
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = []
    indicators: dict[str, Any] = {}
    patterns: list[str] = []
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AnalysisResponseSchema(BaseModel):
    id: int
    trade_id: int | None = None
    analysis_type: str
    content: str
    model: str
    tokens_used: int | None = None
    is_mock: bool = False
    created_at: str


class ReportResponseSchema(BaseModel):
    id: int
    report_type: str
    content: str
    summary: str | None
    metrics: dict[str, Any] | None
    model: str
    is_mock: bool = False
    period_start: str
    period_end: str


class ChatResponseSchema(BaseModel):
    reply: str
    model: str
    is_mock: bool = False


class ReportListItemSchema(BaseModel):
    id: int
    report_type: str
    summary: str | None
    metrics: dict[str, Any] | None
    created_at: str
