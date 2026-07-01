"""Indicator service — fetches OHLC and computes technical indicators."""

from typing import Any

from app.core.logging import get_logger
from app.services.market_data import MarketDataService
from app.trading.indicators.calculator import IndicatorCalculator
from app.trading.indicators.registry import parse_indicator_names
from app.trading.types import Timeframe

logger = get_logger(__name__)

# Fetch extra bars so slow indicators (Ichimoku 52) have enough warmup data
WARMUP_BUFFER = 60


class IndicatorService:
    """Orchestrates market data retrieval and indicator computation."""

    def __init__(self, market: MarketDataService | None = None) -> None:
        self._market = market or MarketDataService()
        self._calculator = IndicatorCalculator()

    def list_indicators(self) -> list[dict[str, Any]]:
        return self._calculator.list_available()

    def compute_for_symbol(
        self,
        symbol: str,
        indicators: list[str],
        timeframe: Timeframe = Timeframe.H1,
        count: int = 200,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch OHLC from MT5 and compute indicators."""
        fetch_count = min(count + WARMUP_BUFFER, 5000)
        bars = self._market.get_ohlc(symbol, timeframe, fetch_count)

        # Use the most recent `count` bars for output alignment
        bars = bars[-count:] if len(bars) > count else bars

        logger.info(
            "Computing %d indicators for %s %s (%d bars)",
            len(indicators),
            symbol,
            timeframe.value,
            len(bars),
        )
        computed = self._calculator.compute(bars, indicators, params)
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "bars_used": len(bars),
            "indicators": computed,
        }

    def snapshot(
        self,
        symbol: str,
        indicators: list[str],
        timeframe: Timeframe = Timeframe.H1,
        count: int = 200,
    ) -> dict[str, Any]:
        """Return latest values only for each indicator."""
        result = self.compute_for_symbol(symbol, indicators, timeframe, count)
        snapshot = {
            name: data["latest"]
            for name, data in result["indicators"].items()
            if data.get("latest")
        }
        return {
            "symbol": result["symbol"],
            "timeframe": result["timeframe"],
            "snapshot": snapshot,
        }


def get_indicator_service() -> IndicatorService:
    return IndicatorService()
