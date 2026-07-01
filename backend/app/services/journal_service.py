"""Trade journal business logic."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import TradeJournal
from app.repositories.journal_repository import JournalRepository


class JournalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = JournalRepository(session)

    async def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        journals = await self._repo.list_journals(limit)
        return [self._to_dict(j) for j in journals]

    async def get_entry(self, trade_id: int) -> dict[str, Any] | None:
        journal = await self._repo.get_by_trade_id(trade_id)
        if not journal:
            return None
        return self._to_dict(journal)

    async def upsert_entry(self, trade_id: int, data: dict[str, Any]) -> dict[str, Any]:
        trade = await self._repo.get_trade(trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        journal = await self._repo.get_by_trade_id(trade_id)
        if journal:
            for field in ("notes", "emotion", "screenshot_path", "lessons_learned", "tags"):
                if field in data:
                    setattr(journal, field, data[field])
            journal = await self._repo.update(journal)
        else:
            journal = TradeJournal(
                trade_id=trade_id,
                notes=data.get("notes"),
                emotion=data.get("emotion"),
                screenshot_path=data.get("screenshot_path"),
                lessons_learned=data.get("lessons_learned"),
                tags=data.get("tags"),
            )
            journal = await self._repo.create(journal)

        # Re-fetch with trade relationship loaded
        loaded = await self._repo.get_by_trade_id(trade_id)
        return self._to_dict(loaded or journal)

    async def delete_entry(self, trade_id: int) -> bool:
        journal = await self._repo.get_by_trade_id(trade_id)
        if not journal:
            return False
        await self._repo.delete(journal)
        return True

    def _to_dict(self, journal: TradeJournal) -> dict[str, Any]:
        trade = journal.trade
        return {
            "id": journal.id,
            "trade_id": journal.trade_id,
            "notes": journal.notes,
            "emotion": journal.emotion,
            "screenshot_path": journal.screenshot_path,
            "lessons_learned": journal.lessons_learned,
            "ai_review": journal.ai_review,
            "tags": journal.tags,
            "created_at": journal.created_at.isoformat(),
            "updated_at": journal.updated_at.isoformat(),
            "trade": {
                "symbol": trade.symbol,
                "direction": trade.direction,
                "status": trade.status,
                "profit_loss": float(trade.profit_loss) if trade.profit_loss else None,
            }
            if trade
            else None,
        }
