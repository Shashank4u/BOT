"""Auto-trading config repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auto_trading import AutoTradingConfig


class AutoTradingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self) -> AutoTradingConfig:
        result = await self._session.execute(
            select(AutoTradingConfig).where(AutoTradingConfig.id == 1)
        )
        config = result.scalar_one_or_none()
        if config is None:
            config = AutoTradingConfig(id=1)
            self._session.add(config)
            await self._session.flush()
            await self._session.refresh(config)
        return config

    async def update(self, config: AutoTradingConfig) -> AutoTradingConfig:
        await self._session.flush()
        await self._session.refresh(config)
        return config
