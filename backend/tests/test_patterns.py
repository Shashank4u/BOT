"""Pattern detection unit tests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.trading.patterns.candlestick import CandlestickDetector
from app.trading.patterns.detector import PatternDetector, MIN_BARS
from app.trading.patterns.registry import parse_categories, parse_pattern_names
from app.trading.types import OHLCBar


def _bar(
    i: int,
    o: float,
    h: float,
    low: float,
    c: float,
    base: datetime | None = None,
) -> OHLCBar:
    start = base or datetime(2024, 1, 1, tzinfo=UTC)
    return OHLCBar(
        time=start + timedelta(hours=i),
        open=o,
        high=h,
        low=low,
        close=c,
        volume=1000,
    )


def make_trend_bars(count: int = 100, base: float = 1.1000) -> list[OHLCBar]:
    bars = []
    price = base
    for i in range(count):
        o = price
        c = price + (0.0001 if i % 2 == 0 else -0.0001)
        bars.append(_bar(i, o, max(o, c) + 0.0002, min(o, c) - 0.0002, c))
        price = c
    return bars


def make_hammer_bars() -> list[OHLCBar]:
    bars = make_trend_bars(50)
    bars.append(_bar(50, 1.1000, 1.10015, 1.0950, 1.10015))
    return bars


def make_doji_bars() -> list[OHLCBar]:
    bars = make_trend_bars(50)
    bars.append(_bar(50, 1.1000, 1.1010, 1.0990, 1.1000))
    return bars


def make_bullish_engulfing_bars() -> list[OHLCBar]:
    bars = make_trend_bars(50)
    bars.append(_bar(50, 1.1020, 1.1025, 1.1000, 1.1005))  # bearish
    bars.append(_bar(51, 1.1000, 1.1030, 1.0995, 1.1025))  # bullish engulfing
    return bars


def make_inside_bar_bars() -> list[OHLCBar]:
    bars = make_trend_bars(50)
    bars.append(_bar(50, 1.1000, 1.1020, 1.0980, 1.1010))
    bars.append(_bar(51, 1.1005, 1.1015, 1.0990, 1.1008))  # inside previous
    return bars


@pytest.fixture
def detector() -> PatternDetector:
    return PatternDetector()


class TestCandlestickDetector:
    def test_detect_hammer(self) -> None:
        from app.trading.indicators.dataframe import bars_to_dataframe

        df = bars_to_dataframe(make_hammer_bars())
        matches = CandlestickDetector().scan(df)
        names = {m.name for m in matches}
        assert "hammer" in names

    def test_detect_doji(self) -> None:
        from app.trading.indicators.dataframe import bars_to_dataframe

        df = bars_to_dataframe(make_doji_bars())
        matches = CandlestickDetector().scan(df)
        assert any(m.name == "doji" for m in matches)

    def test_detect_bullish_engulfing(self) -> None:
        from app.trading.indicators.dataframe import bars_to_dataframe

        df = bars_to_dataframe(make_bullish_engulfing_bars())
        matches = CandlestickDetector().scan(df)
        assert any(m.name == "bullish_engulfing" for m in matches)

    def test_detect_inside_bar(self) -> None:
        from app.trading.indicators.dataframe import bars_to_dataframe

        df = bars_to_dataframe(make_inside_bar_bars())
        matches = CandlestickDetector().scan(df)
        assert any(m.name == "inside_bar" for m in matches)


class TestPatternDetector:
    def test_list_available(self, detector: PatternDetector) -> None:
        items = detector.list_available()
        names = {i["name"] for i in items}
        assert "hammer" in names
        assert "double_top" in names
        assert len(items) >= 23

    def test_scan_candlestick_only(self, detector: PatternDetector) -> None:
        bars = make_hammer_bars()
        matches = detector.scan(bars, categories=["candlestick"])
        assert all(m.category.value == "candlestick" for m in matches)

    def test_scan_chart_only(self, detector: PatternDetector) -> None:
        bars = make_trend_bars(150)
        matches = detector.scan(bars, categories=["chart"])
        assert all(m.category.value == "chart" for m in matches)

    def test_scan_filter_by_name(self, detector: PatternDetector) -> None:
        bars = make_hammer_bars()
        matches = detector.scan(bars, patterns=["hammer"])
        assert all(m.name == "hammer" for m in matches)

    def test_scan_recent(self, detector: PatternDetector) -> None:
        bars = make_hammer_bars()
        matches = detector.scan_recent(bars, recent_bars=5)
        assert all(m.bar_index >= len(bars) - 5 for m in matches)

    def test_insufficient_bars(self, detector: PatternDetector) -> None:
        with pytest.raises(ValueError, match=f"at least {MIN_BARS}"):
            detector.scan(make_trend_bars(10))

    def test_summarize(self, detector: PatternDetector) -> None:
        bars = make_hammer_bars()
        matches = detector.scan(bars)
        summary = detector.summarize(matches)
        assert summary["total"] == len(matches)
        assert "by_direction" in summary


class TestPatternRegistry:
    def test_parse_pattern_names(self) -> None:
        names = parse_pattern_names("hammer, doji, double_top")
        assert names == ["hammer", "doji", "double_top"]

    def test_parse_unknown_pattern(self) -> None:
        with pytest.raises(ValueError):
            parse_pattern_names("not_a_pattern")

    def test_parse_categories(self) -> None:
        cats = parse_categories("candlestick, chart")
        assert cats == ["candlestick", "chart"]
