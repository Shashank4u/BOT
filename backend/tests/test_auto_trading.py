"""Auto-trading tests."""

import pytest
from httpx import AsyncClient

from app.trading.connection import get_provider, reset_provider


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    get_provider().connect()
    yield
    reset_provider()


@pytest.mark.asyncio
async def test_auto_trading_status_default(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auto-trading/status")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["bot_status"] == "idle"
    assert data["active_strategies"] == 0


@pytest.mark.asyncio
async def test_start_stop_auto_trading(client: AsyncClient) -> None:
    start = await client.post("/api/v1/auto-trading/start")
    assert start.status_code == 200
    assert start.json()["enabled"] is True
    assert start.json()["bot_status"] in ("waiting", "running")

    stop = await client.post("/api/v1/auto-trading/stop")
    assert stop.status_code == 200
    assert stop.json()["enabled"] is False
    assert stop.json()["bot_status"] == "idle"


@pytest.mark.asyncio
async def test_update_auto_trading_settings(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/auto-trading/settings",
        json={"interval_seconds": 120, "min_confidence": 0.5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interval_seconds"] == 120
    assert data["min_confidence"] == 0.5


@pytest.mark.asyncio
async def test_run_once_with_active_strategy(client: AsyncClient) -> None:
    await client.post("/api/v1/strategies/seed-samples")
    strategies = await client.get("/api/v1/strategies")
    assert strategies.status_code == 200
    first = strategies.json()[0]

    await client.patch(
        f"/api/v1/strategies/{first['id']}",
        json={"status": "active"},
    )

    response = await client.post("/api/v1/auto-trading/run-once")
    assert response.status_code == 200
    data = response.json()
    assert data["scanned"] >= 1
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_dashboard_bot_status(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "bot_status" in data
    assert "auto_trading_enabled" in data
    assert "active_strategies" in data
