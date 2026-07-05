"""Indicator registry — names, defaults, and metadata."""

from enum import Enum


class IndicatorName(str, Enum):
    SMA = "sma"
    EMA = "ema"
    VWAP = "vwap"
    RSI = "rsi"
    MACD = "macd"
    ADX = "adx"
    ATR = "atr"
    BBANDS = "bbands"
    ICHIMOKU = "ichimoku"
    CCI = "cci"
    STOCH = "stoch"
    PSAR = "psar"
    PIVOTS = "pivots"
    SUPERTREND = "supertrend"
    VOLUME_PROFILE = "volume_profile"


INDICATOR_REGISTRY: dict[str, dict] = {
    IndicatorName.SMA.value: {
        "label": "Simple Moving Average",
        "params": {"period": 20},
        "outputs": ["value"],
    },
    IndicatorName.EMA.value: {
        "label": "Exponential Moving Average",
        "params": {"period": 20},
        "outputs": ["value"],
    },
    IndicatorName.VWAP.value: {
        "label": "Volume Weighted Average Price",
        "params": {},
        "outputs": ["value"],
    },
    IndicatorName.RSI.value: {
        "label": "Relative Strength Index",
        "params": {"period": 14},
        "outputs": ["value"],
    },
    IndicatorName.MACD.value: {
        "label": "MACD",
        "params": {"fast": 12, "slow": 26, "signal": 9},
        "outputs": ["macd", "signal", "histogram"],
    },
    IndicatorName.ADX.value: {
        "label": "Average Directional Index",
        "params": {"period": 14},
        "outputs": ["adx", "di_plus", "di_minus"],
    },
    IndicatorName.ATR.value: {
        "label": "Average True Range",
        "params": {"period": 14},
        "outputs": ["value"],
    },
    IndicatorName.BBANDS.value: {
        "label": "Bollinger Bands",
        "params": {"period": 20, "std": 2.0},
        "outputs": ["upper", "middle", "lower"],
    },
    IndicatorName.ICHIMOKU.value: {
        "label": "Ichimoku Cloud",
        "params": {"tenkan": 9, "kijun": 26, "senkou": 52},
        "outputs": [
            "tenkan",
            "kijun",
            "senkou_a",
            "senkou_b",
            "chikou",
        ],
    },
    IndicatorName.CCI.value: {
        "label": "Commodity Channel Index",
        "params": {"period": 20},
        "outputs": ["value"],
    },
    IndicatorName.STOCH.value: {
        "label": "Stochastic Oscillator",
        "params": {"k_period": 14, "d_period": 3},
        "outputs": ["k", "d"],
    },
    IndicatorName.PSAR.value: {
        "label": "Parabolic SAR",
        "params": {"step": 0.02, "max_step": 0.2},
        "outputs": ["value"],
    },
    IndicatorName.PIVOTS.value: {
        "label": "Pivot Points (Classic)",
        "params": {},
        "outputs": ["pivot", "r1", "r2", "r3", "s1", "s2", "s3"],
    },
    IndicatorName.SUPERTREND.value: {
        "label": "SuperTrend",
        "params": {"period": 10, "multiplier": 3.0},
        "outputs": ["value", "direction"],
    },
    IndicatorName.VOLUME_PROFILE.value: {
        "label": "Volume Profile",
        "params": {"bins": 20},
        "outputs": ["poc", "levels"],
    },
}


def parse_indicator_names(raw: str) -> list[str]:
    """Parse comma-separated indicator names and validate."""
    names = [n.strip().lower() for n in raw.split(",") if n.strip()]
    valid = {i.value for i in IndicatorName}
    unknown = [n for n in names if n not in valid]
    if unknown:
        raise ValueError(f"Unknown indicators: {', '.join(unknown)}")
    return names
