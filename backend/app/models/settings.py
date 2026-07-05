"""User settings, risk limits, and notification models."""

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    """Per-user application and risk settings."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Trading preferences
    default_account_id: Mapped[int | None] = mapped_column(nullable=True)
    trading_mode: Mapped[str] = mapped_column(String(10), default="demo", nullable=False)
    live_trading_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Risk management
    max_risk_per_trade: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=1.0, nullable=False)
    max_daily_loss: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=500, nullable=False)
    max_weekly_loss: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=1500, nullable=False)
    max_monthly_loss: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=5000, nullable=False)
    max_open_trades: Mapped[int] = mapped_column(default=5, nullable=False)
    max_consecutive_losses: Mapped[int] = mapped_column(default=3, nullable=False)

    # News module
    pause_trading_during_news: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    news_impact_filter: Mapped[dict] = mapped_column(JSON, default=["high"])

    # Notifications
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_trade_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_trade_close: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_risk_alert: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_daily_report: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Scanner watchlist
    watchlist_symbols: Mapped[dict] = mapped_column(JSON, default=list)

    user = relationship("User", back_populates="settings")


class Notification(Base, TimestampMixin):
    """In-app and push notifications."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    user = relationship("User", back_populates="notifications")
