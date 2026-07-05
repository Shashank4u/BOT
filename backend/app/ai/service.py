"""AI analysis and reporting service."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import AIClient
from app.ai.prompts.templates import (
    chat_prompt,
    journal_analysis_prompt,
    period_report_prompt,
    signal_explanation_prompt,
    trade_review_prompt,
)
from app.core.logging import get_logger
from app.models.ai import AIAnalysis, AnalysisType, Report
from app.models.trade import Trade, TradeJournal, TradeStatus
from app.models.user import User
from app.repositories.trade_repository import TradeRepository

logger = get_logger(__name__)


class AIService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._client = AIClient()
        self._trades = TradeRepository(session)

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    def _trade_dict(self, trade: Trade) -> dict[str, Any]:
        return {
            "symbol": trade.symbol,
            "direction": trade.direction,
            "lot_size": float(trade.lot_size),
            "entry_price": float(trade.entry_price),
            "exit_price": float(trade.exit_price) if trade.exit_price else None,
            "profit_loss": float(trade.profit_loss) if trade.profit_loss else None,
            "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
            "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
            "entry_reason": trade.entry_reason,
            "exit_reason": trade.exit_reason,
            "strategy_id": trade.strategy_id,
            "indicators_snapshot": trade.indicators_snapshot,
        }

    def _journal_dict(self, journal: TradeJournal | None) -> dict | None:
        if not journal:
            return None
        return {
            "notes": journal.notes,
            "emotion": journal.emotion,
            "lessons_learned": journal.lessons_learned,
            "tags": journal.tags,
        }

    async def analyze_trade(self, trade_id: int) -> dict[str, Any]:
        result = await self._session.execute(
            select(Trade)
            .options(selectinload(Trade.journal))
            .where(Trade.id == trade_id)
        )
        trade = result.scalar_one_or_none()
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        prompt = trade_review_prompt(self._trade_dict(trade), self._journal_dict(trade.journal))
        ai_resp = await self._client.complete(prompt)

        user_id = await self._owner_id()
        analysis = AIAnalysis(
            user_id=user_id,
            trade_id=trade_id,
            analysis_type=AnalysisType.TRADE_REVIEW.value,
            prompt_used=prompt[:2000],
            content=ai_resp.content,
            model=ai_resp.model,
            tokens_used=ai_resp.tokens_used,
        )
        self._session.add(analysis)

        if trade.journal:
            trade.journal.ai_review = ai_resp.content
        else:
            journal = TradeJournal(trade_id=trade_id, ai_review=ai_resp.content)
            self._session.add(journal)

        await self._session.flush()
        return self._analysis_response(analysis, ai_resp.is_mock)

    async def explain_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        prompt = signal_explanation_prompt(signal)
        ai_resp = await self._client.complete(prompt)

        user_id = await self._owner_id()
        analysis = AIAnalysis(
            user_id=user_id,
            analysis_type=AnalysisType.SIGNAL_EXPLANATION.value,
            prompt_used=prompt[:2000],
            content=ai_resp.content,
            model=ai_resp.model,
            tokens_used=ai_resp.tokens_used,
            metadata_={"symbol": signal.get("symbol"), "action": signal.get("action")},
        )
        self._session.add(analysis)
        await self._session.flush()
        return self._analysis_response(analysis, ai_resp.is_mock)

    async def generate_report(self, report_type: str) -> dict[str, Any]:
        days = {"daily": 1, "weekly": 7, "monthly": 30}.get(report_type, 1)
        metrics, trades_summary = await self._gather_period_stats(days)

        prompt = period_report_prompt(report_type, metrics, trades_summary)
        ai_resp = await self._client.complete(prompt, max_tokens=2000)

        now = datetime.now(UTC)
        user_id = await self._owner_id()
        report = Report(
            user_id=user_id,
            report_type=report_type,
            period_start=now - timedelta(days=days),
            period_end=now,
            content=ai_resp.content,
            summary=ai_resp.content[:300],
            metrics=metrics,
        )
        type_map = {
            "daily": AnalysisType.DAILY_REPORT,
            "weekly": AnalysisType.WEEKLY_REPORT,
            "monthly": AnalysisType.MONTHLY_REPORT,
        }
        analysis = AIAnalysis(
            user_id=user_id,
            analysis_type=type_map.get(report_type, AnalysisType.DAILY_REPORT).value,
            content=ai_resp.content,
            model=ai_resp.model,
            tokens_used=ai_resp.tokens_used,
            metadata_={"report_type": report_type, "metrics": metrics},
        )
        self._session.add(analysis)
        self._session.add(report)
        await self._session.flush()

        return {
            "id": report.id,
            "report_type": report_type,
            "content": ai_resp.content,
            "summary": report.summary,
            "metrics": metrics,
            "model": ai_resp.model,
            "is_mock": ai_resp.is_mock,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
        }

    async def analyze_journals(self) -> dict[str, Any]:
        result = await self._session.execute(
            select(TradeJournal).order_by(TradeJournal.created_at.desc()).limit(20)
        )
        journals = [
            {
                "trade_id": j.trade_id,
                "emotion": j.emotion,
                "notes": j.notes,
                "lessons_learned": j.lessons_learned,
            }
            for j in result.scalars()
        ]
        prompt = journal_analysis_prompt(journals)
        ai_resp = await self._client.complete(prompt)

        user_id = await self._owner_id()
        analysis = AIAnalysis(
            user_id=user_id,
            analysis_type=AnalysisType.JOURNAL_ANALYSIS.value,
            content=ai_resp.content,
            model=ai_resp.model,
            tokens_used=ai_resp.tokens_used,
        )
        self._session.add(analysis)
        await self._session.flush()
        return self._analysis_response(analysis, ai_resp.is_mock)

    async def chat(self, message: str) -> dict[str, Any]:
        metrics, _ = await self._gather_period_stats(30)
        context = {
            "trading_mode": "demo",
            "open_trades": metrics.get("open_trades", 0),
            "monthly_pnl": metrics.get("total_pnl", 0),
            "win_rate": metrics.get("win_rate", 0),
        }
        prompt = chat_prompt(message, context)
        ai_resp = await self._client.complete(prompt, max_tokens=800)
        return {
            "reply": ai_resp.content,
            "model": ai_resp.model,
            "is_mock": ai_resp.is_mock,
        }

    async def list_analyses(self, limit: int = 50) -> list[dict]:
        user_id = await self._owner_id()
        result = await self._session.execute(
            select(AIAnalysis)
            .where(AIAnalysis.user_id == user_id)
            .order_by(AIAnalysis.created_at.desc())
            .limit(limit)
        )
        return [self._analysis_dict(a) for a in result.scalars()]

    async def list_reports(self, limit: int = 20) -> list[dict]:
        user_id = await self._owner_id()
        result = await self._session.execute(
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": r.id,
                "report_type": r.report_type,
                "summary": r.summary,
                "metrics": r.metrics,
                "created_at": r.created_at.isoformat(),
            }
            for r in result.scalars()
        ]

    async def _gather_period_stats(self, days: int) -> tuple[dict, list[dict]]:
        since = datetime.now(UTC) - timedelta(days=days)
        result = await self._session.execute(
            select(Trade).where(Trade.opened_at >= since).order_by(Trade.opened_at.desc())
        )
        trades = list(result.scalars())
        closed = [t for t in trades if t.status == TradeStatus.CLOSED.value]
        wins = [t for t in closed if t.profit_loss and float(t.profit_loss) > 0]
        losses = [t for t in closed if t.profit_loss and float(t.profit_loss) < 0]
        total_pnl = sum(float(t.profit_loss or 0) for t in closed)
        open_trades = len([t for t in trades if t.status == TradeStatus.OPEN.value])

        symbol_pnl: dict[str, float] = {}
        for t in closed:
            symbol_pnl[t.symbol] = symbol_pnl.get(t.symbol, 0) + float(t.profit_loss or 0)

        best = max(symbol_pnl, key=symbol_pnl.get) if symbol_pnl else None
        worst = min(symbol_pnl, key=symbol_pnl.get) if symbol_pnl else None

        hold_hours = []
        for t in closed:
            if t.closed_at and t.opened_at:
                hold_hours.append((t.closed_at - t.opened_at).total_seconds() / 3600)

        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else 0,
            "total_pnl": round(total_pnl, 2),
            "best_symbol": best,
            "worst_symbol": worst,
            "avg_hold_hours": round(sum(hold_hours) / len(hold_hours), 1) if hold_hours else 0,
            "open_trades": open_trades,
            "max_consecutive_losses": 0,
            "risk_violations": 0,
        }, [self._trade_dict(t) for t in closed]

    def _analysis_response(self, analysis: AIAnalysis, is_mock: bool) -> dict:
        return {
            **self._analysis_dict(analysis),
            "is_mock": is_mock,
        }

    def _analysis_dict(self, analysis: AIAnalysis) -> dict:
        return {
            "id": analysis.id,
            "trade_id": analysis.trade_id,
            "analysis_type": analysis.analysis_type,
            "content": analysis.content,
            "model": analysis.model,
            "tokens_used": analysis.tokens_used,
            "created_at": analysis.created_at.isoformat(),
        }
