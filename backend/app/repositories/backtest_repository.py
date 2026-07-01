"""Backtest run data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.market import BacktestRun


class BacktestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: BacktestRun) -> BacktestRun:
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get_by_id(self, run_id: int, user_id: int) -> BacktestRun | None:
        result = await self._session.execute(
            select(BacktestRun)
            .options(selectinload(BacktestRun.strategy))
            .where(BacktestRun.id == run_id, BacktestRun.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_runs(self, user_id: int, limit: int = 50) -> list[BacktestRun]:
        result = await self._session.execute(
            select(BacktestRun)
            .options(selectinload(BacktestRun.strategy))
            .where(BacktestRun.user_id == user_id)
            .order_by(BacktestRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
