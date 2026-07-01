"""Analytics and Telegram notification tests."""

import pytest
from httpx import AsyncClient

from app.notifications.telegram_client import TelegramClient
from app.trading.connection import get_provider, reset_provider


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    provider = get_provider()
    provider.connect()
    yield
    reset_provider()


class TestTelegramClient:
    @pytest.mark.asyncio
    async def test_mock_mode_without_token(self) -> None:
        client = TelegramClient()
        assert client.is_mock is True
        result = await client.send_message("Test message")
        assert result.success is True
        assert result.is_mock is True


@pytest.mark.asyncio
async def test_telegram_status_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/telegram/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_mock"] is True


@pytest.mark.asyncio
async def test_telegram_test_message_api(client: AsyncClient) -> None:
    response = await client.post("/api/v1/telegram/test")
    assert response.status_code == 200
    data = response.json()
    assert data["sent"] is True
    assert data["is_mock"] is True


@pytest.mark.asyncio
async def test_analytics_overview_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analytics/overview?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "win_rate" in data
    assert "total_pnl" in data
    assert "current_balance" in data


@pytest.mark.asyncio
async def test_equity_curve_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analytics/equity-curve")
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert len(data["points"]) >= 1


@pytest.mark.asyncio
async def test_pnl_by_symbol_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analytics/pnl-by-symbol")
    assert response.status_code == 200
    assert "symbols" in response.json()


@pytest.mark.asyncio
async def test_daily_pnl_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analytics/daily-pnl")
    assert response.status_code == 200
    assert "series" in response.json()


@pytest.mark.asyncio
async def test_heatmap_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analytics/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert "session_heatmap" in data
    assert "symbol_performance" in data
    assert len(data["session_heatmap"]) == 7 * 24


@pytest.mark.asyncio
async def test_trade_open_creates_notification(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/orders/market",
        json={"symbol": "EURUSD", "side": "buy", "lot_size": 0.01, "stop_loss_pips": 20},
    )
    response = await client.get("/api/v1/notifications")
    assert response.status_code == 200
    notifications = response.json()
    assert any(n["category"] == "trade_open" for n in notifications)


@pytest.mark.asyncio
async def test_notifications_mark_read(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/orders/market",
        json={"symbol": "EURUSD", "side": "buy", "lot_size": 0.01, "stop_loss_pips": 20},
    )
    notifs = await client.get("/api/v1/notifications?unread_only=true")
    if notifs.json():
        nid = notifs.json()[0]["id"]
        response = await client.patch(f"/api/v1/notifications/{nid}/read")
        assert response.status_code == 204

    read_all = await client.post("/api/v1/notifications/read-all")
    assert read_all.status_code == 200
