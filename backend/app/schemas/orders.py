"""Order and trade API schemas."""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class MarketOrderRequest(BaseSchema):
    symbol: str
    side: str = Field(pattern="^(buy|sell)$")
    lot_size: float = Field(gt=0, le=100)
    stop_loss: float | None = None
    take_profit: float | None = None
    stop_loss_pips: float | None = Field(default=None, gt=0)
    strategy_id: int | None = None
    magic_number: int = 100001
    entry_reason: str | None = None
    skip_risk_check: bool = False


class PendingOrderRequest(BaseSchema):
    symbol: str
    side: str = Field(pattern="^(buy|sell)$")
    lot_size: float = Field(gt=0, le=100)
    price: float = Field(gt=0)
    stop_loss: float | None = None
    take_profit: float | None = None
    magic_number: int = 100001


class ModifyOrderRequest(BaseSchema):
    stop_loss: float | None = None
    take_profit: float | None = None


class CloseOrderRequest(BaseSchema):
    lot_size: float | None = Field(default=None, gt=0)
    exit_reason: str | None = None


class OrderResultSchema(BaseSchema):
    success: bool
    order_id: int | None = None
    trade_id: int | None = None
    mt5_ticket: int | None = None
    symbol: str
    side: str
    lot_size: float
    price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    message: str
    is_demo: bool
    disclaimer: str = (
        "Order execution does not guarantee profit. "
        "Trading involves substantial risk of loss."
    )


class TradeResponseSchema(BaseSchema):
    id: int
    symbol: str
    direction: str
    status: str
    lot_size: float
    entry_price: float
    exit_price: float | None
    stop_loss: float | None
    take_profit: float | None
    profit_loss: float | None
    opened_at: datetime
    closed_at: datetime | None
    entry_reason: str | None
    exit_reason: str | None
    strategy_id: int | None
    mt5_ticket: int | None


class PositionSchema(BaseSchema):
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
