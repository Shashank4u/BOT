"""Real MetaTrader 5 provider — Windows only."""

import sys
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.trading.exceptions import MT5Error, MT5NotConnectedError, SymbolNotFoundError
from app.trading.provider import MT5Provider
from app.trading.types import (
    AccountInfo,
    ConnectionStatus,
    OHLCBar,
    OrderRequest,
    OrderResult,
    OrderSide,
    PositionInfo,
    TickPrice,
    Timeframe,
)
from app.trading.types import MT5_TIMEFRAME_MAP

logger = get_logger(__name__)


def _import_mt5():
    """Import MetaTrader5 package (Windows only)."""
    if sys.platform != "win32":
        raise MT5Error(
            "MetaTrader5 package is only available on Windows. "
            "Set MT5_USE_MOCK=true for development on macOS/Linux."
        )
    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
    except ImportError as exc:
        raise MT5Error(
            "MetaTrader5 package not installed. "
            "Run: pip install -r requirements-trading.txt"
        ) from exc
    return mt5


class RealMT5Provider(MT5Provider):
    """Production MT5 provider using the official MetaTrader5 Python API."""

    def __init__(self) -> None:
        self._mt5 = None
        self._connected = False
        self._login: int | None = None
        self._server: str | None = None

    @property
    def name(self) -> str:
        return "mt5"

    def _require_mt5(self):
        if self._mt5 is None:
            self._mt5 = _import_mt5()
        return self._mt5

    def connect(
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        path: str | None = None,
    ) -> ConnectionStatus:
        mt5 = self._require_mt5()

        init_kwargs: dict = {"timeout": 15000}
        if path:
            init_kwargs["path"] = path

        # 1) Attach to terminal already logged in via GUI (no re-auth)
        if mt5.initialize(**init_kwargs):
            account = mt5.account_info()
            if account and account.login:
                if login and account.login != login and password and server:
                    mt5.shutdown()
                else:
                    self._connected = True
                    self._login = account.login
                    self._server = account.server
                    logger.info("MT5 connected (login=%s, server=%s)", self._login, self._server)
                    return self.get_status()
            mt5.shutdown()

        # 2) Full initialize with credentials (required by many MT5 builds)
        if login and password and server:
            cred_kwargs = {**init_kwargs, "login": login, "password": password, "server": server}
            if mt5.initialize(**cred_kwargs):
                self._connected = True
                account = mt5.account_info()
                if account:
                    self._login = account.login
                    self._server = account.server
                else:
                    self._login = login
                    self._server = server
                logger.info("MT5 connected (login=%s, server=%s)", self._login, self._server)
                return self.get_status()

            error = mt5.last_error()
            mt5.shutdown()
            raise MT5Error(f"MT5 initialize failed: {error}")

        raise MT5Error(
            "MT5 not connected — open terminal, log in to your account, enable "
            "'Allow algorithmic trading', then restart the backend"
        )

    def disconnect(self) -> ConnectionStatus:
        if self._mt5 and self._connected:
            self._mt5.shutdown()
        self._connected = False
        logger.info("MT5 disconnected")
        return self.get_status()

    def get_status(self) -> ConnectionStatus:
        if not self._connected:
            return ConnectionStatus(
                connected=False,
                provider="mt5",
                server=self._server,
                login=self._login,
                message="Not connected to MT5",
            )
        return ConnectionStatus(
            connected=True,
            provider="mt5",
            server=self._server,
            login=self._login,
            message="Connected to MetaTrader 5",
        )

    def _require_connected(self) -> None:
        if not self._connected:
            raise MT5NotConnectedError()

    def get_symbols(self) -> list[str]:
        self._require_connected()
        mt5 = self._require_mt5()
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        return [s.name for s in symbols if s.visible]

    def get_tick(self, symbol: str) -> TickPrice:
        self._require_connected()
        mt5 = self._require_mt5()
        symbol = symbol.upper()
        if not mt5.symbol_select(symbol, True):
            raise SymbolNotFoundError(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise SymbolNotFoundError(symbol)

        return TickPrice(
            symbol=symbol,
            bid=tick.bid,
            ask=tick.ask,
            last=tick.last,
            volume=tick.volume,
            time=datetime.fromtimestamp(tick.time, tz=UTC),
        )

    def get_ticks(self, symbols: list[str]) -> list[TickPrice]:
        return [self.get_tick(s) for s in symbols]

    def get_ohlc(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 100,
        start: datetime | None = None,
    ) -> list[OHLCBar]:
        self._require_connected()
        mt5 = self._require_mt5()
        symbol = symbol.upper()
        tf = MT5_TIMEFRAME_MAP[timeframe]
        count = min(max(count, 1), 5000)

        if start:
            rates = mt5.copy_rates_from(symbol, tf, start, count)
        else:
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)

        if rates is None or len(rates) == 0:
            raise SymbolNotFoundError(symbol)

        return [
            OHLCBar(
                time=datetime.fromtimestamp(r["time"], tz=UTC),
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=int(r["tick_volume"]),
                spread=int(r["spread"]),
            )
            for r in rates
        ]

    def get_account_info(self) -> AccountInfo:
        self._require_connected()
        mt5 = self._require_mt5()
        info = mt5.account_info()
        if info is None:
            raise MT5Error("Failed to retrieve account info")

        return AccountInfo(
            login=info.login,
            server=info.server,
            balance=float(info.balance),
            equity=float(info.equity),
            margin=float(info.margin),
            free_margin=float(info.margin_free),
            margin_level=float(info.margin_level),
            currency=info.currency,
            leverage=info.leverage,
            profit=float(info.profit),
            name=info.name,
        )

    def place_market_order(self, request: OrderRequest) -> OrderResult:
        self._require_connected()
        mt5 = self._require_mt5()
        symbol = request.symbol.upper()
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise SymbolNotFoundError(symbol)

        order_type = mt5.ORDER_TYPE_BUY if request.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL
        price = tick.ask if request.side == OrderSide.BUY else tick.bid

        request_dict = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": request.lot_size,
            "type": order_type,
            "price": price,
            "magic": request.magic_number,
            "comment": request.comment or "AI Trading Assistant",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        if request.stop_loss:
            request_dict["sl"] = request.stop_loss
        if request.take_profit:
            request_dict["tp"] = request.take_profit

        result = mt5.order_send(request_dict)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            msg = str(mt5.last_error()) if result is None else result.comment
            return OrderResult(
                success=False, ticket=None, symbol=symbol, side=request.side.value,
                lot_size=request.lot_size, price=price,
                stop_loss=request.stop_loss, take_profit=request.take_profit,
                message=msg, is_demo=False,
            )
        return OrderResult(
            success=True, ticket=result.order, symbol=symbol, side=request.side.value,
            lot_size=request.lot_size, price=result.price,
            stop_loss=request.stop_loss, take_profit=request.take_profit,
            message="Order filled", is_demo=False,
        )

    def place_pending_order(self, request: OrderRequest) -> OrderResult:
        self._require_connected()
        mt5 = self._require_mt5()
        if request.price is None:
            return OrderResult(
                success=False, ticket=None, symbol=request.symbol, side=request.side.value,
                lot_size=request.lot_size, price=0, stop_loss=request.stop_loss,
                take_profit=request.take_profit, message="Price required", is_demo=False,
            )
        order_type = (
            mt5.ORDER_TYPE_BUY_LIMIT if request.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL_LIMIT
        )
        result = mt5.order_send({
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": request.symbol.upper(),
            "volume": request.lot_size,
            "type": order_type,
            "price": request.price,
            "magic": request.magic_number,
            "type_time": mt5.ORDER_TIME_GTC,
        })
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            return OrderResult(
                success=False, ticket=None, symbol=request.symbol, side=request.side.value,
                lot_size=request.lot_size, price=request.price or 0,
                stop_loss=request.stop_loss, take_profit=request.take_profit,
                message="Pending order failed", is_demo=False,
            )
        return OrderResult(
            success=True, ticket=result.order, symbol=request.symbol.upper(),
            side=request.side.value, lot_size=request.lot_size, price=request.price,
            stop_loss=request.stop_loss, take_profit=request.take_profit,
            message="Pending order placed", is_demo=False,
        )

    def close_position(self, ticket: int, lot_size: float | None = None) -> OrderResult:
        self._require_connected()
        mt5 = self._require_mt5()
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return OrderResult(
                success=False, ticket=ticket, symbol="", side="", lot_size=0, price=0,
                stop_loss=None, take_profit=None, message="Position not found", is_demo=False,
            )
        pos = position[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        volume = lot_size or pos.volume
        result = mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "magic": pos.magic,
        })
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            return OrderResult(
                success=False, ticket=ticket, symbol=pos.symbol, side="", lot_size=volume,
                price=price, stop_loss=None, take_profit=None, message="Close failed", is_demo=False,
            )
        return OrderResult(
            success=True, ticket=ticket, symbol=pos.symbol,
            side="buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
            lot_size=volume, price=result.price, stop_loss=None, take_profit=None,
            message="Position closed", is_demo=False,
        )

    def modify_position(
        self, ticket: int, stop_loss: float | None, take_profit: float | None
    ) -> OrderResult:
        self._require_connected()
        mt5 = self._require_mt5()
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return OrderResult(
                success=False, ticket=ticket, symbol="", side="", lot_size=0, price=0,
                stop_loss=None, take_profit=None, message="Position not found", is_demo=False,
            )
        pos = position[0]
        req: dict = {"action": mt5.TRADE_ACTION_SLTP, "position": ticket, "symbol": pos.symbol}
        if stop_loss is not None:
            req["sl"] = stop_loss
        if take_profit is not None:
            req["tp"] = take_profit
        result = mt5.order_send(req)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            return OrderResult(
                success=False, ticket=ticket, symbol=pos.symbol, side="", lot_size=pos.volume,
                price=pos.price_open, stop_loss=stop_loss, take_profit=take_profit,
                message="Modify failed", is_demo=False,
            )
        return OrderResult(
            success=True, ticket=ticket, symbol=pos.symbol,
            side="buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
            lot_size=pos.volume, price=pos.price_open,
            stop_loss=stop_loss, take_profit=take_profit,
            message="Position modified", is_demo=False,
        )

    def get_positions(self, symbol: str | None = None) -> list[PositionInfo]:
        self._require_connected()
        mt5 = self._require_mt5()
        kwargs = {"symbol": symbol.upper()} if symbol else {}
        positions = mt5.positions_get(**kwargs) or []
        result = []
        for pos in positions:
            result.append(PositionInfo(
                ticket=pos.ticket,
                symbol=pos.symbol,
                side="buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
                lot_size=pos.volume,
                open_price=pos.price_open,
                current_price=pos.price_current,
                stop_loss=pos.sl if pos.sl else None,
                take_profit=pos.tp if pos.tp else None,
                profit=pos.profit,
                magic_number=pos.magic,
                opened_at=datetime.fromtimestamp(pos.time, tz=UTC),
            ))
        return result
