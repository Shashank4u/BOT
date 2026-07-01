"""Strategy engine unit tests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.trading.strategies.engine import StrategyEngine
from app.trading.strategies.samples import SAMPLE_STRATEGIES, STRATEGY_TYPES
from app.trading.strategies.types import SignalAction, StrategyConfig
from app.trading.types import OHLCBar


def make_trend_bars(count: int = 150, trend: float = 0.0002) -> list[OHLCBar]:
    bars = []
    price = 1.1000
    start = datetime(2024, 1, 1, tzinfo=UTC)
    for i in range(count):
        o = price
        c = price + trend * (1 if i % 3 != 0 else -1)
        bars.append(
            OHLCBar(
                time=start + timedelta(hours=i),
                open=round(o, 5),
                high=round(max(o, c) + 0.0003, 5),
                low=round(min(o, c) - 0.0003, 5),
                close=round(c, 5),
                volume=1000,
            )
        )
        price = c
    return bars


@pytest.fixture
def engine() -> StrategyEngine:
    return StrategyEngine()


@pytest.fixture
def ema_config() -> StrategyConfig:
    return StrategyConfig(
        name="EMA Cross Test",
        strategy_type="ema_cross",
        symbols=["EURUSD"],
        timeframe="H1",
        params={"fast_period": 9, "slow_period": 21},
        stop_loss_pips=20,
        take_profit_pips=40,
    )


class TestStrategyEngine:
    def test_evaluate_returns_signal(self, engine: StrategyEngine, ema_config: StrategyConfig) -> None:
        bars = make_trend_bars(150)
        signal = engine.evaluate(ema_config, "EURUSD", bars)
        assert signal.symbol == "EURUSD"
        assert signal.action in SignalAction
        assert len(signal.reasons) > 0
        assert "disclaimer" in signal.to_dict()

    def test_evaluate_includes_sl_tp_on_buy_sell(
        self, engine: StrategyEngine, ema_config: StrategyConfig
    ) -> None:
        bars = make_trend_bars(150, trend=0.001)
        signal = engine.evaluate(ema_config, "EURUSD", bars)
        if signal.action in (SignalAction.BUY, SignalAction.SELL):
            assert signal.stop_loss is not None
            assert signal.take_profit is not None

    def test_unknown_strategy_type(self, engine: StrategyEngine) -> None:
        config = StrategyConfig(
            name="Bad", strategy_type="nonexistent",
            symbols=["EURUSD"], timeframe="H1", params={},
        )
        with pytest.raises(ValueError, match="Unknown strategy type"):
            engine.evaluate(config, "EURUSD", make_trend_bars(150))

    def test_all_sample_types_evaluate(self, engine: StrategyEngine) -> None:
        bars = make_trend_bars(150)
        for sample in SAMPLE_STRATEGIES:
            config = StrategyConfig(
                name=sample["name"],
                strategy_type=sample["strategy_type"],
                symbols=sample["symbols"],
                timeframe=sample["timeframes"][0],
                params=sample["entry_conditions"]["params"],
                stop_loss_pips=sample.get("stop_loss_pips"),
                take_profit_pips=sample.get("take_profit_pips"),
            )
            signal = engine.evaluate(config, "EURUSD", bars)
            assert signal.strategy_type == sample["strategy_type"]
            assert signal.action in SignalAction

    def test_breakout_detects_range(self, engine: StrategyEngine) -> None:
        config = StrategyConfig(
            name="Breakout",
            strategy_type="breakout",
            symbols=["EURUSD"],
            timeframe="H1",
            params={"lookback": 20},
        )
        bars = make_trend_bars(150, trend=0.0)
        signal = engine.evaluate(config, "EURUSD", bars)
        assert signal.strategy_type == "breakout"
        assert len(signal.reasons) > 0


class TestSampleStrategies:
    def test_eight_samples_defined(self) -> None:
        assert len(SAMPLE_STRATEGIES) == 8

    def test_all_types_in_registry(self) -> None:
        for s in SAMPLE_STRATEGIES:
            assert s["strategy_type"] in STRATEGY_TYPES
