"""Auto-trading API schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class AutoTradingStatusSchema(BaseSchema):
    enabled: bool
    interval_seconds: int
    min_confidence: float
    bot_status: str
    active_strategies: int
    last_scan_at: datetime | None = None
    last_message: str | None = None
    last_error: str | None = None
    orders_placed_last_scan: int = 0
    disclaimer: str = (
        "Auto-trading executes your active strategies only. "
        "It does not predict markets or guarantee profits."
    )


class AutoTradingSettingsUpdate(BaseSchema):
    interval_seconds: int | None = Field(default=None, ge=60, le=3600)
    min_confidence: float | None = Field(default=None, ge=0.1, le=1.0)


class AutoTradingScanResultSchema(BaseSchema):
    strategy_id: int
    strategy_name: str
    symbol: str
    action: str
    confidence: float
    executed: bool
    message: str


class AutoTradingRunResponse(BaseSchema):
    scanned: int
    orders_placed: int
    results: list[AutoTradingScanResultSchema]
