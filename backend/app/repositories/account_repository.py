"""Trading account data access."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import TradingAccount


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, user_id: int) -> list[TradingAccount]:
        result = await self._session.execute(
            select(TradingAccount)
            .where(TradingAccount.user_id == user_id)
            .order_by(TradingAccount.is_active.desc(), TradingAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, account_id: int, user_id: int) -> TradingAccount | None:
        result = await self._session.execute(
            select(TradingAccount).where(
                TradingAccount.id == account_id,
                TradingAccount.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_login(self, user_id: int, mt5_login: int) -> TradingAccount | None:
        result = await self._session.execute(
            select(TradingAccount).where(
                TradingAccount.user_id == user_id,
                TradingAccount.mt5_login == mt5_login,
            )
        )
        return result.scalar_one_or_none()

    async def get_active(self, user_id: int) -> TradingAccount | None:
        result = await self._session.execute(
            select(TradingAccount).where(
                TradingAccount.user_id == user_id,
                TradingAccount.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def deactivate_all(self, user_id: int) -> None:
        await self._session.execute(
            update(TradingAccount)
            .where(TradingAccount.user_id == user_id)
            .values(is_active=False, is_connected=False)
        )

    async def create(self, account: TradingAccount) -> TradingAccount:
        self._session.add(account)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def update(self, account: TradingAccount) -> TradingAccount:
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def delete(self, account: TradingAccount) -> None:
        await self._session.delete(account)
