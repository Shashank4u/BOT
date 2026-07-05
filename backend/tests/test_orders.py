"""Order execution tests."""

import pytest
from httpx import AsyncClient

from app.trading.connection import get_provider, reset_provider
from app.trading.types import OrderRequest, OrderSide


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    provider = get_provider()
    provider.connect()
    yield
    reset_provider()


class TestMockOrderExecution:
    def test_market_buy(self) -> None:
        provider = get_provider()
        result = provider.place_market_order(
            OrderRequest(symbol="EURUSD", side=OrderSide.BUY, lot_size=0.1)
        )
        assert result.success is True
        assert result.ticket is not None
        assert result.is_demo is True

    def test_get_positions_after_buy(self) -> None:
        provider = get_provider()
        provider.place_market_order(
            OrderRequest(symbol="EURUSD", side=OrderSide.BUY, lot_size=0.1)
        )
        positions = provider.get_positions("EURUSD")
        assert len(positions) == 1
        assert positions[0].symbol == "EURUSD"

    def test_close_position(self) -> None:
        provider = get_provider()
        result = provider.place_market_order(
            OrderRequest(symbol="EURUSD", side=OrderSide.BUY, lot_size=0.1)
        )
        close = provider.close_position(result.ticket)
        assert close.success is True
        assert len(provider.get_positions()) == 0


@pytest.mark.asyncio
async def test_calculate_lot_size_api(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/risk/calculate-lot-size",
        json={"balance": 10000, "risk_percent": 1, "stop_loss_pips": 20, "symbol": "EURUSD"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lot_size"] >= 0.01


@pytest.mark.asyncio
async def test_risk_check_api(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/risk/check",
        json={"symbol": "EURUSD", "lot_size": 0.01, "stop_loss_pips": 20, "balance": 10000},
    )
    assert response.status_code == 200
    assert "allowed" in response.json()


@pytest.mark.asyncio
async def test_place_market_order_api(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/orders/market",
        json={
            "symbol": "EURUSD",
            "side": "buy",
            "lot_size": 0.01,
            "stop_loss_pips": 20,
            "entry_reason": "Test order",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_demo"] is True


@pytest.mark.asyncio
async def test_list_trades_api(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/orders/market",
        json={"symbol": "EURUSD", "side": "buy", "lot_size": 0.01, "stop_loss_pips": 20},
    )
    response = await client.get("/api/v1/orders/trades?status=open")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_risk_settings_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/risk/settings")
    assert response.status_code == 200
    assert response.json()["max_risk_per_trade"] == 1.0
