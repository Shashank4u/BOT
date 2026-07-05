"""Trade, order, and journal models."""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TradeDirection(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class OrderType(str, enum.Enum):
    MARKET_BUY = "market_buy"
    MARKET_SELL = "market_sell"
    PENDING_BUY = "pending_buy"
    PENDING_SELL = "pending_sell"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    MODIFIED = "modified"


class Trade(Base, TimestampMixin):
    """Executed trade with full audit trail."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("trading_accounts.id", ondelete="CASCADE"), index=True
    )
    strategy_id: Mapped[int | None] = mapped_column(
        ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    mt5_ticket: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=TradeStatus.OPEN.value)
    lot_size: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    profit_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    swap: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    magic_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicators_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    account = relationship("TradingAccount", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    journal = relationship("TradeJournal", back_populates="trade", uselist=False, cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="trade", cascade="all, delete-orphan")


class Order(Base, TimestampMixin):
    """Order requests sent to MT5."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("trading_accounts.id", ondelete="CASCADE"), index=True
    )
    trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("trades.id", ondelete="SET NULL"), nullable=True
    )
    mt5_ticket: Mapped[int | None] = mapped_column(Integer, nullable=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.PENDING.value)
    lot_size: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    magic_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    account = relationship("TradingAccount", back_populates="orders")


class TradeJournal(Base, TimestampMixin):
    """Detailed trade journal entry with emotion and AI review."""

    __tablename__ = "trade_journals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trades.id", ondelete="CASCADE"), unique=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trade = relationship("Trade", back_populates="journal")
