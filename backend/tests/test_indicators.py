"""Indicator calculator unit tests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.trading.indicators.calculator import IndicatorCalculator, MIN_BARS
from app.trading.indicators.registry import parse_indicator_names
from app.trading.types import OHLCBar


def make_bars(count: int = 200, base: float = 1.1000) -> list[OHLCBar]:
    """Generate synthetic OHLC bars with a slight upward drift."""
    bars: list[OHLCBar] = []
    price = base
    start = datetime(2024, 1, 1, tzinfo=UTC)
    for i in range(count):
        change = (i % 7 - 3) * 0.0005
        o = price
        c = price + change
        h = max(o, c) + 0.0003
        low = min(o, c) - 0.0003
        bars.append(
            OHLCBar(
                time=start + timedelta(hours=i),
                open=round(o, 5),
                high=round(h, 5),
                low=round(low, 5),
                close=round(c, 5),
                volume=1000 + i * 10,
            )
        )
        price = c
    return bars


@pytest.fixture
def calculator() -> IndicatorCalculator:
    return IndicatorCalculator()


@pytest.fixture
def bars() -> list[OHLCBar]:
    return make_bars(200)


class TestIndicatorCalculator:
    def test_list_available(self, calculator: IndicatorCalculator) -> None:
        items = calculator.list_available()
        names = {i["name"] for i in items}
        assert "rsi" in names
        assert "ema" in names
        assert "supertrend" in names
        assert len(items) >= 15

    def test_compute_rsi(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["rsi"])
        rsi = result["rsi"]
        assert "latest" in rsi
        assert 0 <= rsi["latest"]["value"] <= 100

    def test_compute_ema(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["ema"], {"ema": {"period": 20}})
        assert result["ema"]["latest"]["value"] > 0

    def test_compute_macd(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["macd"])
        latest = result["macd"]["latest"]
        assert "macd" in latest
        assert "signal" in latest
        assert "histogram" in latest

    def test_compute_bbands(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["bbands"])
        latest = result["bbands"]["latest"]
        assert latest["upper"] >= latest["middle"] >= latest["lower"]

    def test_compute_atr(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["atr"])
        assert result["atr"]["latest"]["value"] > 0

    def test_compute_adx(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["adx"])
        assert result["adx"]["latest"]["adx"] >= 0

    def test_compute_ichimoku(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["ichimoku"])
        latest = result["ichimoku"]["latest"]
        assert "tenkan" in latest
        assert "kijun" in latest

    def test_compute_stoch(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["stoch"])
        latest = result["stoch"]["latest"]
        assert 0 <= latest["k"] <= 100

    def test_compute_psar(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["psar"])
        assert result["psar"]["latest"]["value"] > 0

    def test_compute_pivots(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["pivots"])
        latest = result["pivots"]["latest"]
        assert latest["r1"] > latest["pivot"] > latest["s1"]

    def test_compute_supertrend(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["supertrend"])
        latest = result["supertrend"]["latest"]
        assert latest["direction"] in (1.0, -1.0)
        assert latest["value"] > 0

    def test_compute_vwap(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["vwap"])
        assert result["vwap"]["latest"]["value"] > 0

    def test_compute_volume_profile(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["volume_profile"])
        latest = result["volume_profile"]["latest"]
        assert "poc" in latest
        assert len(latest["levels"]) > 0

    def test_compute_multiple(self, calculator: IndicatorCalculator, bars: list[OHLCBar]) -> None:
        result = calculator.compute(bars, ["rsi", "ema", "macd"])
        assert set(result.keys()) == {"rsi", "ema", "macd"}

    def test_insufficient_bars(self, calculator: IndicatorCalculator) -> None:
        with pytest.raises(ValueError, match=f"at least {MIN_BARS}"):
            calculator.compute(make_bars(10), ["rsi"])

    def test_empty_bars(self, calculator: IndicatorCalculator) -> None:
        with pytest.raises(ValueError):
            calculator.compute([], ["rsi"])


class TestIndicatorRegistry:
    def test_parse_valid_names(self) -> None:
        names = parse_indicator_names("rsi, ema, macd")
        assert names == ["rsi", "ema", "macd"]

    def test_parse_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown"):
            parse_indicator_names("rsi,invalid")
