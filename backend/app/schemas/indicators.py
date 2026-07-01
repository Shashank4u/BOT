"""Indicator API schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema
from app.trading.types import Timeframe


class IndicatorMetaSchema(BaseSchema):
    name: str
    label: str
    params: dict[str, Any]
    outputs: list[str]


class IndicatorResultSchema(BaseSchema):
    params: dict[str, Any] = Field(default_factory=dict)
    values: list[dict[str, Any]]
    latest: dict[str, Any]


class IndicatorsResponse(BaseSchema):
    symbol: str
    timeframe: Timeframe
    bars_used: int
    indicators: dict[str, IndicatorResultSchema]
    disclaimer: str = (
        "Indicators describe historical price behavior only. "
        "They do not predict future prices or guarantee profitable trades."
    )


class IndicatorSnapshotResponse(BaseSchema):
    """Latest indicator values only — optimized for dashboard/mobile."""

    symbol: str
    timeframe: Timeframe
    snapshot: dict[str, dict[str, Any]]
    disclaimer: str = (
        "Indicators describe historical price behavior only. "
        "They do not predict future prices or guarantee profitable trades."
    )
