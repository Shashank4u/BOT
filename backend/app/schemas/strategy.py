"""Strategy schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema
from app.trading.types import Timeframe


class StrategyCreateSchema(BaseSchema):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    strategy_type: str
    symbols: list[str] = Field(default_factory=list)
    timeframes: list[str] = Field(default_factory=lambda: ["H1"])
    params: dict[str, Any] = Field(default_factory=dict)
    stop_loss_pips: float | None = None
    take_profit_pips: float | None = None
    max_risk_percent: float = Field(default=1.0, ge=0.1, le=10.0)
    max_trades: int = Field(default=3, ge=1, le=20)
    magic_number: int = Field(default=100001)


class StrategyUpdateSchema(BaseSchema):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    symbols: list[str] | None = None
    timeframes: list[str] | None = None
    params: dict[str, Any] | None = None
    stop_loss_pips: float | None = None
    take_profit_pips: float | None = None
    max_risk_percent: float | None = None
    max_trades: int | None = None


class StrategyResponseSchema(BaseSchema):
    id: int
    name: str
    description: str | None
    status: str
    is_sample: bool
    strategy_type: str
    symbols: list[str]
    timeframes: list[str]
    params: dict[str, Any]
    stop_loss_pips: float | None
    take_profit_pips: float | None
    max_risk_percent: float
    max_trades: int
    magic_number: int


class SampleStrategySchema(BaseSchema):
    name: str
    description: str
    strategy_type: str
    symbols: list[str]
    timeframes: list[str]
    indicators: list[str]
    stop_loss_pips: float | None
    take_profit_pips: float | None
    max_risk_percent: float
    max_trades: int


class StrategySignalSchema(BaseSchema):
    strategy_name: str
    strategy_type: str
    symbol: str
    timeframe: str
    action: str
    confidence: float
    reasons: list[str]
    price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    indicators: dict[str, Any] = Field(default_factory=dict)
    patterns: list[dict[str, Any]] = Field(default_factory=list)
    evaluated_at: str | None = None
    disclaimer: str


class EvaluateRequestSchema(BaseSchema):
    symbol: str
    timeframe: Timeframe | None = None


class SeedSamplesResponse(BaseSchema):
    created: int
    skipped: int
    message: str
