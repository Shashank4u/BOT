"""Broker account API tests."""

import pytest
from httpx import AsyncClient

from app.trading.connection import reset_provider


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    yield
    reset_provider()


@pytest.mark.asyncio
async def test_list_accounts_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/accounts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_add_broker_account_mock(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/accounts",
        json={
            "name": "My XM Demo",
            "broker": "XM",
            "account_type": "demo",
            "mt5_login": 87654321,
            "mt5_password": "demo-password",
            "mt5_server": "XMGlobal-MT5",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["account"]["mt5_login"] == 87654321
    assert data["account"]["is_active"] is True
    assert data["account"]["is_connected"] is True
    assert data["connection"]["connected"] is True


@pytest.mark.asyncio
async def test_list_and_reconnect_account(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/accounts",
        json={
            "name": "Demo",
            "account_type": "demo",
            "mt5_login": 11111111,
            "mt5_password": "secret",
            "mt5_server": "XMGlobal-MT5",
        },
    )
    account_id = create.json()["account"]["id"]

    await client.post("/api/v1/accounts/disconnect")
    reconnect = await client.post(f"/api/v1/accounts/{account_id}/connect")
    assert reconnect.status_code == 200
    assert reconnect.json()["connection"]["connected"] is True

    active = await client.get("/api/v1/accounts/active")
    assert active.status_code == 200
    assert active.json()["id"] == account_id


@pytest.mark.asyncio
async def test_delete_broker_account(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/accounts",
        json={
            "mt5_login": 22222222,
            "mt5_password": "secret",
            "mt5_server": "XMGlobal-MT5",
        },
    )
    account_id = create.json()["account"]["id"]

    delete = await client.delete(f"/api/v1/accounts/{account_id}")
    assert delete.status_code == 204

    listing = await client.get("/api/v1/accounts")
    assert listing.json() == []
