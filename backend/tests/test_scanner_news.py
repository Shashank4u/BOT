"""Market scanner and news tests."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.trading.connection import get_provider, reset_provider
from app.trading.news.guard import is_trading_paused
from app.trading.scanner.engine import MarketScanner
from app.trading.types import Timeframe


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    provider = get_provider()
    provider.connect()
    yield
    reset_provider()


class TestNewsGuard:
    def test_paused_during_high_impact_window(self) -> None:
        now = datetime.now(UTC)
        events = [{
            "title": "US NFP",
            "currency": "USD",
            "impact": "high",
            "event_time": now + timedelta(minutes=10),
        }]
        paused, reason = is_trading_paused("EURUSD", events, ["high"], now=now)
        assert paused is True
        assert reason is not None

    def test_not_paused_for_unrelated_currency(self) -> None:
        now = datetime.now(UTC)
        events = [{
            "title": "AUD Employment",
            "currency": "AUD",
            "impact": "high",
            "event_time": now + timedelta(minutes=10),
        }]
        paused, _ = is_trading_paused("EURUSD", events, ["high"], now=now)
        assert paused is False

    def test_medium_impact_filtered_out(self) -> None:
        now = datetime.now(UTC)
        events = [{
            "title": "US Retail Sales",
            "currency": "USD",
            "impact": "medium",
            "event_time": now + timedelta(minutes=10),
        }]
        paused, _ = is_trading_paused("EURUSD", events, ["high"], now=now)
        assert paused is False


class TestMarketScanner:
    def test_scan_symbol(self) -> None:
        scanner = MarketScanner()
        result = scanner.scan_symbol("EURUSD", Timeframe.H1, "ema_cross")
        assert result["symbol"] == "EURUSD"
        assert result["signal"] in ("buy", "sell", "hold")
        assert 0 <= result["score"] <= 100

    def test_scan_many_sorted(self) -> None:
        scanner = MarketScanner()
        results = scanner.scan_many(["EURUSD", "GBPUSD"], Timeframe.H1)
        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]


@pytest.mark.asyncio
async def test_news_sync_api(client: AsyncClient) -> None:
    response = await client.post("/api/v1/news/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["fetched"] > 0


@pytest.mark.asyncio
async def test_news_calendar_api(client: AsyncClient) -> None:
    await client.post("/api/v1/news/sync")
    response = await client.get("/api/v1/news/calendar?impact=high")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[0]["impact"] == "high"


@pytest.mark.asyncio
async def test_high_impact_events_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/news/high-impact")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_trading_pause_status_api(client: AsyncClient) -> None:
    response = await client.get("/api/v1/news/pause-status/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert "paused" in data


@pytest.mark.asyncio
async def test_scanner_run_api(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/scanner/run",
        json={"symbols": ["EURUSD", "GBPUSD"], "save": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert len(data["results"]) == 2
    assert data["summary"]["total"] == 2


@pytest.mark.asyncio
async def test_scanner_list_and_get(client: AsyncClient) -> None:
    run = await client.post(
        "/api/v1/scanner/run",
        json={"symbols": ["EURUSD"], "save": True},
    )
    scan_id = run.json()["id"]

    listing = await client.get("/api/v1/scanner/runs")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1

    detail = await client.get(f"/api/v1/scanner/runs/{scan_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == scan_id


@pytest.mark.asyncio
async def test_news_pause_blocks_order_when_enabled(client: AsyncClient, monkeypatch) -> None:
    from app.trading.risk.manager import RiskManager

    async def fake_news_pause(self, symbol: str, settings) -> str | None:
        if settings.pause_trading_during_news:
            return "Trading paused: test high-impact news event"
        return None

    monkeypatch.setattr(RiskManager, "_check_news_pause", fake_news_pause)

    await client.patch(
        "/api/v1/news/settings",
        json={"pause_trading_during_news": True, "news_impact_filter": ["high"]},
    )
    response = await client.post(
        "/api/v1/risk/check",
        json={"symbol": "EURUSD", "lot_size": 0.01, "stop_loss_pips": 20, "balance": 10000},
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is False
    assert any("paused" in v.lower() for v in response.json()["violations"])

    await client.patch(
        "/api/v1/news/settings",
        json={"pause_trading_during_news": False},
    )
