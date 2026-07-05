"""AI assistant tests."""

import pytest
from httpx import AsyncClient

from app.ai.client import AIClient
from app.ai.prompts.system import DISCLAIMER, SYSTEM_PROMPT
from app.trading.connection import get_provider, reset_provider


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    provider = get_provider()
    provider.connect()
    yield
    reset_provider()


async def _create_trade(client: AsyncClient) -> int:
    await client.post(
        "/api/v1/orders/market",
        json={"symbol": "EURUSD", "side": "buy", "lot_size": 0.01, "stop_loss_pips": 20},
    )
    trades = await client.get("/api/v1/orders/trades?status=open")
    return trades.json()[0]["id"]


class TestAIClient:
    @pytest.mark.asyncio
    async def test_mock_mode_when_no_api_key(self) -> None:
        client = AIClient()
        assert client.is_mock is True
        response = await client.complete("Analyze this completed trade with trade data")
        assert response.is_mock is True
        assert response.model == "mock"
        assert DISCLAIMER in response.content

    @pytest.mark.asyncio
    async def test_mock_signal_explanation(self) -> None:
        client = AIClient()
        response = await client.complete("Explain this strategy signal for EURUSD")
        assert "not" in response.content.lower() or "Mock" in response.content


class TestAIPrompts:
    def test_system_prompt_has_guardrails(self) -> None:
        assert "NEVER predict" in SYSTEM_PROMPT
        assert "NEVER" in SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_analyze_trade_api(client: AsyncClient) -> None:
    trade_id = await _create_trade(client)
    response = await client.post(f"/api/v1/ai/analyze/trade/{trade_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_type"] == "trade_review"
    assert data["is_mock"] is True
    assert len(data["content"]) > 50

    journal = await client.get(f"/api/v1/journal/{trade_id}")
    assert journal.status_code == 200
    assert journal.json()["ai_review"] is not None


@pytest.mark.asyncio
async def test_explain_signal_api(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ai/explain/signal",
        json={
            "strategy_name": "EMA Cross",
            "strategy_type": "ema_cross",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "action": "buy",
            "confidence": 0.72,
            "reasons": ["EMA 9 crossed above EMA 21"],
            "indicators": {"ema_9": 1.085, "ema_21": 1.084},
            "patterns": [],
            "price": 1.0852,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_type"] == "signal_explanation"
    assert data["is_mock"] is True


@pytest.mark.asyncio
async def test_generate_daily_report(client: AsyncClient) -> None:
    await _create_trade(client)
    response = await client.post("/api/v1/ai/reports/daily")
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "daily"
    assert data["metrics"]["total_trades"] >= 1
    assert data["is_mock"] is True


@pytest.mark.asyncio
async def test_ai_chat(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "How am I doing this month?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_mock"] is True
    assert len(data["reply"]) > 20


@pytest.mark.asyncio
async def test_list_analyses(client: AsyncClient) -> None:
    trade_id = await _create_trade(client)
    await client.post(f"/api/v1/ai/analyze/trade/{trade_id}")
    response = await client.get("/api/v1/ai/analyses")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_invalid_report_type(client: AsyncClient) -> None:
    response = await client.post("/api/v1/ai/reports/yearly")
    assert response.status_code == 400
