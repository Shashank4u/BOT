"""Pattern detection service — fetches OHLC and scans for patterns."""

from typing import Any

from app.core.logging import get_logger
from app.services.market_data import MarketDataService
from app.trading.patterns.detector import PatternDetector
from app.trading.types import Timeframe

logger = get_logger(__name__)

WARMUP_BUFFER = 20


class PatternService:
    """Orchestrates market data retrieval and pattern scanning."""

    def __init__(self, market: MarketDataService | None = None) -> None:
        self._market = market or MarketDataService()
        self._detector = PatternDetector()

    def list_patterns(self) -> list[dict[str, Any]]:
        return self._detector.list_available()

    def scan_symbol(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.H1,
        count: int = 200,
        patterns: list[str] | None = None,
        categories: list[str] | None = None,
        lookback: int = 100,
    ) -> dict[str, Any]:
        fetch_count = min(count + WARMUP_BUFFER, 5000)
        bars = self._market.get_ohlc(symbol, timeframe, fetch_count)
        bars = bars[-count:] if len(bars) > count else bars

        logger.info(
            "Scanning patterns for %s %s (%d bars)",
            symbol,
            timeframe.value,
            len(bars),
        )
        matches = self._detector.scan(
            bars,
            patterns=patterns,
            categories=categories,
            lookback=lookback,
        )
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "bars_scanned": len(bars),
            "patterns": [m.to_dict() for m in matches],
            "summary": self._detector.summarize(matches),
        }

    def scan_recent(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.H1,
        count: int = 200,
        recent_bars: int = 10,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        fetch_count = min(count + WARMUP_BUFFER, 5000)
        bars = self._market.get_ohlc(symbol, timeframe, fetch_count)
        bars = bars[-count:] if len(bars) > count else bars

        matches = self._detector.scan_recent(
            bars,
            recent_bars=recent_bars,
            categories=categories,
        )
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "recent_bars": recent_bars,
            "patterns": [m.to_dict() for m in matches],
        }


def get_pattern_service() -> PatternService:
    return PatternService()
