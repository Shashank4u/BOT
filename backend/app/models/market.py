"""Backtesting and market scanner models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BacktestRun(Base, TimestampMixin):
    """Backtest execution results for a strategy."""

    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    final_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    profit_factor: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    expectancy: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    average_win: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    average_loss: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    strategy = relationship("Strategy", back_populates="backtest_runs")


class MarketScan(Base, TimestampMixin):
    """Market scanner results snapshot."""

    __tablename__ = "market_scans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    symbols: Mapped[dict] = mapped_column(JSON, nullable=False)
    results: Mapped[dict] = mapped_column(JSON, nullable=False)
    scan_type: Mapped[str] = mapped_column(String(50), default="full", nullable=False)


class EconomicEvent(Base, TimestampMixin):
    """Cached economic calendar events."""

    __tablename__ = "economic_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    country: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    impact: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    forecast: Mapped[str | None] = mapped_column(String(50), nullable=True)
    previous: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actual: Mapped[str | None] = mapped_column(String(50), nullable=True)
