"""Pattern detection types."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PatternCategory(str, Enum):
    CANDLESTICK = "candlestick"
    CHART = "chart"


class PatternDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class PatternMatch:
    """A detected pattern occurrence on a specific bar or zone."""

    name: str
    category: PatternCategory
    direction: PatternDirection
    confidence: float
    bar_index: int
    time: datetime
    description: str
    price_level: float | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "direction": self.direction.value,
            "confidence": round(self.confidence, 3),
            "bar_index": self.bar_index,
            "time": self.time.isoformat(),
            "description": self.description,
            "price_level": round(self.price_level, 6) if self.price_level else None,
        }
