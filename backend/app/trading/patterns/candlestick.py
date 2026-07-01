"""Candlestick pattern detection rules."""

import pandas as pd

from app.trading.patterns.types import PatternCategory, PatternDirection, PatternMatch
from app.trading.patterns.utils import (
    avg_range,
    body_bottom,
    body_size,
    body_top,
    candle_range,
    is_bearish,
    is_bullish,
    lower_shadow,
    upper_shadow,
)


class CandlestickDetector:
    """Rule-based candlestick pattern scanner."""

    def scan(self, df: pd.DataFrame) -> list[PatternMatch]:
        if len(df) < 5:
            return []

        matches: list[PatternMatch] = []
        avg_rng = avg_range(df)

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]
            rng = candle_range(row)
            if rng <= 0:
                continue

            body = body_size(row)
            body_ratio = body / rng

            # Doji
            if body_ratio < 0.1:
                matches.append(self._match(
                    "doji", PatternDirection.NEUTRAL, 0.75 + (0.1 - body_ratio),
                    i, row, "Doji — open and close nearly equal, market indecision",
                ))

            # Hammer
            if (
                body_ratio < 0.35
                and lower_shadow(row) >= body * 2
                and upper_shadow(row) <= body * 0.5
                and body_top(row) > row["low"] + rng * 0.6
            ):
                conf = min(0.95, 0.7 + lower_shadow(row) / rng * 0.25)
                matches.append(self._match(
                    "hammer", PatternDirection.BULLISH, conf,
                    i, row, "Hammer — long lower wick, potential bullish reversal",
                    row["close"],
                ))

            # Shooting star
            if (
                body_ratio < 0.35
                and upper_shadow(row) >= body * 2
                and lower_shadow(row) <= body * 0.5
                and body_bottom(row) < row["low"] + rng * 0.4
            ):
                conf = min(0.95, 0.7 + upper_shadow(row) / rng * 0.25)
                matches.append(self._match(
                    "shooting_star", PatternDirection.BEARISH, conf,
                    i, row, "Shooting star — long upper wick, potential bearish reversal",
                    row["close"],
                ))

            # Pin bar (general rejection)
            wick_ratio = max(upper_shadow(row), lower_shadow(row)) / rng
            if body_ratio < 0.3 and wick_ratio > 0.6:
                direction = (
                    PatternDirection.BULLISH
                    if lower_shadow(row) > upper_shadow(row)
                    else PatternDirection.BEARISH
                )
                matches.append(self._match(
                    "pin_bar", direction, min(0.9, 0.65 + wick_ratio * 0.3),
                    i, row, "Pin bar — strong rejection wick",
                    row["close"],
                ))

            # Inside bar
            if row["high"] < prev["high"] and row["low"] > prev["low"]:
                matches.append(self._match(
                    "inside_bar", PatternDirection.NEUTRAL, 0.8,
                    i, row, "Inside bar — consolidation within prior range",
                    row["close"],
                ))

            # Bullish engulfing
            if (
                is_bearish(prev)
                and is_bullish(row)
                and row["open"] <= prev["close"]
                and row["close"] >= prev["open"]
                and body_size(row) > body_size(prev)
            ):
                matches.append(self._match(
                    "bullish_engulfing", PatternDirection.BULLISH, 0.85,
                    i, row, "Bullish engulfing — buyers absorbed selling pressure",
                    row["close"],
                ))

            # Bearish engulfing
            if (
                is_bullish(prev)
                and is_bearish(row)
                and row["open"] >= prev["close"]
                and row["close"] <= prev["open"]
                and body_size(row) > body_size(prev)
            ):
                matches.append(self._match(
                    "bearish_engulfing", PatternDirection.BEARISH, 0.85,
                    i, row, "Bearish engulfing — sellers overwhelmed buyers",
                    row["close"],
                ))

            # Harami
            if (
                body_size(prev) > avg_rng * 0.4
                and body_size(row) < body_size(prev) * 0.5
                and body_top(row) < body_top(prev)
                and body_bottom(row) > body_bottom(prev)
            ):
                direction = (
                    PatternDirection.BULLISH
                    if is_bearish(prev) and is_bullish(row)
                    else PatternDirection.BEARISH
                    if is_bullish(prev) and is_bearish(row)
                    else PatternDirection.NEUTRAL
                )
                matches.append(self._match(
                    "harami", direction, 0.75,
                    i, row, "Harami — momentum pause inside prior candle body",
                    row["close"],
                ))

        # Multi-candle patterns
        for i in range(2, len(df)):
            self._scan_stars(df, i, matches)

        return matches

    def _scan_stars(
        self, df: pd.DataFrame, i: int, matches: list[PatternMatch]
    ) -> None:
        c1, c2, c3 = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]
        star_body = body_size(c2)
        star_range = candle_range(c2)

        # Morning star
        if (
            is_bearish(c1)
            and star_range > 0
            and star_body / star_range < 0.35
            and is_bullish(c3)
            and c3["close"] > (c1["open"] + c1["close"]) / 2
        ):
            matches.append(self._match(
                "morning_star", PatternDirection.BULLISH, 0.82,
                i, c3, "Morning star — three-candle bullish reversal",
                c3["close"],
            ))

        # Evening star
        if (
            is_bullish(c1)
            and star_range > 0
            and star_body / star_range < 0.35
            and is_bearish(c3)
            and c3["close"] < (c1["open"] + c1["close"]) / 2
        ):
            matches.append(self._match(
                "evening_star", PatternDirection.BEARISH, 0.82,
                i, c3, "Evening star — three-candle bearish reversal",
                c3["close"],
            ))

    def _match(
        self,
        name: str,
        direction: PatternDirection,
        confidence: float,
        index: int,
        row: pd.Series,
        description: str,
        price: float | None = None,
    ) -> PatternMatch:
        return PatternMatch(
            name=name,
            category=PatternCategory.CANDLESTICK,
            direction=direction,
            confidence=min(confidence, 0.99),
            bar_index=index,
            time=row["time"],
            description=description,
            price_level=price,
        )
