"""Abstract MT5 data provider interface."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.trading.types import (
    AccountInfo,
    ConnectionStatus,
    OHLCBar,
    OrderRequest,
    OrderResult,
    PositionInfo,
    TickPrice,
    Timeframe,
)


class MT5Provider(ABC):
    """Interface for MT5 market data and account access."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier: 'mock' or 'mt5'."""

    @abstractmethod
    def connect(
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        path: str | None = None,
    ) -> ConnectionStatus:
        """Establish connection to MT5 terminal."""

    @abstractmethod
    def disconnect(self) -> ConnectionStatus:
        """Shut down MT5 connection."""

    @abstractmethod
    def get_status(self) -> ConnectionStatus:
        """Return current connection status."""

    @abstractmethod
    def get_symbols(self) -> list[str]:
        """List available trading symbols."""

    @abstractmethod
    def get_tick(self, symbol: str) -> TickPrice:
        """Get current bid/ask for a symbol."""

    @abstractmethod
    def get_ticks(self, symbols: list[str]) -> list[TickPrice]:
        """Get current prices for multiple symbols."""

    @abstractmethod
    def get_ohlc(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 100,
        start: datetime | None = None,
    ) -> list[OHLCBar]:
        """Fetch OHLC candle data."""

    @abstractmethod
    def get_account_info(self) -> AccountInfo:
        """Return account balance, equity, margin."""

    # --- Order execution ---

    @abstractmethod
    def place_market_order(self, request: OrderRequest) -> OrderResult:
        """Execute a market buy or sell order."""

    @abstractmethod
    def place_pending_order(self, request: OrderRequest) -> OrderResult:
        """Place a pending (limit/stop) order."""

    @abstractmethod
    def close_position(self, ticket: int, lot_size: float | None = None) -> OrderResult:
        """Close an open position (full or partial)."""

    @abstractmethod
    def modify_position(
        self, ticket: int, stop_loss: float | None, take_profit: float | None
    ) -> OrderResult:
        """Modify SL/TP on an open position."""

    @abstractmethod
    def get_positions(self, symbol: str | None = None) -> list[PositionInfo]:
        """List open positions."""
