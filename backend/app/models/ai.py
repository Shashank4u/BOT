"""AI analysis, reports, and prompt models."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AnalysisType(str, enum.Enum):
    TRADE_REVIEW = "trade_review"
    DAILY_REPORT = "daily_report"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"
    RISK_REVIEW = "risk_review"
    JOURNAL_ANALYSIS = "journal_analysis"
    SIGNAL_EXPLANATION = "signal_explanation"
    MARKET_SUMMARY = "market_summary"


class AIAnalysis(Base, TimestampMixin):
    """AI-generated analysis for trades or time periods."""

    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    trade_id: Mapped[int | None] = mapped_column(
        ForeignKey("trades.id", ondelete="CASCADE"), nullable=True, index=True
    )
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    prompt_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(nullable=True)

    trade = relationship("Trade", back_populates="ai_analyses")


class Report(Base, TimestampMixin):
    """Scheduled AI reports (daily, weekly, monthly)."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sent_via_telegram: Mapped[bool] = mapped_column(default=False, nullable=False)
