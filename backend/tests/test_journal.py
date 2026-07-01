"""Trade journal API tests."""

import pytest
from httpx import AsyncClient

from app.trading.connection import get_provider, reset_provider


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    provider = get_provider()
    provider.connect()
    yield
    reset_provider()


async def _create_trade(client: AsyncClient) -> int:
    response = await client.post(
        "/api/v1/orders/market",
        json={
            "symbol": "EURUSD",
            "side": "buy",
            "lot_size": 0.01,
            "stop_loss_pips": 20,
            "entry_reason": "Journal test",
        },
    )
    assert response.status_code == 200
    trades = await client.get("/api/v1/orders/trades?status=open")
    return trades.json()[0]["id"]


@pytest.mark.asyncio
async def test_upsert_journal_entry(client: AsyncClient) -> None:
    trade_id = await _create_trade(client)
    response = await client.put(
        f"/api/v1/journal/{trade_id}",
        json={
            "notes": "Felt confident but rushed entry",
            "emotion": "anxious",
            "lessons_learned": "Wait for confirmation candle",
            "tags": ["scalping", "eurusd"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trade_id"] == trade_id
    assert data["notes"] == "Felt confident but rushed entry"
    assert data["emotion"] == "anxious"
    assert data["trade"]["symbol"] == "EURUSD"


@pytest.mark.asyncio
async def test_get_journal_entry(client: AsyncClient) -> None:
    trade_id = await _create_trade(client)
    await client.put(
        f"/api/v1/journal/{trade_id}",
        json={"notes": "Test note"},
    )
    response = await client.get(f"/api/v1/journal/{trade_id}")
    assert response.status_code == 200
    assert response.json()["notes"] == "Test note"


@pytest.mark.asyncio
async def test_list_journal_entries(client: AsyncClient) -> None:
    trade_id = await _create_trade(client)
    await client.put(f"/api/v1/journal/{trade_id}", json={"notes": "Listed"})
    response = await client.get("/api/v1/journal")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_journal_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/journal/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_journal_entry(client: AsyncClient) -> None:
    trade_id = await _create_trade(client)
    await client.put(f"/api/v1/journal/{trade_id}", json={"notes": "To delete"})
    response = await client.delete(f"/api/v1/journal/{trade_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/api/v1/journal/{trade_id}")
    assert get_resp.status_code == 404
