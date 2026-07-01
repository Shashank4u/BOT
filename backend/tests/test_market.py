"""Market data and MT5 mock provider tests."""

import pytest

from app.trading.connection import get_provider, reset_provider
from app.trading.exceptions import MT5NotConnectedError, SymbolNotFoundError
from app.trading.mock_provider import MockMT5Provider
from app.trading.types import Timeframe


@pytest.fixture
def clean_provider():
    """Reset global MT5 provider between isolated unit tests."""
    reset_provider()
    yield
    reset_provider()


class TestMockMT5Provider:
    @pytest.fixture(autouse=True)
    def _reset(self, clean_provider):
        pass
    def test_connect_and_status(self) -> None:
        provider = MockMT5Provider()
        status = provider.connect()
        assert status.connected is True
        assert status.provider == "mock"
        assert "simulated" in status.message.lower()

    def test_disconnect(self) -> None:
        provider = MockMT5Provider()
        provider.connect()
        status = provider.disconnect()
        assert status.connected is False

    def test_requires_connection_for_ticks(self) -> None:
        provider = MockMT5Provider()
        with pytest.raises(MT5NotConnectedError):
            provider.get_tick("EURUSD")

    def test_get_tick(self) -> None:
        provider = MockMT5Provider()
        provider.connect()
        tick = provider.get_tick("EURUSD")
        assert tick.symbol == "EURUSD"
        assert tick.bid < tick.ask
        assert tick.spread > 0

    def test_unknown_symbol(self) -> None:
        provider = MockMT5Provider()
        provider.connect()
        with pytest.raises(SymbolNotFoundError):
            provider.get_tick("INVALID")

    def test_get_ohlc(self) -> None:
        provider = MockMT5Provider()
        provider.connect()
        bars = provider.get_ohlc("XAUUSD", Timeframe.H1, count=50)
        assert len(bars) == 50
        assert bars[0].high >= bars[0].low

    def test_get_account_info(self) -> None:
        provider = MockMT5Provider()
        provider.connect()
        account = provider.get_account_info()
        assert account.balance > 0
        assert account.currency == "USD"

    def test_list_symbols(self) -> None:
        provider = MockMT5Provider()
        provider.connect()
        symbols = provider.get_symbols()
        assert "EURUSD" in symbols
        assert "XAUUSD" in symbols


@pytest.mark.asyncio
async def test_market_status_endpoint(client) -> None:
    # Status endpoint does not auto-connect — connect first
    await client.post("/api/v1/market/connect")
    response = await client.get("/api/v1/market/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["connected"] is True


@pytest.mark.asyncio
async def test_market_price_endpoint(client) -> None:
    response = await client.get("/api/v1/market/price/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert data["bid"] > 0


@pytest.mark.asyncio
async def test_market_ohlc_endpoint(client) -> None:
    response = await client.get("/api/v1/market/ohlc/XAUUSD?timeframe=H1&count=20")
    assert response.status_code == 200
    bars = response.json()
    assert len(bars) == 20
    assert "open" in bars[0]


@pytest.mark.asyncio
async def test_market_account_endpoint(client) -> None:
    response = await client.get("/api/v1/market/account")
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "equity" in data


@pytest.mark.asyncio
async def test_dashboard_endpoint(client) -> None:
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["trading_mode"] == "demo"
    assert len(data["watchlist_prices"]) > 0
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_market_prices_multiple(client) -> None:
    response = await client.get("/api/v1/market/prices?symbols=EURUSD,GBPUSD")
    assert response.status_code == 200
    prices = response.json()
    assert len(prices) == 2
