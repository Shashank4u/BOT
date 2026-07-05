"""Trading domain types and enums."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Timeframe(str, Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"


# MT5 timeframe constant mapping (used by real provider on Windows)
MT5_TIMEFRAME_MAP: dict[Timeframe, int] = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.M30: 30,
    Timeframe.H1: 16385,
    Timeframe.H4: 16388,
    Timeframe.D1: 16408,
    Timeframe.W1: 32769,
    Timeframe.MN1: 49153,
}


@dataclass(frozen=True)
class TickPrice:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    time: datetime

    @property
    def spread(self) -> float:
        return round(self.ask - self.bid, 8)

    @property
    def mid(self) -> float:
        return round((self.bid + self.ask) / 2, 8)


@dataclass(frozen=True)
class OHLCBar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    spread: int = 0


@dataclass(frozen=True)
class AccountInfo:
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    leverage: int
    profit: float
    name: str


@dataclass(frozen=True)
class ConnectionStatus:
    connected: bool
    provider: str  # "mock" | "mt5"
    server: str | None
    login: int | None
    message: str


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class OrderRequest:
    """Order placement request."""

    symbol: str
    side: OrderSide
    lot_size: float
    stop_loss: float | None = None
    take_profit: float | None = None
    price: float | None = None  # For pending orders
    magic_number: int = 100001
    comment: str = ""


@dataclass
class OrderResult:
    """Result of an order execution attempt."""

    success: bool
    ticket: int | None
    symbol: str
    side: str
    lot_size: float
    price: float
    stop_loss: float | None
    take_profit: float | None
    message: str
    is_demo: bool = True


@dataclass
class PositionInfo:
    """Open position from MT5."""

    ticket: int
    symbol: str
    side: str
    lot_size: float
    open_price: float
    current_price: float
    stop_loss: float | None
    take_profit: float | None
    profit: float
    magic_number: int
    opened_at: datetime
