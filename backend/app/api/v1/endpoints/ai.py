"""AI assistant endpoints — analysis, reports, chat."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.ai.service import AIService
from app.schemas.ai import (
    AnalysisResponseSchema,
    ChatRequest,
    ChatResponseSchema,
    ReportListItemSchema,
    ReportResponseSchema,
    SignalExplainRequest,
)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def get_ai_service(db: DbSession) -> AIService:
    return AIService(db)


AISvc = Annotated[AIService, Depends(get_ai_service)]


@router.post("/analyze/trade/{trade_id}", response_model=AnalysisResponseSchema)
async def analyze_trade(trade_id: int, svc: AISvc) -> AnalysisResponseSchema:
    """
    AI review of a completed trade.
    Explains what happened and suggests process improvements — never predicts markets.
    """
    try:
        result = await svc.analyze_trade(trade_id)
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnalysisResponseSchema(**result)


@router.post("/explain/signal", response_model=AnalysisResponseSchema)
async def explain_signal(body: SignalExplainRequest, svc: AISvc) -> AnalysisResponseSchema:
    """Explain why a strategy signal occurred — not a prediction."""
    result = await svc.explain_signal(body.model_dump())
    await svc._session.commit()
    return AnalysisResponseSchema(**result)


@router.post("/reports/{report_type}", response_model=ReportResponseSchema)
async def generate_report(report_type: str, svc: AISvc) -> ReportResponseSchema:
    """Generate daily, weekly, or monthly performance report."""
    if report_type not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="report_type must be daily, weekly, or monthly")
    result = await svc.generate_report(report_type)
    await svc._session.commit()
    return ReportResponseSchema(**result)


@router.post("/analyze/journals", response_model=AnalysisResponseSchema)
async def analyze_journals(svc: AISvc) -> AnalysisResponseSchema:
    """Analyze journal entries for behavioral patterns."""
    result = await svc.analyze_journals()
    await svc._session.commit()
    return AnalysisResponseSchema(**result)


@router.post("/chat", response_model=ChatResponseSchema)
async def ai_chat(body: ChatRequest, svc: AISvc) -> ChatResponseSchema:
    """Chat with the AI assistant about your trading performance."""
    result = await svc.chat(body.message)
    return ChatResponseSchema(**result)


@router.get("/analyses", response_model=list[AnalysisResponseSchema])
async def list_analyses(svc: AISvc, limit: int = 50) -> list[AnalysisResponseSchema]:
    """List past AI analyses."""
    analyses = await svc.list_analyses(limit)
    return [AnalysisResponseSchema(**a, is_mock=False) for a in analyses]


@router.get("/reports", response_model=list[ReportListItemSchema])
async def list_reports(svc: AISvc, limit: int = 20) -> list[ReportListItemSchema]:
    """List generated reports."""
    reports = await svc.list_reports(limit)
    return [ReportListItemSchema(**r) for r in reports]
