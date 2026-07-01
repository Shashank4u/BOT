"""Dashboard summary schemas."""

from app.schemas.common import BaseSchema
from app.schemas.market import AccountInfoSchema, ConnectionStatusSchema, TickPriceSchema


class DashboardResponse(BaseSchema):
    """Single-call dashboard payload for the mobile app."""

    connection: ConnectionStatusSchema
    account: AccountInfoSchema
    watchlist_prices: list[TickPriceSchema]
    trading_mode: str
    bot_status: str
    market_status: str
    disclaimer: str = (
        "Market data is for analysis only. This app does not predict prices "
        "or guarantee profits. Trading involves substantial risk."
    )
