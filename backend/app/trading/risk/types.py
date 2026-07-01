"""Risk management types."""

from dataclasses import dataclass, field


@dataclass
class PositionSizeResult:
    lot_size: float
    risk_amount: float
    risk_percent: float
    stop_loss_pips: float
    pip_value: float
    symbol: str


@dataclass
class RiskRewardResult:
    risk_pips: float
    reward_pips: float
    risk_reward_ratio: float
    entry_price: float
    stop_loss: float
    take_profit: float


@dataclass
class MarginResult:
    required_margin: float
    free_margin: float
    margin_level_after: float
    lot_size: float
    leverage: int
    symbol: str


@dataclass
class RiskCheckResult:
    allowed: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    lot_size: float | None = None
    risk_amount: float | None = None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "violations": self.violations,
            "warnings": self.warnings,
            "lot_size": self.lot_size,
            "risk_amount": self.risk_amount,
        }
