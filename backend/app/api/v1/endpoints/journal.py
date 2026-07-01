"""Trade journal endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.schemas.journal import JournalResponseSchema, JournalUpsertRequest
from app.services.journal_service import JournalService

router = APIRouter(prefix="/journal", tags=["Journal"])


def get_journal_service(db: DbSession) -> JournalService:
    return JournalService(db)


JournalSvc = Annotated[JournalService, Depends(get_journal_service)]


@router.get("", response_model=list[JournalResponseSchema])
async def list_journal_entries(svc: JournalSvc, limit: int = 100) -> list[JournalResponseSchema]:
    """List all trade journal entries."""
    entries = await svc.list_entries(limit)
    return [JournalResponseSchema(**e) for e in entries]


@router.get("/{trade_id}", response_model=JournalResponseSchema)
async def get_journal_entry(trade_id: int, svc: JournalSvc) -> JournalResponseSchema:
    """Get journal entry for a specific trade."""
    entry = await svc.get_entry(trade_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"No journal for trade {trade_id}")
    return JournalResponseSchema(**entry)


@router.put("/{trade_id}", response_model=JournalResponseSchema)
async def upsert_journal_entry(
    trade_id: int, body: JournalUpsertRequest, svc: JournalSvc
) -> JournalResponseSchema:
    """Create or update journal notes, emotion, tags, and screenshot path for a trade."""
    try:
        entry = await svc.upsert_entry(trade_id, body.model_dump(exclude_unset=True))
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JournalResponseSchema(**entry)


@router.delete("/{trade_id}", status_code=204)
async def delete_journal_entry(trade_id: int, svc: JournalSvc) -> None:
    """Delete a journal entry."""
    deleted = await svc.delete_entry(trade_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No journal for trade {trade_id}")
    await svc._session.commit()
