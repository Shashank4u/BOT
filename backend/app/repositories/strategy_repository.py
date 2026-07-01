"""Strategy data access repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy import Strategy


class StrategyRepository:
    """CRUD operations for strategies."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, user_id: int) -> list[Strategy]:
        result = await self._session.execute(
            select(Strategy)
            .where(Strategy.user_id == user_id)
            .order_by(Strategy.is_sample.desc(), Strategy.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, strategy_id: int, user_id: int) -> Strategy | None:
        result = await self._session.execute(
            select(Strategy).where(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, user_id: int) -> Strategy | None:
        result = await self._session.execute(
            select(Strategy).where(
                Strategy.name == name,
                Strategy.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, strategy: Strategy) -> Strategy:
        self._session.add(strategy)
        await self._session.flush()
        await self._session.refresh(strategy)
        return strategy

    async def update(self, strategy: Strategy) -> Strategy:
        await self._session.flush()
        await self._session.refresh(strategy)
        return strategy

    async def delete(self, strategy: Strategy) -> None:
        await self._session.delete(strategy)

    async def count_samples(self, user_id: int) -> int:
        result = await self._session.execute(
            select(Strategy).where(
                Strategy.user_id == user_id,
                Strategy.is_sample.is_(True),
            )
        )
        return len(list(result.scalars().all()))
