"""Pattern detection API schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema
from app.trading.types import Timeframe


class PatternMetaSchema(BaseSchema):
    name: str
    category: str
    label: str
    direction: str
    description: str


class PatternMatchSchema(BaseSchema):
    name: str
    category: str
    direction: str
    confidence: float
    bar_index: int
    time: str
    description: str
    price_level: float | None = None


class PatternSummarySchema(BaseSchema):
    total: int
    by_pattern: dict[str, int]
    by_direction: dict[str, int]


class PatternScanResponse(BaseSchema):
    symbol: str
    timeframe: Timeframe
    bars_scanned: int
    patterns: list[PatternMatchSchema]
    summary: PatternSummarySchema
    disclaimer: str = (
        "Detected patterns describe historical price formations only. "
        "They are not trade signals and do not predict future price movement."
    )


class RecentPatternsResponse(BaseSchema):
    symbol: str
    timeframe: Timeframe
    recent_bars: int
    patterns: list[PatternMatchSchema]
    disclaimer: str = (
        "Detected patterns describe historical price formations only. "
        "They are not trade signals and do not predict future price movement."
    )
