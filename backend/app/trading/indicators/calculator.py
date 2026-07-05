"""Technical indicator calculator using ta library and custom implementations."""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import (
    ADXIndicator,
    CCIIndicator,
    EMAIndicator,
    IchimokuIndicator,
    MACD,
    PSARIndicator,
    SMAIndicator,
)
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import VolumeWeightedAveragePrice

from app.core.logging import get_logger
from app.trading.indicators.dataframe import bars_to_dataframe
from app.trading.indicators.registry import INDICATOR_REGISTRY, IndicatorName
from app.trading.types import OHLCBar

logger = get_logger(__name__)

MIN_BARS = 30


class IndicatorCalculator:
    """Compute technical indicators from OHLC bar data."""

    def list_available(self) -> list[dict[str, Any]]:
        """Return metadata for all supported indicators."""
        return [
            {"name": name, **meta}
            for name, meta in INDICATOR_REGISTRY.items()
        ]

    def compute(
        self,
        bars: list[OHLCBar],
        indicators: list[str],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Compute requested indicators on OHLC bars.
        Returns a dict keyed by indicator name with values + latest snapshot.
        """
        if len(bars) < MIN_BARS:
            raise ValueError(
                f"Need at least {MIN_BARS} bars for reliable indicators, got {len(bars)}"
            )

        df = bars_to_dataframe(bars)
        params = params or {}
        results: dict[str, Any] = {}

        for name in indicators:
            merged = {**INDICATOR_REGISTRY[name]["params"], **params.get(name, {})}
            try:
                results[name] = self._dispatch(name, df, merged)
            except Exception as exc:
                logger.error("Failed to compute %s: %s", name, exc)
                raise ValueError(f"Indicator '{name}' computation failed: {exc}") from exc

        return results

    def _dispatch(self, name: str, df: pd.DataFrame, p: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            IndicatorName.SMA.value: self._sma,
            IndicatorName.EMA.value: self._ema,
            IndicatorName.VWAP.value: self._vwap,
            IndicatorName.RSI.value: self._rsi,
            IndicatorName.MACD.value: self._macd,
            IndicatorName.ADX.value: self._adx,
            IndicatorName.ATR.value: self._atr,
            IndicatorName.BBANDS.value: self._bbands,
            IndicatorName.ICHIMOKU.value: self._ichimoku,
            IndicatorName.CCI.value: self._cci,
            IndicatorName.STOCH.value: self._stoch,
            IndicatorName.PSAR.value: self._psar,
            IndicatorName.PIVOTS.value: self._pivots,
            IndicatorName.SUPERTREND.value: self._supertrend,
            IndicatorName.VOLUME_PROFILE.value: self._volume_profile,
        }
        return handlers[name](df, p)

    def _pack(
        self,
        df: pd.DataFrame,
        fields: dict[str, pd.Series],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Serialize indicator series into API-friendly structure."""
        values: list[dict[str, Any]] = []
        for i in range(len(df)):
            row: dict[str, Any] = {"time": df.at[i, "time"].isoformat()}
            has_data = False
            for key, series in fields.items():
                val = series.iloc[i] if i < len(series) else np.nan
                if pd.notna(val):
                    row[key] = round(float(val), 6) if isinstance(val, (float, np.floating)) else val
                    has_data = True
                else:
                    row[key] = None
            if has_data:
                values.append(row)

        latest: dict[str, Any] = {}
        for key, series in fields.items():
            cleaned = series.dropna()
            if len(cleaned) > 0:
                val = cleaned.iloc[-1]
                latest[key] = round(float(val), 6) if isinstance(val, (float, np.floating)) else val

        return {
            "params": params,
            "values": values,
            "latest": latest,
        }

    def _sma(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        period = int(p["period"])
        series = SMAIndicator(df["close"], window=period).sma_indicator()
        return self._pack(df, {"value": series}, p)

    def _ema(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        period = int(p["period"])
        series = EMAIndicator(df["close"], window=period).ema_indicator()
        return self._pack(df, {"value": series}, p)

    def _vwap(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        series = VolumeWeightedAveragePrice(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            volume=df["volume"],
        ).volume_weighted_average_price()
        return self._pack(df, {"value": series}, p)

    def _rsi(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        period = int(p["period"])
        series = RSIIndicator(df["close"], window=period).rsi()
        return self._pack(df, {"value": series}, p)

    def _macd(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        macd = MACD(
            df["close"],
            window_fast=int(p["fast"]),
            window_slow=int(p["slow"]),
            window_sign=int(p["signal"]),
        )
        return self._pack(
            df,
            {
                "macd": macd.macd(),
                "signal": macd.macd_signal(),
                "histogram": macd.macd_diff(),
            },
            p,
        )

    def _adx(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        period = int(p["period"])
        adx = ADXIndicator(df["high"], df["low"], df["close"], window=period)
        return self._pack(
            df,
            {
                "adx": adx.adx(),
                "di_plus": adx.adx_pos(),
                "di_minus": adx.adx_neg(),
            },
            p,
        )

    def _atr(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        period = int(p["period"])
        series = AverageTrueRange(
            df["high"], df["low"], df["close"], window=period
        ).average_true_range()
        return self._pack(df, {"value": series}, p)

    def _bbands(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        bb = BollingerBands(
            df["close"],
            window=int(p["period"]),
            window_dev=float(p["std"]),
        )
        return self._pack(
            df,
            {
                "upper": bb.bollinger_hband(),
                "middle": bb.bollinger_mavg(),
                "lower": bb.bollinger_lband(),
            },
            p,
        )

    def _ichimoku(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        ichi = IchimokuIndicator(
            df["high"],
            df["low"],
            window1=int(p["tenkan"]),
            window2=int(p["kijun"]),
            window3=int(p["senkou"]),
        )
        return self._pack(
            df,
            {
                "tenkan": ichi.ichimoku_conversion_line(),
                "kijun": ichi.ichimoku_base_line(),
                "senkou_a": ichi.ichimoku_a(),
                "senkou_b": ichi.ichimoku_b(),
                "chikou": df["close"].shift(-int(p["kijun"])),
            },
            p,
        )

    def _cci(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        period = int(p["period"])
        series = CCIIndicator(
            df["high"], df["low"], df["close"], window=period
        ).cci()
        return self._pack(df, {"value": series}, p)

    def _stoch(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        stoch = StochasticOscillator(
            df["high"],
            df["low"],
            df["close"],
            window=int(p["k_period"]),
            smooth_window=int(p["d_period"]),
        )
        return self._pack(
            df,
            {"k": stoch.stoch(), "d": stoch.stoch_signal()},
            p,
        )

    def _psar(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        series = PSARIndicator(
            df["high"],
            df["low"],
            df["close"],
            step=float(p["step"]),
            max_step=float(p["max_step"]),
        ).psar()
        return self._pack(df, {"value": series}, p)

    def _pivots(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        """Classic pivot points from the prior bar's HLC."""
        high = df["high"].shift(1)
        low = df["low"].shift(1)
        close = df["close"].shift(1)

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return self._pack(
            df,
            {
                "pivot": pivot,
                "r1": r1,
                "r2": r2,
                "r3": r3,
                "s1": s1,
                "s2": s2,
                "s3": s3,
            },
            p,
        )

    def _supertrend(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        """SuperTrend indicator with direction (+1 bullish, -1 bearish)."""
        period = int(p["period"])
        multiplier = float(p["multiplier"])

        atr = AverageTrueRange(
            df["high"], df["low"], df["close"], window=period
        ).average_true_range()
        hl2 = (df["high"] + df["low"]) / 2
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        supertrend = pd.Series(np.nan, index=df.index, dtype=float)
        direction = pd.Series(np.nan, index=df.index, dtype=float)

        for i in range(period, len(df)):
            if i == period:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1.0
                continue

            prev_st = supertrend.iloc[i - 1]
            prev_dir = direction.iloc[i - 1]

            curr_upper = upper_band.iloc[i]
            curr_lower = lower_band.iloc[i]
            close = df["close"].iloc[i]

            if prev_dir == 1:
                curr_lower = max(curr_lower, lower_band.iloc[i - 1])
            else:
                curr_upper = min(curr_upper, upper_band.iloc[i - 1])

            if prev_st is not None and close > prev_st:
                direction.iloc[i] = 1.0
                supertrend.iloc[i] = curr_lower
            else:
                direction.iloc[i] = -1.0
                supertrend.iloc[i] = curr_upper

        return self._pack(df, {"value": supertrend, "direction": direction}, p)

    def _volume_profile(self, df: pd.DataFrame, p: dict) -> dict[str, Any]:
        """Simplified volume profile — POC and top price levels by volume."""
        bins = int(p["bins"])
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        price_min = typical_price.min()
        price_max = typical_price.max()

        if price_min == price_max:
            poc = float(price_min)
            levels = [{"price": poc, "volume": float(df["volume"].sum())}]
        else:
            hist, edges = np.histogram(
                typical_price,
                bins=bins,
                weights=df["volume"],
            )
            max_idx = int(np.argmax(hist))
            poc = float((edges[max_idx] + edges[max_idx + 1]) / 2)
            levels = []
            for i, vol in enumerate(hist):
                if vol > 0:
                    price = float((edges[i] + edges[i + 1]) / 2)
                    levels.append({"price": round(price, 6), "volume": round(float(vol), 2)})
            levels.sort(key=lambda x: x["volume"], reverse=True)
            levels = levels[:10]

        latest_time: datetime = df["time"].iloc[-1]
        return {
            "params": p,
            "values": [
                {
                    "time": latest_time.isoformat(),
                    "poc": round(poc, 6),
                    "levels": levels,
                }
            ],
            "latest": {"poc": round(poc, 6), "levels": levels},
        }
