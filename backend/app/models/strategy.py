"""Strategy definition and configuration models."""

import enum

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class StrategyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Strategy(Base, TimestampMixin):
    """
    User-defined trading strategy with indicators, entry/exit rules,
    and risk parameters stored as JSON configuration.
    """

    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=StrategyStatus.DRAFT.value)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Strategy configuration (JSON)
    symbols: Mapped[dict] = mapped_column(JSON, default=list)
    timeframes: Mapped[dict] = mapped_column(JSON, default=list)
    indicators: Mapped[dict] = mapped_column(JSON, default=list)
    entry_conditions: Mapped[dict] = mapped_column(JSON, default=list)
    exit_conditions: Mapped[dict] = mapped_column(JSON, default=list)

    # Risk parameters
    stop_loss_pips: Mapped[float | None] = mapped_column(nullable=True)
    take_profit_pips: Mapped[float | None] = mapped_column(nullable=True)
    trailing_stop_pips: Mapped[float | None] = mapped_column(nullable=True)
    break_even_pips: Mapped[float | None] = mapped_column(nullable=True)
    max_risk_percent: Mapped[float] = mapped_column(default=1.0, nullable=False)
    max_trades: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    trading_sessions: Mapped[dict] = mapped_column(JSON, default=list)
    magic_number: Mapped[int] = mapped_column(Integer, default=100001, nullable=False)

    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")
    backtest_runs = relationship("BacktestRun", back_populates="strategy", cascade="all, delete-orphan")
