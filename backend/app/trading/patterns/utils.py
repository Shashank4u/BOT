"""Shared OHLC geometry helpers for pattern detection."""

import pandas as pd


def body_size(row: pd.Series) -> float:
    return abs(row["close"] - row["open"])


def candle_range(row: pd.Series) -> float:
    return row["high"] - row["low"]


def upper_shadow(row: pd.Series) -> float:
    return row["high"] - max(row["open"], row["close"])


def lower_shadow(row: pd.Series) -> float:
    return min(row["open"], row["close"]) - row["low"]


def is_bullish(row: pd.Series) -> bool:
    return row["close"] > row["open"]


def is_bearish(row: pd.Series) -> bool:
    return row["close"] < row["open"]


def body_top(row: pd.Series) -> float:
    return max(row["open"], row["close"])


def body_bottom(row: pd.Series) -> float:
    return min(row["open"], row["close"])


def avg_range(df: pd.DataFrame, window: int = 14) -> float:
    ranges = df["high"] - df["low"]
    return float(ranges.tail(window).mean())
