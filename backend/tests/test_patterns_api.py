"""Pattern detection API integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_patterns_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/patterns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 23
    names = {p["name"] for p in data}
    assert "hammer" in names
    assert "head_shoulders" in names


@pytest.mark.asyncio
async def test_scan_patterns_endpoint(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/patterns/EURUSD?timeframe=H1&count=200&categories=candlestick"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert data["bars_scanned"] == 200
    assert "patterns" in data
    assert "summary" in data
    assert "not trade signals" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_scan_recent_patterns_endpoint(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/patterns/XAUUSD/recent?recent_bars=20&count=200"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recent_bars"] == 20
    for p in data["patterns"]:
        assert p["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_scan_with_name_filter(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/patterns/GBPUSD?names=hammer,doji,inside_bar&count=150"
    )
    assert response.status_code == 200
    for p in response.json()["patterns"]:
        assert p["name"] in {"hammer", "doji", "inside_bar"}


@pytest.mark.asyncio
async def test_invalid_pattern_name(client: AsyncClient) -> None:
    response = await client.get("/api/v1/patterns/EURUSD?names=invalid_pattern")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_invalid_category(client: AsyncClient) -> None:
    response = await client.get("/api/v1/patterns/EURUSD?categories=invalid")
    assert response.status_code == 400
