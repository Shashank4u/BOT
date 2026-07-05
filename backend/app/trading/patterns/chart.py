"""Chart pattern detection using swing highs/lows."""

import numpy as np
import pandas as pd

from app.trading.patterns.types import PatternCategory, PatternDirection, PatternMatch


class ChartPatternDetector:
    """Heuristic chart pattern scanner on OHLC data."""

    def scan(self, df: pd.DataFrame, lookback: int = 80) -> list[PatternMatch]:
        if len(df) < lookback:
            lookback = len(df)
        if lookback < 30:
            return []

        window = df.iloc[-lookback:].reset_index(drop=True)
        matches: list[PatternMatch] = []

        peaks = self._find_peaks(window["high"].values)
        troughs = self._find_troughs(window["low"].values)

        matches.extend(self._detect_double_top(window, peaks))
        matches.extend(self._detect_double_bottom(window, troughs))
        matches.extend(self._detect_head_shoulders(window, peaks))
        matches.extend(self._detect_inverse_hs(window, troughs))
        matches.extend(self._detect_triangles(window))
        matches.extend(self._detect_rectangle(window))
        matches.extend(self._detect_channel(window))
        matches.extend(self._detect_flag_pennant(window))
        matches.extend(self._detect_cup_handle(window))
        matches.extend(self._detect_wedge(window))

        offset = len(df) - lookback
        return [
            PatternMatch(
                name=m.name,
                category=m.category,
                direction=m.direction,
                confidence=m.confidence,
                bar_index=m.bar_index + offset,
                time=df.iloc[m.bar_index + offset]["time"],
                description=m.description,
                price_level=m.price_level,
            )
            for m in matches
        ]

    def _find_peaks(self, highs: np.ndarray, order: int = 3) -> list[int]:
        peaks = []
        for i in range(order, len(highs) - order):
            if all(highs[i] >= highs[i - j] for j in range(1, order + 1)) and all(
                highs[i] >= highs[i + j] for j in range(1, order + 1)
            ):
                peaks.append(i)
        return peaks

    def _find_troughs(self, lows: np.ndarray, order: int = 3) -> list[int]:
        troughs = []
        for i in range(order, len(lows) - order):
            if all(lows[i] <= lows[i - j] for j in range(1, order + 1)) and all(
                lows[i] <= lows[i + j] for j in range(1, order + 1)
            ):
                troughs.append(i)
        return troughs

    def _level_similar(self, a: float, b: float, tolerance: float = 0.015) -> bool:
        mid = (a + b) / 2
        if mid == 0:
            return False
        return abs(a - b) / mid <= tolerance

    def _chart_match(
        self,
        name: str,
        direction: PatternDirection,
        confidence: float,
        index: int,
        df: pd.DataFrame,
        description: str,
        price: float | None = None,
    ) -> PatternMatch:
        row = df.iloc[index]
        return PatternMatch(
            name=name,
            category=PatternCategory.CHART,
            direction=direction,
            confidence=min(confidence, 0.95),
            bar_index=index,
            time=row["time"],
            description=description,
            price_level=price,
        )

    def _detect_double_top(
        self, df: pd.DataFrame, peaks: list[int]
    ) -> list[PatternMatch]:
        matches = []
        for i in range(len(peaks) - 1):
            p1, p2 = peaks[i], peaks[i + 1]
            if p2 - p1 < 5:
                continue
            h1, h2 = df.at[p1, "high"], df.at[p2, "high"]
            if self._level_similar(h1, h2):
                valley = float(df.iloc[p1:p2]["low"].min())
                if valley < h1 * 0.98:
                    conf = 0.7 + (1 - abs(h1 - h2) / h1) * 0.2
                    matches.append(self._chart_match(
                        "double_top", PatternDirection.BEARISH, conf, p2, df,
                        f"Double top near {h2:.5f} — potential bearish reversal",
                        h2,
                    ))
        return matches

    def _detect_double_bottom(
        self, df: pd.DataFrame, troughs: list[int]
    ) -> list[PatternMatch]:
        matches = []
        for i in range(len(troughs) - 1):
            t1, t2 = troughs[i], troughs[i + 1]
            if t2 - t1 < 5:
                continue
            l1, l2 = df.at[t1, "low"], df.at[t2, "low"]
            if self._level_similar(l1, l2):
                peak = float(df.iloc[t1:t2]["high"].max())
                if peak > l1 * 1.02:
                    conf = 0.7 + (1 - abs(l1 - l2) / l1) * 0.2
                    matches.append(self._chart_match(
                        "double_bottom", PatternDirection.BULLISH, conf, t2, df,
                        f"Double bottom near {l2:.5f} — potential bullish reversal",
                        l2,
                    ))
        return matches

    def _detect_head_shoulders(
        self, df: pd.DataFrame, peaks: list[int]
    ) -> list[PatternMatch]:
        matches = []
        for i in range(len(peaks) - 2):
            ls, head, rs = peaks[i], peaks[i + 1], peaks[i + 2]
            h_ls = df.at[ls, "high"]
            h_head = df.at[head, "high"]
            h_rs = df.at[rs, "high"]
            if h_head > h_ls and h_head > h_rs and self._level_similar(h_ls, h_rs, 0.03):
                matches.append(self._chart_match(
                    "head_shoulders", PatternDirection.BEARISH, 0.78, rs, df,
                    "Head and shoulders — middle peak highest, bearish reversal risk",
                    h_head,
                ))
        return matches

    def _detect_inverse_hs(
        self, df: pd.DataFrame, troughs: list[int]
    ) -> list[PatternMatch]:
        matches = []
        for i in range(len(troughs) - 2):
            ls, head, rs = troughs[i], troughs[i + 1], troughs[i + 2]
            l_ls = df.at[ls, "low"]
            l_head = df.at[head, "low"]
            l_rs = df.at[rs, "low"]
            if l_head < l_ls and l_head < l_rs and self._level_similar(l_ls, l_rs, 0.03):
                matches.append(self._chart_match(
                    "inverse_head_shoulders", PatternDirection.BULLISH, 0.78, rs, df,
                    "Inverse head and shoulders — middle trough lowest, bullish reversal risk",
                    l_head,
                ))
        return matches

    def _detect_triangles(self, df: pd.DataFrame) -> list[PatternMatch]:
        matches = []
        n = len(df)
        if n < 20:
            return matches

        third = n // 3
        early_highs = df.iloc[:third]["high"]
        late_highs = df.iloc[2 * third:]["high"]
        early_lows = df.iloc[:third]["low"]
        late_lows = df.iloc[2 * third:]["low"]

        high_falling = late_highs.mean() < early_highs.mean() * 0.998
        low_rising = late_lows.mean() > early_lows.mean() * 1.002
        high_flat = abs(late_highs.mean() - early_highs.mean()) / early_highs.mean() < 0.005
        low_flat = abs(late_lows.mean() - early_lows.mean()) / early_lows.mean() < 0.005
        low_falling = late_lows.mean() < early_lows.mean() * 0.998

        idx = n - 1
        price = float(df.iloc[-1]["close"])

        if high_falling and low_rising:
            matches.append(self._chart_match(
                "triangle", PatternDirection.NEUTRAL, 0.72, idx, df,
                "Symmetrical triangle — converging highs and lows",
                price,
            ))
        if high_flat and low_rising:
            matches.append(self._chart_match(
                "ascending_triangle", PatternDirection.BULLISH, 0.74, idx, df,
                "Ascending triangle — flat resistance, rising support",
                price,
            ))
        if low_flat and high_falling:
            matches.append(self._chart_match(
                "descending_triangle", PatternDirection.BEARISH, 0.74, idx, df,
                "Descending triangle — flat support, falling resistance",
                price,
            ))
        return matches

    def _detect_rectangle(self, df: pd.DataFrame) -> list[PatternMatch]:
        n = len(df)
        if n < 20:
            return []
        highs = df["high"]
        lows = df["low"]
        high_std = highs.std() / highs.mean()
        low_std = lows.std() / lows.mean()
        if high_std < 0.008 and low_std < 0.008:
            return [self._chart_match(
                "rectangle", PatternDirection.NEUTRAL, 0.7, n - 1, df,
                "Rectangle — price oscillating between horizontal levels",
                float(df.iloc[-1]["close"]),
            )]
        return []

    def _detect_channel(self, df: pd.DataFrame) -> list[PatternMatch]:
        n = len(df)
        if n < 25:
            return []
        x = np.arange(n, dtype=float)
        high_slope = np.polyfit(x, df["high"].values, 1)[0]
        low_slope = np.polyfit(x, df["low"].values, 1)[0]
        avg_price = df["close"].mean()
        if avg_price == 0:
            return []
        slope_ratio = abs(high_slope - low_slope) / avg_price
        if slope_ratio < 0.0001 and abs(high_slope) > 0:
            direction = (
                PatternDirection.BULLISH if high_slope > 0 else PatternDirection.BEARISH
            )
            return [self._chart_match(
                "channel", direction, 0.68, n - 1, df,
                "Price channel — parallel support and resistance",
                float(df.iloc[-1]["close"]),
            )]
        return []

    def _detect_flag_pennant(self, df: pd.DataFrame) -> list[PatternMatch]:
        n = len(df)
        if n < 25:
            return []
        matches = []
        pole = df.iloc[: n // 3]
        flag = df.iloc[n // 3:]

        pole_move = abs(pole.iloc[-1]["close"] - pole.iloc[0]["open"]) / pole.iloc[0]["open"]
        if pole_move < 0.01:
            return []

        flag_range = (flag["high"].max() - flag["low"].min()) / flag["close"].mean()
        if flag_range > pole_move * 0.6:
            return []

        x = np.arange(len(flag), dtype=float)
        high_slope = np.polyfit(x, flag["high"].values, 1)[0]
        low_slope = np.polyfit(x, flag["low"].values, 1)[0]

        idx = n - 1
        price = float(df.iloc[-1]["close"])

        if abs(high_slope - low_slope) < abs(high_slope) * 0.3:
            matches.append(self._chart_match(
                "flag", PatternDirection.NEUTRAL, 0.7, idx, df,
                "Flag — sharp move followed by parallel consolidation",
                price,
            ))
        elif high_slope < 0 and low_slope > 0:
            matches.append(self._chart_match(
                "pennant", PatternDirection.NEUTRAL, 0.68, idx, df,
                "Pennant — sharp move followed by converging consolidation",
                price,
            ))
        return matches

    def _detect_cup_handle(self, df: pd.DataFrame) -> list[PatternMatch]:
        n = len(df)
        if n < 40:
            return []
        cup_len = int(n * 0.7)
        cup = df.iloc[:cup_len]
        handle = df.iloc[cup_len:]

        if len(handle) < 5:
            return []

        left_rim = cup.iloc[0]["open"]
        right_rim = cup.iloc[-1]["close"]
        cup_low = cup["low"].min()

        if not self._level_similar(left_rim, right_rim, 0.03):
            return []
        if cup_low > min(left_rim, right_rim) * 0.95:
            return []
        if handle["high"].max() > right_rim * 1.01:
            return []

        return [self._chart_match(
            "cup_handle", PatternDirection.BULLISH, 0.72, n - 1, df,
            "Cup and handle — rounded bottom with consolidation pullback",
            float(df.iloc[-1]["close"]),
        )]

    def _detect_wedge(self, df: pd.DataFrame) -> list[PatternMatch]:
        n = len(df)
        if n < 25:
            return []
        x = np.arange(n, dtype=float)
        high_slope = np.polyfit(x, df["high"].values, 1)[0]
        low_slope = np.polyfit(x, df["low"].values, 1)[0]

        if high_slope * low_slope <= 0:
            return []
        if abs(high_slope - low_slope) > abs(high_slope) * 0.5:
            return []

        direction = (
            PatternDirection.BEARISH
            if high_slope > 0
            else PatternDirection.BULLISH
        )
        return [self._chart_match(
            "wedge", direction, 0.67, n - 1, df,
            "Wedge — converging trendlines in same direction",
            float(df.iloc[-1]["close"]),
        )]
