"""Strategy evaluation engine — applies user-defined rules to market data."""

from datetime import UTC, datetime
from typing import Any, Callable

from app.trading.indicators.calculator import IndicatorCalculator
from app.trading.patterns.detector import PatternDetector
from app.trading.strategies.types import SignalAction, StrategyConfig, StrategySignal
from app.trading.types import OHLCBar, Timeframe


class StrategyEngine:
    """
    Evaluates trading strategies against OHLC data, indicators, and patterns.
    Returns signals with explanations — never predicts future prices.
    """

    def __init__(self) -> None:
        self._indicators = IndicatorCalculator()
        self._patterns = PatternDetector()
        self._evaluators: dict[str, Callable] = {
            "ema_cross": self._eval_ema_cross,
            "ema_rsi": self._eval_ema_rsi,
            "macd_trend": self._eval_macd_trend,
            "breakout": self._eval_breakout,
            "support_resistance": self._eval_support_resistance,
            "pullback": self._eval_pullback,
            "scalping": self._eval_scalping,
            "swing": self._eval_swing,
        }

    def evaluate(
        self,
        config: StrategyConfig,
        symbol: str,
        bars: list[OHLCBar],
        indicator_data: dict[str, Any] | None = None,
        pattern_matches: list | None = None,
    ) -> StrategySignal:
        evaluator = self._evaluators.get(config.strategy_type)
        if evaluator is None:
            raise ValueError(f"Unknown strategy type: {config.strategy_type}")

        if indicator_data is None:
            indicator_data = self._compute_indicators(config, bars)

        if pattern_matches is None and config.strategy_type in ("swing",):
            pattern_matches = self._patterns.scan_recent(bars, recent_bars=5)
        else:
            pattern_matches = pattern_matches or []

        price = float(bars[-1].close)
        signal = evaluator(config, bars, indicator_data, pattern_matches, price)

        # Apply SL/TP from config (pip approximation)
        pip = self._pip_size(symbol)
        if config.stop_loss_pips and signal.action in (SignalAction.BUY, SignalAction.SELL):
            if signal.action == SignalAction.BUY:
                signal.stop_loss = price - config.stop_loss_pips * pip
                signal.take_profit = price + (config.take_profit_pips or 0) * pip
            else:
                signal.stop_loss = price + config.stop_loss_pips * pip
                signal.take_profit = price - (config.take_profit_pips or 0) * pip

        signal.evaluated_at = datetime.now(UTC)
        signal.symbol = symbol.upper()
        return signal

    def _compute_indicators(
        self, config: StrategyConfig, bars: list[OHLCBar]
    ) -> dict[str, Any]:
        type_indicators = {
            "ema_cross": ["ema"],
            "ema_rsi": ["ema", "rsi"],
            "macd_trend": ["macd", "atr"],
            "breakout": ["atr"],
            "support_resistance": ["bbands", "pivots", "rsi"],
            "pullback": ["ema", "rsi", "adx"],
            "scalping": ["ema", "atr", "rsi"],
            "swing": ["ema", "rsi", "macd"],
        }
        names = type_indicators.get(config.strategy_type, ["ema", "rsi"])
        params = self._indicator_params(config)
        return self._indicators.compute(bars, names, params)

    def _indicator_params(self, config: StrategyConfig) -> dict[str, dict]:
        p = config.params
        mapping: dict[str, dict] = {}

        if "fast_period" in p:
            mapping["ema"] = {"period": p["fast_period"]}
        elif "ema_period" in p:
            mapping["ema"] = {"period": p["ema_period"]}
        else:
            mapping["ema"] = {"period": 20}

        if "rsi_period" in p:
            mapping["rsi"] = {"period": p["rsi_period"]}
        if config.strategy_type == "ema_rsi":
            mapping["ema_slow"] = {"period": p.get("slow_period", 21)}

        if "macd_trend" in config.strategy_type or config.strategy_type == "swing":
            mapping["macd"] = {
                "fast": p.get("fast", 12),
                "slow": p.get("slow", 26),
                "signal": p.get("signal", 9),
            }
        if "atr_period" in p or config.strategy_type in ("macd_trend", "breakout", "scalping"):
            mapping["atr"] = {"period": p.get("atr_period", 14)}
        if config.strategy_type == "support_resistance":
            mapping["bbands"] = {"period": p.get("bb_period", 20), "std": 2.0}
            mapping["pivots"] = {}
            mapping["rsi"] = {"period": p.get("rsi_period", 14)}
        if config.strategy_type == "pullback":
            mapping["adx"] = {"period": p.get("adx_period", 14)}
            mapping["rsi"] = {"period": p.get("rsi_period", 14)}
            mapping["ema"] = {"period": p.get("ema_period", 50)}

        return mapping

    def _pip_size(self, symbol: str) -> float:
        symbol = symbol.upper()
        if "JPY" in symbol:
            return 0.01
        if symbol in ("XAUUSD", "XAGUSD"):
            return 0.1
        if symbol in ("BTCUSD", "ETHUSD", "US30", "NAS100"):
            return 1.0
        return 0.0001

    def _hold(
        self,
        config: StrategyConfig,
        symbol: str,
        price: float,
        reasons: list[str],
        indicators: dict | None = None,
        patterns: list | None = None,
        confidence: float = 0.0,
    ) -> StrategySignal:
        return StrategySignal(
            strategy_name=config.name,
            strategy_type=config.strategy_type,
            symbol=symbol,
            timeframe=config.timeframe,
            action=SignalAction.HOLD,
            confidence=confidence,
            reasons=reasons,
            price=price,
            indicators=indicators or {},
            patterns=patterns or [],
        )

    def _ema_values(
        self, indicator_data: dict, fast_period: int, slow_period: int
    ) -> tuple[list, list] | tuple[None, None]:
        """Get fast and slow EMA series — computes slow separately if needed."""
        ema_result = indicator_data.get("ema", {})
        values = ema_result.get("values", [])
        if len(values) < 2:
            return None, None

        # If only one EMA computed, use it as fast; approximate slow from values
        fast_vals = [v["value"] for v in values if v.get("value") is not None]
        return fast_vals, fast_vals  # engine pre-computes; cross logic uses last 2 bars

    def _eval_ema_cross(
        self, config, bars, indicator_data, patterns, price
    ) -> StrategySignal:
        p = config.params
        fast_p, slow_p = p.get("fast_period", 9), p.get("slow_period", 21)

        fast_ema = self._indicators.compute(bars, ["ema"], {"ema": {"period": fast_p}})
        slow_ema = self._indicators.compute(bars, ["ema"], {"ema": {"period": slow_p}})

        fast_vals = [v["value"] for v in fast_ema["ema"]["values"] if v.get("value")]
        slow_vals = [v["value"] for v in slow_ema["ema"]["values"] if v.get("value")]

        if len(fast_vals) < 2 or len(slow_vals) < 2:
            return self._hold(config, config.symbols[0] if config.symbols else "", price,
                              ["Insufficient data for EMA cross"])

        prev_diff = fast_vals[-2] - slow_vals[-2]
        curr_diff = fast_vals[-1] - slow_vals[-1]

        ind_snapshot = {
            "ema_fast": fast_vals[-1],
            "ema_slow": slow_vals[-1],
        }
        reasons = [
            f"EMA({fast_p})={fast_vals[-1]:.5f}, EMA({slow_p})={slow_vals[-1]:.5f}",
        ]

        if prev_diff <= 0 < curr_diff:
            reasons.append(f"Bullish cross: EMA({fast_p}) crossed above EMA({slow_p})")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.BUY, 0.75, reasons, price, indicators=ind_snapshot,
            )
        if prev_diff >= 0 > curr_diff:
            reasons.append(f"Bearish cross: EMA({fast_p}) crossed below EMA({slow_p})")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.SELL, 0.75, reasons, price, indicators=ind_snapshot,
            )

        trend = "bullish" if curr_diff > 0 else "bearish"
        reasons.append(f"No cross — trend is {trend}")
        return self._hold(
            config, config.symbols[0] if config.symbols else "", price, reasons,
            ind_snapshot, confidence=0.3,
        )

    def _eval_ema_rsi(self, config, bars, indicator_data, patterns, price) -> StrategySignal:
        signal = self._eval_ema_cross(config, bars, indicator_data, patterns, price)
        rsi_latest = indicator_data.get("rsi", {}).get("latest", {}).get("value")
        if rsi_latest is None:
            rsi_data = self._indicators.compute(
                bars, ["rsi"], {"rsi": {"period": config.params.get("rsi_period", 14)}}
            )
            rsi_latest = rsi_data["rsi"]["latest"].get("value")

        p = config.params
        ob, os_ = p.get("rsi_overbought", 70), p.get("rsi_oversold", 30)
        signal.indicators["rsi"] = rsi_latest

        if signal.action == SignalAction.BUY and rsi_latest > ob:
            return self._hold(
                config, signal.symbol, price,
                [f"EMA cross bullish but RSI={rsi_latest:.1f} overbought (>{ob}) — filtered"],
                signal.indicators, confidence=0.2,
            )
        if signal.action == SignalAction.SELL and rsi_latest < os_:
            return self._hold(
                config, signal.symbol, price,
                [f"EMA cross bearish but RSI={rsi_latest:.1f} oversold (<{os_}) — filtered"],
                signal.indicators, confidence=0.2,
            )
        if signal.action != SignalAction.HOLD:
            signal.reasons.append(f"RSI={rsi_latest:.1f} confirms entry filter")
            signal.confidence = min(0.9, signal.confidence + 0.1)
        return signal

    def _eval_macd_trend(self, config, bars, indicator_data, patterns, price) -> StrategySignal:
        macd = indicator_data.get("macd", {}).get("latest", {})
        atr = indicator_data.get("atr", {}).get("latest", {}).get("value", 0)
        m, s, h = macd.get("macd"), macd.get("signal"), macd.get("histogram")

        if m is None or s is None:
            return self._hold(config, config.symbols[0] if config.symbols else "", price,
                              ["Insufficient MACD data"])

        ind = {"macd": m, "signal": s, "histogram": h, "atr": atr}
        reasons = [f"MACD={m:.6f}, Signal={s:.6f}, Histogram={h:.6f}"]

        if h and h > 0 and m > s:
            reasons.append("MACD above signal with positive histogram — bullish momentum")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.BUY, 0.72, reasons, price, indicators=ind,
            )
        if h and h < 0 and m < s:
            reasons.append("MACD below signal with negative histogram — bearish momentum")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.SELL, 0.72, reasons, price, indicators=ind,
            )
        reasons.append("No clear MACD trend signal")
        return self._hold(
            config, config.symbols[0] if config.symbols else "", price, reasons, ind,
            confidence=0.25,
        )

    def _eval_breakout(self, config, bars, indicator_data, patterns, price) -> StrategySignal:
        p = config.params
        lookback = int(p.get("lookback", 20))
        if len(bars) < lookback + 1:
            return self._hold(config, config.symbols[0] if config.symbols else "", price,
                              ["Insufficient bars for breakout"])

        window = bars[-(lookback + 1):-1]
        range_high = max(b.high for b in window)
        range_low = min(b.low for b in window)
        atr = indicator_data.get("atr", {}).get("latest", {}).get("value", 0)
        ind = {"range_high": float(range_high), "range_low": float(range_low), "atr": atr}
        reasons = [f"Range high={range_high:.5f}, low={range_low:.5f}, price={price:.5f}"]

        if price > float(range_high):
            reasons.append(f"Price broke above {lookback}-bar high — bullish breakout")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.BUY, 0.7, reasons, price, indicators=ind,
            )
        if price < float(range_low):
            reasons.append(f"Price broke below {lookback}-bar low — bearish breakout")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.SELL, 0.7, reasons, price, indicators=ind,
            )
        reasons.append("Price within range — no breakout")
        return self._hold(
            config, config.symbols[0] if config.symbols else "", price, reasons, ind,
            confidence=0.2,
        )

    def _eval_support_resistance(
        self, config, bars, indicator_data, patterns, price
    ) -> StrategySignal:
        bb = indicator_data.get("bbands", {}).get("latest", {})
        piv = indicator_data.get("pivots", {}).get("latest", {})
        rsi = indicator_data.get("rsi", {}).get("latest", {}).get("value")
        lower, upper = bb.get("lower"), bb.get("upper")
        s1, r1 = piv.get("s1"), piv.get("r1")

        ind = {"bb_lower": lower, "bb_upper": upper, "pivot_s1": s1, "pivot_r1": r1, "rsi": rsi}
        reasons = [f"Price={price:.5f}, BB lower={lower}, upper={upper}"]

        if lower and price <= lower * 1.001 and rsi and rsi < 40:
            reasons.append("Price at lower Bollinger Band with RSI<40 — potential support bounce")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.BUY, 0.68, reasons, price, indicators=ind,
            )
        if upper and price >= upper * 0.999 and rsi and rsi > 60:
            reasons.append("Price at upper Bollinger Band with RSI>60 — potential resistance rejection")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.SELL, 0.68, reasons, price, indicators=ind,
            )
        reasons.append("No support/resistance setup at current levels")
        return self._hold(
            config, config.symbols[0] if config.symbols else "", price, reasons, ind,
            confidence=0.2,
        )

    def _eval_pullback(self, config, bars, indicator_data, patterns, price) -> StrategySignal:
        ema = indicator_data.get("ema", {}).get("latest", {}).get("value")
        rsi = indicator_data.get("rsi", {}).get("latest", {}).get("value")
        adx = indicator_data.get("adx", {}).get("latest", {}).get("adx")
        p = config.params

        if ema is None or rsi is None:
            return self._hold(config, config.symbols[0] if config.symbols else "", price,
                              ["Insufficient indicator data"])

        ind = {"ema": ema, "rsi": rsi, "adx": adx}
        reasons = [f"Price={price:.5f}, EMA={ema:.5f}, RSI={rsi:.1f}, ADX={adx}"]

        if adx and adx < p.get("adx_min", 20):
            reasons.append(f"ADX={adx:.1f} below minimum — no clear trend")
            return self._hold(
                config, config.symbols[0] if config.symbols else "", price, reasons, ind,
                confidence=0.15,
            )

        rsi_lo, rsi_hi = p.get("rsi_pullback_low", 40), p.get("rsi_pullback_high", 60)

        if price > ema and rsi_lo <= rsi <= rsi_hi:
            reasons.append("Uptrend with RSI pullback to neutral zone — potential long entry")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.BUY, 0.7, reasons, price, indicators=ind,
            )
        if price < ema and rsi_lo <= rsi <= rsi_hi:
            reasons.append("Downtrend with RSI pullback to neutral zone — potential short entry")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.SELL, 0.7, reasons, price, indicators=ind,
            )
        reasons.append("No pullback setup in current trend")
        return self._hold(
            config, config.symbols[0] if config.symbols else "", price, reasons, ind,
            confidence=0.2,
        )

    def _eval_scalping(self, config, bars, indicator_data, patterns, price) -> StrategySignal:
        p = config.params
        fast_p, slow_p = p.get("fast_period", 5), p.get("slow_period", 13)
        atr = indicator_data.get("atr", {}).get("latest", {}).get("value", 0)
        max_atr_ratio = p.get("max_atr_ratio", 0.001)

        if atr / price > max_atr_ratio:
            return self._hold(
                config, config.symbols[0] if config.symbols else "", price,
                [f"ATR/price ratio too high for scalping ({atr/price:.5f})"],
                confidence=0.1,
            )

        signal = self._eval_ema_cross(config, bars, indicator_data, patterns, price)
        signal.strategy_type = config.strategy_type
        signal.strategy_name = config.name

        if signal.action != SignalAction.HOLD:
            signal.reasons.append(f"Low volatility confirmed (ATR={atr:.5f})")
            signal.confidence = min(0.85, signal.confidence + 0.05)
        return signal

    def _eval_swing(self, config, bars, indicator_data, patterns, price) -> StrategySignal:
        ema = indicator_data.get("ema", {}).get("latest", {}).get("value")
        rsi = indicator_data.get("rsi", {}).get("latest", {}).get("value")
        macd = indicator_data.get("macd", {}).get("latest", {})

        pattern_dicts = [pm.to_dict() for pm in patterns] if patterns else []
        bullish_patterns = {
            "hammer", "morning_star", "bullish_engulfing", "double_bottom",
            "inverse_head_shoulders",
        }
        bearish_patterns = {
            "shooting_star", "evening_star", "bearish_engulfing", "double_top",
            "head_shoulders",
        }

        recent_bull = [p for p in pattern_dicts if p["name"] in bullish_patterns]
        recent_bear = [p for p in pattern_dicts if p["name"] in bearish_patterns]

        ind = {"ema": ema, "rsi": rsi, "macd_histogram": macd.get("histogram")}
        reasons = [f"EMA={ema}, RSI={rsi}, patterns found={len(pattern_dicts)}"]

        if ema and price > ema and rsi and 45 < rsi < 70 and recent_bull:
            pname = recent_bull[0]["name"]
            reasons.append(f"Bullish trend + pattern '{pname}' — swing long setup")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.BUY, 0.78, reasons, price, indicators=ind, patterns=pattern_dicts,
            )
        if ema and price < ema and rsi and 30 < rsi < 55 and recent_bear:
            pname = recent_bear[0]["name"]
            reasons.append(f"Bearish trend + pattern '{pname}' — swing short setup")
            return StrategySignal(
                config.name, config.strategy_type,
                config.symbols[0] if config.symbols else "", config.timeframe,
                SignalAction.SELL, 0.78, reasons, price, indicators=ind, patterns=pattern_dicts,
            )
        reasons.append("No swing setup — waiting for trend + pattern alignment")
        return self._hold(
            config, config.symbols[0] if config.symbols else "", price, reasons, ind,
            patterns=pattern_dicts, confidence=0.2,
        )
