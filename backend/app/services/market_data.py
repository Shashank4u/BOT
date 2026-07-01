"""Market data service — orchestrates MT5 provider calls."""

from datetime import datetime

from app.core.logging import get_logger
from app.trading.connection import get_provider
from app.trading.types import AccountInfo, ConnectionStatus, OHLCBar, TickPrice, Timeframe

logger = get_logger(__name__)


class MarketDataService:
    """High-level market data operations."""

    def _ensure_connected(self) -> None:
        """Auto-connect using env credentials if not already connected."""
        provider = get_provider()
        if not provider.get_status().connected:
            provider.connect()

    def get_connection_status(self) -> ConnectionStatus:
        return get_provider().get_status()

    def connect(
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
    ) -> ConnectionStatus:
        status = get_provider().connect(login=login, password=password, server=server)
        logger.info("Market data connection: %s", status.message)
        return status

    def disconnect(self) -> ConnectionStatus:
        return get_provider().disconnect()

    def list_symbols(self) -> list[str]:
        self._ensure_connected()
        symbols = get_provider().get_symbols()
        logger.debug("Listed %d symbols", len(symbols))
        return symbols

    def get_price(self, symbol: str) -> TickPrice:
        self._ensure_connected()
        tick = get_provider().get_tick(symbol.upper())
        logger.debug("Tick %s bid=%.5f ask=%.5f", tick.symbol, tick.bid, tick.ask)
        return tick

    def get_prices(self, symbols: list[str]) -> list[TickPrice]:
        self._ensure_connected()
        ticks = get_provider().get_ticks([s.upper() for s in symbols])
        logger.debug("Fetched %d tick prices", len(ticks))
        return ticks

    def get_ohlc(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 100,
        start: datetime | None = None,
    ) -> list[OHLCBar]:
        self._ensure_connected()
        bars = get_provider().get_ohlc(symbol.upper(), timeframe, count, start)
        logger.debug("Fetched %d OHLC bars for %s %s", len(bars), symbol, timeframe.value)
        return bars

    def get_account(self) -> AccountInfo:
        self._ensure_connected()
        return get_provider().get_account_info()


def get_market_service() -> MarketDataService:
    """FastAPI dependency for market data service."""
    return MarketDataService()
