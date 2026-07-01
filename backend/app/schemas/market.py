"""Market data API schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema
from app.trading.types import Timeframe


class ConnectionStatusSchema(BaseSchema):
    connected: bool
    provider: str
    server: str | None
    login: int | None
    message: str


class ConnectRequest(BaseSchema):
    login: int | None = None
    password: str | None = None
    server: str | None = None


class TickPriceSchema(BaseSchema):
    symbol: str
    bid: float
    ask: float
    last: float
    spread: float
    mid: float
    volume: int
    time: datetime


class OHLCBarSchema(BaseSchema):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    spread: int = 0


class AccountInfoSchema(BaseSchema):
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


class OHLCRequestParams(BaseSchema):
    symbol: str
    timeframe: Timeframe = Timeframe.H1
    count: int = Field(default=100, ge=1, le=5000)
