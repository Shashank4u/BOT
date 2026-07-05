"""Indicator API integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_indicators_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/indicators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 15
    names = {item["name"] for item in data}
    assert "rsi" in names
    assert "supertrend" in names


@pytest.mark.asyncio
async def test_compute_indicators_endpoint(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/indicators/EURUSD?names=rsi,ema,atr&timeframe=H1&count=100"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert data["bars_used"] == 100
    assert "rsi" in data["indicators"]
    assert data["indicators"]["rsi"]["latest"]["value"] is not None
    assert "do not predict" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_indicator_snapshot_endpoint(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/indicators/XAUUSD/snapshot?names=rsi,macd,bbands&count=150"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "XAUUSD"
    assert "rsi" in data["snapshot"]
    assert "value" in data["snapshot"]["rsi"]


@pytest.mark.asyncio
async def test_invalid_indicator_name(client: AsyncClient) -> None:
    response = await client.get("/api/v1/indicators/EURUSD?names=notreal")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_insufficient_count(client: AsyncClient) -> None:
    response = await client.get("/api/v1/indicators/EURUSD?names=rsi&count=10")
    assert response.status_code == 422  # validation error on count ge=30
