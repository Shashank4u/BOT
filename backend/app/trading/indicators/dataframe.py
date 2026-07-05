"""Convert OHLC bars to pandas DataFrame for indicator calculations."""

import pandas as pd

from app.trading.types import OHLCBar


def bars_to_dataframe(bars: list[OHLCBar]) -> pd.DataFrame:
    """Build a sorted OHLCV DataFrame from bar objects."""
    if not bars:
        raise ValueError("Cannot compute indicators on empty OHLC data")

    df = pd.DataFrame(
        [
            {
                "time": bar.time,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
            }
            for bar in bars
        ]
    )
    return df.sort_values("time").reset_index(drop=True)
