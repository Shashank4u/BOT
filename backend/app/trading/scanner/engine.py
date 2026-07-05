"""Multi-symbol market scanner."""

from typing import Any

from app.core.logging import get_logger
from app.services.market_data import MarketDataService
from app.trading.indicators.calculator import IndicatorCalculator
from app.trading.patterns.detector import PatternDetector
from app.trading.strategies.engine import StrategyEngine
from app.trading.strategies.samples import STRATEGY_TYPES
from app.trading.strategies.types import SignalAction, StrategyConfig
from app.trading.types import Timeframe

logger = get_logger(__name__)

MIN_BARS = 120


class MarketScanner:
    """Scan multiple symbols for signals, patterns, and trend strength."""

    def __init__(self, market: MarketDataService | None = None) -> None:
        self._market = market or MarketDataService()
        self._engine = StrategyEngine()
        self._indicators = IndicatorCalculator()
        self._patterns = PatternDetector()

    def scan_symbol(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.H1,
        strategy_type: str = "ema_cross",
    ) -> dict[str, Any]:
        bars = self._market.get_ohlc(symbol, timeframe, MIN_BARS + 20)
        bars = bars[-MIN_BARS:]

        template = STRATEGY_TYPES.get(strategy_type, STRATEGY_TYPES["ema_cross"])
        config = StrategyConfig(
            name=template["name"],
            strategy_type=strategy_type,
            symbols=[symbol.upper()],
            timeframe=timeframe.value,
            params=template["entry_conditions"]["params"],
            stop_loss_pips=template.get("stop_loss_pips"),
            take_profit_pips=template.get("take_profit_pips"),
        )

        signal = self._engine.evaluate(config, symbol, bars)
        pattern_matches = self._patterns.scan_recent(bars, recent_bars=5)
        ind_data = self._indicators.compute(bars, ["rsi", "adx", "atr"])
        ind_snapshot = {
            name: data.get("latest", {})
            for name, data in ind_data.items()
        }

        score = self._score(signal, pattern_matches, ind_snapshot)
        tick = self._market.get_price(symbol)

        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe.value,
            "price": round(tick.mid, 5),
            "signal": signal.action.value,
            "confidence": round(signal.confidence, 3),
            "score": round(score, 1),
            "reasons": signal.reasons[:3],
            "patterns": [p.to_dict() for p in pattern_matches[:3]],
            "indicators": ind_snapshot,
            "strategy_type": strategy_type,
        }

    def scan_many(
        self,
        symbols: list[str],
        timeframe: Timeframe = Timeframe.H1,
        strategy_type: str = "ema_cross",
    ) -> list[dict[str, Any]]:
        results = []
        for symbol in symbols:
            try:
                results.append(self.scan_symbol(symbol, timeframe, strategy_type))
            except Exception as exc:
                logger.warning("Scanner failed for %s: %s", symbol, exc)
                results.append({
                    "symbol": symbol.upper(),
                    "timeframe": timeframe.value,
                    "error": str(exc),
                    "score": 0,
                    "signal": "hold",
                })
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return results

    def _score(self, signal, patterns, indicators) -> float:
        base = signal.confidence * 50 if signal.action != SignalAction.HOLD else 10

        if signal.action in (SignalAction.BUY, SignalAction.SELL):
            base += 25

        if patterns:
            base += min(15, sum(p.confidence for p in patterns) * 5)

        rsi = indicators.get("rsi", {}).get("value")
        if rsi is not None and 30 < rsi < 70:
            base += 5

        adx = indicators.get("adx", {}).get("adx")
        if adx and adx > 25:
            base += 10

        return min(100, base)
