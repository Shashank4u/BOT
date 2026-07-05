"""Mock MT5 provider for development and testing (macOS/Linux)."""

from datetime import UTC, datetime, timedelta

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
from app.trading.constants import DEFAULT_SYMBOLS, MOCK_BASE_PRICES, MOCK_SPREADS
from app.trading.exceptions import MT5NotConnectedError, SymbolNotFoundError
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

logger = get_logger(__name__)

TIMEFRAME_MINUTES: dict[Timeframe, int] = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.M30: 30,
    Timeframe.H1: 60,
    Timeframe.H4: 240,
    Timeframe.D1: 1440,
    Timeframe.W1: 10080,
    Timeframe.MN1: 43200,
}


class MockMT5Provider(MT5Provider):
    """
    Simulated MT5 connection with realistic price movement.
    NEVER used for live trading — development and CI only.
    """

    def __init__(self) -> None:
        self._connected = False
        self._login: int | None = None
        self._server: str | None = None
        self._rng = np.random.default_rng(42)
        self._price_offsets: dict[str, float] = {s: 0.0 for s in DEFAULT_SYMBOLS}
        self._positions: dict[int, dict] = {}
        self._next_ticket = 200001

    @property
    def name(self) -> str:
        return "mock"

    def connect(
        self,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        path: str | None = None,
    ) -> ConnectionStatus:
        settings = get_settings()
        self._connected = True
        self._login = login or settings.mt5_login or 12345678
        self._server = server or settings.mt5_server
        logger.info("Mock MT5 connected (login=%s, server=%s)", self._login, self._server)
        return self.get_status()

    def disconnect(self) -> ConnectionStatus:
        self._connected = False
        logger.info("Mock MT5 disconnected")
        return self.get_status()

    def get_status(self) -> ConnectionStatus:
        return ConnectionStatus(
            connected=self._connected,
            provider="mock",
            server=self._server,
            login=self._login,
            message="Mock provider — simulated data only, not real market prices",
        )

    def _require_connected(self) -> None:
        if not self._connected:
            raise MT5NotConnectedError()

    def get_symbols(self) -> list[str]:
        self._require_connected()
        return list(DEFAULT_SYMBOLS)

    def _base_price(self, symbol: str) -> float:
        if symbol not in MOCK_BASE_PRICES:
            raise SymbolNotFoundError(symbol)
        # Small random walk on each tick request
        drift = self._rng.normal(0, self._volatility(symbol))
        self._price_offsets[symbol] = self._price_offsets.get(symbol, 0.0) + drift
        return MOCK_BASE_PRICES[symbol] + self._price_offsets.get(symbol, 0.0)

    def _volatility(self, symbol: str) -> float:
        base = MOCK_BASE_PRICES.get(symbol, 1.0)
        if base > 1000:
            return base * 0.0001
        if base > 100:
            return base * 0.0002
        return base * 0.00005

    def get_tick(self, symbol: str) -> TickPrice:
        self._require_connected()
        symbol = symbol.upper()
        mid = self._base_price(symbol)
        half_spread = MOCK_SPREADS.get(symbol, mid * 0.0001) / 2
        bid = round(mid - half_spread, 5)
        ask = round(mid + half_spread, 5)
        return TickPrice(
            symbol=symbol,
            bid=bid,
            ask=ask,
            last=mid,
            volume=int(self._rng.integers(10, 500)),
            time=datetime.now(UTC),
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
        symbol = symbol.upper()
        if symbol not in MOCK_BASE_PRICES:
            raise SymbolNotFoundError(symbol)

        count = min(max(count, 1), 5000)
        minutes = TIMEFRAME_MINUTES[timeframe]
        base = MOCK_BASE_PRICES[symbol]
        vol = self._volatility(symbol) * 10

        returns = self._rng.normal(0, vol, count)
        closes = base * np.cumprod(1 + returns)
        opens = np.roll(closes, 1)
        opens[0] = base

        highs = np.maximum(opens, closes) * (1 + self._rng.uniform(0, vol, count))
        lows = np.minimum(opens, closes) * (1 - self._rng.uniform(0, vol, count))
        volumes = self._rng.integers(50, 5000, count)

        now = start or datetime.now(UTC)
        bars: list[OHLCBar] = []
        for i in range(count):
            bar_time = now - timedelta(minutes=minutes * (count - i))
            bars.append(
                OHLCBar(
                    time=bar_time,
                    open=round(float(opens[i]), 5),
                    high=round(float(highs[i]), 5),
                    low=round(float(lows[i]), 5),
                    close=round(float(closes[i]), 5),
                    volume=int(volumes[i]),
                    spread=int(MOCK_SPREADS.get(symbol, 1) * 100000),
                )
            )
        return bars

    def get_account_info(self) -> AccountInfo:
        self._require_connected()
        settings = get_settings()
        balance = 10000.0 if settings.is_demo_mode else 0.0
        equity = balance + self._rng.uniform(-50, 150)
        margin = max(0.0, self._rng.uniform(0, 500))
        return AccountInfo(
            login=self._login or 12345678,
            server=self._server or settings.mt5_server,
            balance=round(balance, 2),
            equity=round(equity, 2),
            margin=round(margin, 2),
            free_margin=round(equity - margin, 2),
            margin_level=round((equity / margin * 100) if margin > 0 else 0, 2),
            currency="USD",
            leverage=100,
            profit=round(equity - balance, 2),
            name="Demo Account (Mock)",
        )

    def place_market_order(self, request: OrderRequest) -> OrderResult:
        self._require_connected()
        tick = self.get_tick(request.symbol)
        price = tick.ask if request.side == OrderSide.BUY else tick.bid
        ticket = self._next_ticket
        self._next_ticket += 1
        self._positions[ticket] = {
            "ticket": ticket,
            "symbol": request.symbol.upper(),
            "side": request.side.value,
            "lot_size": request.lot_size,
            "open_price": price,
            "stop_loss": request.stop_loss,
            "take_profit": request.take_profit,
            "magic_number": request.magic_number,
            "opened_at": datetime.now(UTC),
        }
        logger.info("Mock market order: %s %s %.2f lots @ %.5f", request.side.value, request.symbol, request.lot_size, price)
        return OrderResult(
            success=True,
            ticket=ticket,
            symbol=request.symbol.upper(),
            side=request.side.value,
            lot_size=request.lot_size,
            price=price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            message="Demo order filled (mock)",
            is_demo=True,
        )

    def place_pending_order(self, request: OrderRequest) -> OrderResult:
        self._require_connected()
        if request.price is None:
            return OrderResult(
                success=False, ticket=None, symbol=request.symbol,
                side=request.side.value, lot_size=request.lot_size, price=0,
                stop_loss=request.stop_loss, take_profit=request.take_profit,
                message="Pending order requires a price", is_demo=True,
            )
        ticket = self._next_ticket
        self._next_ticket += 1
        return OrderResult(
            success=True, ticket=ticket, symbol=request.symbol.upper(),
            side=request.side.value, lot_size=request.lot_size,
            price=request.price, stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            message="Pending order placed (mock)", is_demo=True,
        )

    def close_position(self, ticket: int, lot_size: float | None = None) -> OrderResult:
        self._require_connected()
        pos = self._positions.pop(ticket, None)
        if pos is None:
            return OrderResult(
                success=False, ticket=ticket, symbol="", side="", lot_size=0, price=0,
                stop_loss=None, take_profit=None, message=f"Position {ticket} not found", is_demo=True,
            )
        tick = self.get_tick(pos["symbol"])
        close_price = tick.bid if pos["side"] == "buy" else tick.ask
        close_lots = lot_size or pos["lot_size"]
        return OrderResult(
            success=True, ticket=ticket, symbol=pos["symbol"], side=pos["side"],
            lot_size=close_lots, price=close_price,
            stop_loss=pos["stop_loss"], take_profit=pos["take_profit"],
            message="Position closed (mock)", is_demo=True,
        )

    def modify_position(
        self, ticket: int, stop_loss: float | None, take_profit: float | None
    ) -> OrderResult:
        self._require_connected()
        pos = self._positions.get(ticket)
        if pos is None:
            return OrderResult(
                success=False, ticket=ticket, symbol="", side="", lot_size=0, price=0,
                stop_loss=None, take_profit=None, message=f"Position {ticket} not found", is_demo=True,
            )
        if stop_loss is not None:
            pos["stop_loss"] = stop_loss
        if take_profit is not None:
            pos["take_profit"] = take_profit
        return OrderResult(
            success=True, ticket=ticket, symbol=pos["symbol"], side=pos["side"],
            lot_size=pos["lot_size"], price=pos["open_price"],
            stop_loss=pos["stop_loss"], take_profit=pos["take_profit"],
            message="Position modified (mock)", is_demo=True,
        )

    def get_positions(self, symbol: str | None = None) -> list[PositionInfo]:
        self._require_connected()
        positions = []
        for ticket, pos in self._positions.items():
            if symbol and pos["symbol"] != symbol.upper():
                continue
            tick = self.get_tick(pos["symbol"])
            current = tick.bid if pos["side"] == "buy" else tick.ask
            diff = (current - pos["open_price"]) if pos["side"] == "buy" else (pos["open_price"] - current)
            profit = round(diff * pos["lot_size"] * 100000, 2)
            positions.append(PositionInfo(
                ticket=ticket, symbol=pos["symbol"], side=pos["side"],
                lot_size=pos["lot_size"], open_price=pos["open_price"],
                current_price=current, stop_loss=pos["stop_loss"],
                take_profit=pos["take_profit"], profit=profit,
                magic_number=pos["magic_number"], opened_at=pos["opened_at"],
            ))
        return positions
