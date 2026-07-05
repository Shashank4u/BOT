"""Trade journal request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JournalUpsertRequest(BaseModel):
    notes: str | None = None
    emotion: str | None = Field(None, max_length=50)
    screenshot_path: str | None = Field(None, max_length=500)
    lessons_learned: str | None = None
    tags: list[str] | dict[str, Any] | None = None


class TradeSummarySchema(BaseModel):
    symbol: str
    direction: str
    status: str
    profit_loss: float | None


class JournalResponseSchema(BaseModel):
    id: int
    trade_id: int
    notes: str | None
    emotion: str | None
    screenshot_path: str | None
    lessons_learned: str | None
    ai_review: str | None
    tags: list[str] | dict[str, Any] | None
    created_at: str
    updated_at: str
    trade: TradeSummarySchema | None = None
