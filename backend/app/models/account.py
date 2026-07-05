"""Trading account and broker connection models."""

import enum
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AccountType(str, enum.Enum):
    DEMO = "demo"
    LIVE = "live"


class TradingAccount(Base, TimestampMixin):
    """MT5/XM broker account linked to a user."""

    __tablename__ = "trading_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    broker: Mapped[str] = mapped_column(String(50), default="XM", nullable=False)
    account_type: Mapped[str] = mapped_column(String(10), default=AccountType.DEMO.value)
    mt5_login: Mapped[int] = mapped_column(nullable=False)
    mt5_server: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    leverage: Mapped[int] = mapped_column(default=100, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    margin: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    free_margin: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="accounts")
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="account", cascade="all, delete-orphan")
