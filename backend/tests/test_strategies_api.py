"""Strategy API integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_sample_templates(client: AsyncClient) -> None:
    response = await client.get("/api/v1/strategies/samples")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 8
    types = {s["strategy_type"] for s in data}
    assert "ema_cross" in types
    assert "swing" in types


@pytest.mark.asyncio
async def test_seed_samples(client: AsyncClient) -> None:
    response = await client.post("/api/v1/strategies/seed-samples")
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 8
    assert data["skipped"] == 0


@pytest.mark.asyncio
async def test_seed_samples_idempotent(client: AsyncClient) -> None:
    await client.post("/api/v1/strategies/seed-samples")
    response = await client.post("/api/v1/strategies/seed-samples")
    data = response.json()
    assert data["created"] == 0
    assert data["skipped"] == 8


@pytest.mark.asyncio
async def test_list_strategies_after_seed(client: AsyncClient) -> None:
    await client.post("/api/v1/strategies/seed-samples")
    response = await client.get("/api/v1/strategies")
    assert response.status_code == 200
    assert len(response.json()) == 8


@pytest.mark.asyncio
async def test_evaluate_by_type(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/strategies/evaluate/EURUSD?strategy_type=ema_cross&timeframe=H1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert data["action"] in ("buy", "sell", "hold", "close_long", "close_short")
    assert len(data["reasons"]) > 0
    assert "not a prediction" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_evaluate_saved_strategy(client: AsyncClient) -> None:
    await client.post("/api/v1/strategies/seed-samples")
    strategies = (await client.get("/api/v1/strategies")).json()
    strategy_id = strategies[0]["id"]

    response = await client.post(
        f"/api/v1/strategies/{strategy_id}/evaluate",
        json={"symbol": "EURUSD", "timeframe": "H1"},
    )
    assert response.status_code == 200
    assert response.json()["strategy_name"] == strategies[0]["name"]


@pytest.mark.asyncio
async def test_create_custom_strategy(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/strategies",
        json={
            "name": "My Custom EMA",
            "strategy_type": "ema_cross",
            "symbols": ["EURUSD"],
            "params": {"fast_period": 8, "slow_period": 21},
            "stop_loss_pips": 15,
            "take_profit_pips": 30,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Custom EMA"
    assert data["strategy_type"] == "ema_cross"


@pytest.mark.asyncio
async def test_invalid_strategy_type(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/strategies/evaluate/EURUSD?strategy_type=invalid"
    )
    assert response.status_code == 400
