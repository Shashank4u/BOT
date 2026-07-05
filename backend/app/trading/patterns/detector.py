"""Main pattern detector — orchestrates candlestick and chart scanners."""

from typing import Any

import pandas as pd

from app.trading.indicators.dataframe import bars_to_dataframe
from app.trading.patterns.candlestick import CandlestickDetector
from app.trading.patterns.chart import ChartPatternDetector
from app.trading.patterns.registry import (
    CANDLESTICK_PATTERNS,
    CHART_PATTERNS,
)
from app.trading.patterns.types import PatternMatch
from app.trading.types import OHLCBar

MIN_BARS = 30


class PatternDetector:
    """Detect candlestick and chart patterns on OHLC data."""

    def __init__(self) -> None:
        self._candlestick = CandlestickDetector()
        self._chart = ChartPatternDetector()

    def list_available(self) -> list[dict[str, Any]]:
        items = []
        for name, meta in CANDLESTICK_PATTERNS.items():
            items.append({"name": name, "category": "candlestick", **meta})
        for name, meta in CHART_PATTERNS.items():
            items.append({"name": name, "category": "chart", **meta})
        return items

    def scan(
        self,
        bars: list[OHLCBar],
        patterns: list[str] | None = None,
        categories: list[str] | None = None,
        lookback: int = 100,
        recent_bars: int | None = None,
    ) -> list[PatternMatch]:
        """
        Scan OHLC bars for patterns.
        Optionally filter by pattern names, categories, or recent bar window.
        """
        if len(bars) < MIN_BARS:
            raise ValueError(
                f"Need at least {MIN_BARS} bars for pattern detection, got {len(bars)}"
            )

        df = bars_to_dataframe(bars)
        all_matches: list[PatternMatch] = []

        run_candle = not categories or "candlestick" in categories
        run_chart = not categories or "chart" in categories

        if run_candle:
            all_matches.extend(self._candlestick.scan(df))

        if run_chart:
            all_matches.extend(self._chart.scan(df, lookback=min(lookback, len(df))))

        if patterns:
            pattern_set = set(patterns)
            all_matches = [m for m in all_matches if m.name in pattern_set]

        if recent_bars is not None:
            cutoff = len(df) - recent_bars
            all_matches = [m for m in all_matches if m.bar_index >= cutoff]

        # Deduplicate same pattern at same bar (keep highest confidence)
        seen: dict[tuple[str, int], PatternMatch] = {}
        for m in all_matches:
            key = (m.name, m.bar_index)
            if key not in seen or m.confidence > seen[key].confidence:
                seen[key] = m

        results = sorted(seen.values(), key=lambda m: (m.bar_index, -m.confidence))
        return results

    def scan_recent(
        self,
        bars: list[OHLCBar],
        recent_bars: int = 10,
        **kwargs: Any,
    ) -> list[PatternMatch]:
        """Return only patterns detected in the most recent N bars."""
        return self.scan(bars, recent_bars=recent_bars, **kwargs)

    def summarize(self, matches: list[PatternMatch]) -> dict[str, Any]:
        """Build summary counts by pattern and direction."""
        by_name: dict[str, int] = {}
        by_direction: dict[str, int] = {"bullish": 0, "bearish": 0, "neutral": 0}
        for m in matches:
            by_name[m.name] = by_name.get(m.name, 0) + 1
            by_direction[m.direction.value] += 1
        return {
            "total": len(matches),
            "by_pattern": by_name,
            "by_direction": by_direction,
        }
