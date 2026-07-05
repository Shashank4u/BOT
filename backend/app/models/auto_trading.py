"""Auto-trading configuration — single-row persisted state."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AutoTradingConfig(Base, TimestampMixin):
    """Global auto-trading switch and scan interval (one row per app)."""

    __tablename__ = "auto_trading_config"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    min_confidence: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    orders_placed_last_scan: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
