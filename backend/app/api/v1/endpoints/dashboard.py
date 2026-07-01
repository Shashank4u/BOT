"""Dashboard endpoint — balance, equity, prices in one call."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.schemas.market import AccountInfoSchema, ConnectionStatusSchema, TickPriceSchema
from app.services.market_data import MarketDataService, get_market_service
from app.trading.constants import DEFAULT_SYMBOLS

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

MarketSvc = Annotated[MarketDataService, Depends(get_market_service)]


@router.get("", response_model=DashboardResponse)
async def get_dashboard(db: DbSession, svc: MarketSvc) -> DashboardResponse:
    """
    Dashboard summary: account info, connection status, and watchlist prices.
    Designed for single-user app — no login required.
    """
    settings = get_settings()

    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("Owner", "default")

    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    user_settings = settings_result.scalar_one_or_none()
    watchlist = (
        user_settings.watchlist_symbols
        if user_settings and user_settings.watchlist_symbols
        else DEFAULT_SYMBOLS
    )

    connection = svc.get_connection_status()
    if not connection.connected:
        svc.connect()

    account = svc.get_account()
    prices = svc.get_prices(watchlist[:10])

    return DashboardResponse(
        connection=ConnectionStatusSchema.model_validate(connection),
        account=AccountInfoSchema.model_validate(account),
        watchlist_prices=[
            TickPriceSchema(
                symbol=t.symbol,
                bid=t.bid,
                ask=t.ask,
                last=t.last,
                spread=t.spread,
                mid=t.mid,
                volume=t.volume,
                time=t.time,
            )
            for t in prices
        ],
        trading_mode=settings.trading_mode.value,
        bot_status="idle",
        market_status="open" if connection.connected else "disconnected",
    )
