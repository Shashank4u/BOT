"""Market scan data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketScan


class ScannerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, scan: MarketScan) -> MarketScan:
        self._session.add(scan)
        await self._session.flush()
        await self._session.refresh(scan)
        return scan

    async def list_scans(self, user_id: int, limit: int = 20) -> list[MarketScan]:
        result = await self._session.execute(
            select(MarketScan)
            .where(MarketScan.user_id == user_id)
            .order_by(MarketScan.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, scan_id: int, user_id: int) -> MarketScan | None:
        result = await self._session.execute(
            select(MarketScan).where(MarketScan.id == scan_id, MarketScan.user_id == user_id)
        )
        return result.scalar_one_or_none()
