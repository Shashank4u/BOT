"""Backtesting engine tests."""

import pytest
from httpx import AsyncClient

from app.trading.backtest.metrics import calculate_trade_pnl, compute_metrics
from app.trading.backtest.runner import BacktestRunner, WARMUP_BARS
from app.trading.backtest.types import BacktestTrade
from app.trading.connection import get_provider, reset_provider
from app.trading.strategies.types import StrategyConfig
from app.trading.types import OHLCBar, Timeframe


@pytest.fixture(autouse=True)
def setup_provider():
    reset_provider()
    provider = get_provider()
    provider.connect()
    yield
    reset_provider()


class TestBacktestMetrics:
    def test_calculate_trade_pnl_buy_win(self) -> None:
        pnl = calculate_trade_pnl("EURUSD", "buy", 1.1000, 1.1020, 0.1)
        assert pnl > 0

    def test_calculate_trade_pnl_sell_win(self) -> None:
        pnl = calculate_trade_pnl("EURUSD", "sell", 1.1020, 1.1000, 0.1)
        assert pnl > 0

    def test_compute_metrics_empty(self) -> None:
        metrics = compute_metrics([], [{"equity": 10000}], 10000)
        assert metrics.total_trades == 0
        assert metrics.final_balance == 10000

    def test_compute_metrics_with_trades(self) -> None:
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        trades = [
            BacktestTrade("buy", 1.1, 1.102, now, now, 0.1, 20.0, "take_profit"),
            BacktestTrade("buy", 1.1, 1.098, now, now, 0.1, -20.0, "stop_loss"),
        ]
        equity = [{"equity": 10000}, {"equity": 10020}, {"equity": 10000}]
        metrics = compute_metrics(trades, equity, 10000)
        assert metrics.total_trades == 2
        assert metrics.profit_factor == 1.0
        assert metrics.win_rate == 50.0


class TestBacktestRunner:
    def test_run_ema_cross(self) -> None:
        provider = get_provider()
        bars = provider.get_ohlc("EURUSD", Timeframe.H1, WARMUP_BARS + 200)
        config = StrategyConfig(
            name="EMA Cross",
            strategy_type="ema_cross",
            symbols=["EURUSD"],
            timeframe="H1",
            params={"fast_period": 9, "slow_period": 21},
            stop_loss_pips=20,
            take_profit_pips=40,
        )
        runner = BacktestRunner()
        result = runner.run(config, "EURUSD", bars, initial_balance=10000, bar_count=200)
        assert result.symbol == "EURUSD"
        assert result.metrics.total_trades >= 0
        assert len(result.equity_curve) >= 1
        assert "disclaimer" in result.to_dict()

    def test_insufficient_bars_raises(self) -> None:
        runner = BacktestRunner()
        bars = [
            OHLCBar(time=__import__("datetime").datetime.now(__import__("datetime").UTC), open=1, high=1, low=1, close=1, volume=1)
        ] * 50
        config = StrategyConfig(
            name="Test", strategy_type="ema_cross", symbols=["EURUSD"],
            timeframe="H1", params={},
        )
        with pytest.raises(ValueError, match="Need at least"):
            runner.run(config, "EURUSD", bars)


@pytest.mark.asyncio
async def test_backtest_run_by_type_api(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/backtest/run",
        json={
            "strategy_type": "ema_cross",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "bar_count": 200,
            "initial_balance": 10000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "EURUSD"
    assert "metrics" in data
    assert "trades" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_backtest_requires_strategy(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/backtest/run",
        json={"symbol": "EURUSD"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_backtest_with_saved_strategy(client: AsyncClient) -> None:
    await client.post("/api/v1/strategies/seed-samples")
    strategies = await client.get("/api/v1/strategies")
    strategy_id = strategies.json()[0]["id"]

    response = await client.post(
        "/api/v1/backtest/run",
        json={
            "strategy_id": strategy_id,
            "symbol": "EURUSD",
            "bar_count": 200,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] > 0
    assert data["strategy_id"] == strategy_id

    runs = await client.get("/api/v1/backtest/runs")
    assert runs.status_code == 200
    assert len(runs.json()) >= 1

    run_id = data["id"]
    detail = await client.get(f"/api/v1/backtest/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == run_id

    export = await client.get(f"/api/v1/backtest/runs/{run_id}/export")
    assert export.status_code == 200
    assert export.json()["export_format"] == "json"
