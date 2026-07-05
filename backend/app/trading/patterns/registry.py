"""Pattern registry — supported candlestick and chart patterns."""

CANDLESTICK_PATTERNS: dict[str, dict] = {
    "hammer": {
        "label": "Hammer",
        "direction": "bullish",
        "description": "Small body at top with long lower shadow — potential reversal up",
    },
    "shooting_star": {
        "label": "Shooting Star",
        "direction": "bearish",
        "description": "Small body at bottom with long upper shadow — potential reversal down",
    },
    "doji": {
        "label": "Doji",
        "direction": "neutral",
        "description": "Open and close nearly equal — indecision",
    },
    "morning_star": {
        "label": "Morning Star",
        "direction": "bullish",
        "description": "Three-candle bullish reversal pattern",
    },
    "evening_star": {
        "label": "Evening Star",
        "direction": "bearish",
        "description": "Three-candle bearish reversal pattern",
    },
    "bullish_engulfing": {
        "label": "Bullish Engulfing",
        "direction": "bullish",
        "description": "Bullish candle fully engulfs prior bearish body",
    },
    "bearish_engulfing": {
        "label": "Bearish Engulfing",
        "direction": "bearish",
        "description": "Bearish candle fully engulfs prior bullish body",
    },
    "harami": {
        "label": "Harami",
        "direction": "neutral",
        "description": "Small body contained within previous large body",
    },
    "inside_bar": {
        "label": "Inside Bar",
        "direction": "neutral",
        "description": "High/low contained within previous bar range",
    },
    "pin_bar": {
        "label": "Pin Bar",
        "direction": "neutral",
        "description": "Long rejection wick with small body — shows rejection",
    },
}

CHART_PATTERNS: dict[str, dict] = {
    "double_top": {
        "label": "Double Top",
        "direction": "bearish",
        "description": "Two peaks at similar level — potential bearish reversal",
    },
    "double_bottom": {
        "label": "Double Bottom",
        "direction": "bullish",
        "description": "Two troughs at similar level — potential bullish reversal",
    },
    "head_shoulders": {
        "label": "Head and Shoulders",
        "direction": "bearish",
        "description": "Three peaks with middle highest — bearish reversal",
    },
    "inverse_head_shoulders": {
        "label": "Inverse Head and Shoulders",
        "direction": "bullish",
        "description": "Three troughs with middle lowest — bullish reversal",
    },
    "triangle": {
        "label": "Triangle",
        "direction": "neutral",
        "description": "Converging highs and lows — breakout pending",
    },
    "ascending_triangle": {
        "label": "Ascending Triangle",
        "direction": "bullish",
        "description": "Flat resistance with rising support",
    },
    "descending_triangle": {
        "label": "Descending Triangle",
        "direction": "bearish",
        "description": "Flat support with falling resistance",
    },
    "rectangle": {
        "label": "Rectangle",
        "direction": "neutral",
        "description": "Horizontal support and resistance channel",
    },
    "cup_handle": {
        "label": "Cup and Handle",
        "direction": "bullish",
        "description": "Rounded bottom followed by small consolidation",
    },
    "flag": {
        "label": "Flag",
        "direction": "neutral",
        "description": "Sharp move followed by parallel consolidation",
    },
    "pennant": {
        "label": "Pennant",
        "direction": "neutral",
        "description": "Sharp move followed by converging consolidation",
    },
    "wedge": {
        "label": "Wedge",
        "direction": "neutral",
        "description": "Converging trendlines sloping same direction",
    },
    "channel": {
        "label": "Channel",
        "direction": "neutral",
        "description": "Parallel support and resistance lines",
    },
}

ALL_PATTERNS = {**CANDLESTICK_PATTERNS, **CHART_PATTERNS}


def parse_pattern_names(raw: str) -> list[str]:
    names = [n.strip().lower() for n in raw.split(",") if n.strip()]
    unknown = [n for n in names if n not in ALL_PATTERNS]
    if unknown:
        raise ValueError(f"Unknown patterns: {', '.join(unknown)}")
    return names


def parse_categories(raw: str) -> list[str]:
    cats = [c.strip().lower() for c in raw.split(",") if c.strip()]
    valid = {"candlestick", "chart"}
    unknown = [c for c in cats if c not in valid]
    if unknown:
        raise ValueError(f"Unknown categories: {', '.join(unknown)}")
    return cats
