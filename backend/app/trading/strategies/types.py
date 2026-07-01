"""Strategy engine types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


@dataclass
class StrategySignal:
    """Result of strategy evaluation — explains why, never predicts."""

    strategy_name: str
    strategy_type: str
    symbol: str
    timeframe: str
    action: SignalAction
    confidence: float
    reasons: list[str]
    price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    indicators: dict[str, Any] = field(default_factory=dict)
    patterns: list[dict[str, Any]] = field(default_factory=list)
    evaluated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "strategy_type": self.strategy_type,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "action": self.action.value,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "price": round(self.price, 6),
            "stop_loss": round(self.stop_loss, 6) if self.stop_loss else None,
            "take_profit": round(self.take_profit, 6) if self.take_profit else None,
            "indicators": self.indicators,
            "patterns": self.patterns,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "disclaimer": (
                "This signal is based on your strategy rules applied to historical/current data. "
                "It is not a prediction or guarantee of profit."
            ),
        }


@dataclass
class StrategyConfig:
    """Runtime strategy configuration."""

    name: str
    strategy_type: str
    symbols: list[str]
    timeframe: str
    params: dict[str, Any]
    stop_loss_pips: float | None = None
    take_profit_pips: float | None = None
    max_risk_percent: float = 1.0
    max_trades: int = 3
    magic_number: int = 100001

    @classmethod
    def from_model(cls, strategy) -> "StrategyConfig":
        entry = strategy.entry_conditions or {}
        return cls(
            name=strategy.name,
            strategy_type=entry.get("type", "ema_cross"),
            symbols=strategy.symbols if isinstance(strategy.symbols, list) else [],
            timeframe=(
                strategy.timeframes[0]
                if isinstance(strategy.timeframes, list) and strategy.timeframes
                else "H1"
            ),
            params=entry.get("params", {}),
            stop_loss_pips=strategy.stop_loss_pips,
            take_profit_pips=strategy.take_profit_pips,
            max_risk_percent=strategy.max_risk_percent,
            max_trades=strategy.max_trades,
            magic_number=strategy.magic_number,
        )
