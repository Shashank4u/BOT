"""Risk and order API schemas."""

from pydantic import Field

from app.schemas.common import BaseSchema


class LotSizeRequest(BaseSchema):
    balance: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=10)
    stop_loss_pips: float = Field(gt=0)
    symbol: str


class LotSizeResponse(BaseSchema):
    lot_size: float
    risk_amount: float
    risk_percent: float
    stop_loss_pips: float
    pip_value: float
    symbol: str


class RiskRewardRequest(BaseSchema):
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    symbol: str
    side: str = "buy"


class RiskRewardResponse(BaseSchema):
    risk_pips: float
    reward_pips: float
    risk_reward_ratio: float
    entry_price: float
    stop_loss: float
    take_profit: float


class MarginRequest(BaseSchema):
    lot_size: float = Field(gt=0)
    symbol: str
    price: float = Field(gt=0)
    leverage: int = Field(default=100, ge=1)
    free_margin: float = Field(ge=0)


class MarginResponse(BaseSchema):
    required_margin: float
    free_margin: float
    margin_level_after: float
    lot_size: float
    leverage: int
    symbol: str


class RiskCheckRequest(BaseSchema):
    symbol: str
    lot_size: float = Field(gt=0)
    stop_loss_pips: float = Field(gt=0)
    balance: float = Field(gt=0)


class RiskCheckResponse(BaseSchema):
    allowed: bool
    violations: list[str]
    warnings: list[str]
    lot_size: float | None = None
    risk_amount: float | None = None


class RiskSettingsUpdate(BaseSchema):
    max_risk_per_trade: float | None = Field(default=None, ge=0.1, le=10)
    max_daily_loss: float | None = Field(default=None, gt=0)
    max_weekly_loss: float | None = Field(default=None, gt=0)
    max_monthly_loss: float | None = Field(default=None, gt=0)
    max_open_trades: int | None = Field(default=None, ge=1, le=50)
    max_consecutive_losses: int | None = Field(default=None, ge=1, le=20)


class RiskSettingsResponse(BaseSchema):
    max_risk_per_trade: float
    max_daily_loss: float
    max_weekly_loss: float
    max_monthly_loss: float
    max_open_trades: int
    max_consecutive_losses: int
    live_trading_confirmed: bool
    trading_mode: str


class ConfirmLiveResponse(BaseSchema):
    live_trading_confirmed: bool
    message: str
    warning: str
