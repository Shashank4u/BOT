"""Market data and MT5 connection endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.market import (
    AccountInfoSchema,
    ConnectRequest,
    ConnectionStatusSchema,
    OHLCBarSchema,
    TickPriceSchema,
)
from app.services.market_data import MarketDataService, get_market_service
from app.trading.types import Timeframe

router = APIRouter(prefix="/market", tags=["Market Data"])

MarketSvc = Annotated[MarketDataService, Depends(get_market_service)]


def _tick_schema(tick) -> TickPriceSchema:
    return TickPriceSchema(
        symbol=tick.symbol,
        bid=tick.bid,
        ask=tick.ask,
        last=tick.last,
        spread=tick.spread,
        mid=tick.mid,
        volume=tick.volume,
        time=tick.time,
    )


@router.get("/status", response_model=ConnectionStatusSchema)
async def connection_status(svc: MarketSvc) -> ConnectionStatusSchema:
    """Get MT5 connection status."""
    status = svc.get_connection_status()
    return ConnectionStatusSchema.model_validate(status)


@router.post("/connect", response_model=ConnectionStatusSchema)
async def connect_mt5(
    svc: MarketSvc,
    body: ConnectRequest | None = None,
) -> ConnectionStatusSchema:
    """Connect to MT5 using request body or environment credentials."""
    req = body or ConnectRequest()
    status = svc.connect(login=req.login, password=req.password, server=req.server)
    return ConnectionStatusSchema.model_validate(status)


@router.post("/disconnect", response_model=ConnectionStatusSchema)
async def disconnect_mt5(svc: MarketSvc) -> ConnectionStatusSchema:
    """Disconnect from MT5."""
    status = svc.disconnect()
    return ConnectionStatusSchema.model_validate(status)


@router.get("/symbols", response_model=list[str])
async def list_symbols(svc: MarketSvc) -> list[str]:
    """List available trading symbols."""
    return svc.list_symbols()


@router.get("/price/{symbol}", response_model=TickPriceSchema)
async def get_symbol_price(symbol: str, svc: MarketSvc) -> TickPriceSchema:
    """Get live bid/ask for a single symbol."""
    return _tick_schema(svc.get_price(symbol))


@router.get("/prices", response_model=list[TickPriceSchema])
async def get_multiple_prices(
    svc: MarketSvc,
    symbols: Annotated[str, Query(description="Comma-separated symbols, e.g. EURUSD,XAUUSD")],
) -> list[TickPriceSchema]:
    """Get live prices for multiple symbols."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return [_tick_schema(t) for t in svc.get_prices(symbol_list)]


@router.get("/ohlc/{symbol}", response_model=list[OHLCBarSchema])
async def get_ohlc_bars(
    symbol: str,
    svc: MarketSvc,
    timeframe: Timeframe = Timeframe.H1,
    count: int = Query(default=100, ge=1, le=5000),
    start: datetime | None = None,
) -> list[OHLCBarSchema]:
    """Fetch OHLC candle data for a symbol and timeframe."""
    bars = svc.get_ohlc(symbol, timeframe, count, start)
    return [OHLCBarSchema.model_validate(b) for b in bars]


@router.get("/account", response_model=AccountInfoSchema)
async def get_account_info(svc: MarketSvc) -> AccountInfoSchema:
    """Get account balance, equity, margin, and profit."""
    return AccountInfoSchema.model_validate(svc.get_account())
