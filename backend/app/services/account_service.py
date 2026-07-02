"""Broker account business logic."""

from dataclasses import asdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_secret, encrypt_secret
from app.models.account import AccountType, TradingAccount
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.services.market_data import MarketDataService
from app.trading.connection import get_provider

logger = get_logger(__name__)


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)
        self._market = MarketDataService()

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    def _to_response(self, account: TradingAccount) -> dict:
        return {
            "id": account.id,
            "name": account.name,
            "broker": account.broker,
            "account_type": account.account_type,
            "mt5_login": account.mt5_login,
            "mt5_server": account.mt5_server,
            "currency": account.currency,
            "leverage": account.leverage,
            "balance": float(account.balance),
            "equity": float(account.equity),
            "margin": float(account.margin),
            "free_margin": float(account.free_margin),
            "is_active": account.is_active,
            "is_connected": account.is_connected,
            "created_at": account.created_at,
        }

    async def list_accounts(self) -> list[dict]:
        user_id = await self._owner_id()
        accounts = await self._repo.list_all(user_id)
        return [self._to_response(a) for a in accounts]

    async def get_active_account(self) -> dict | None:
        user_id = await self._owner_id()
        account = await self._repo.get_active(user_id)
        if account is None:
            return None
        return self._to_response(account)

    async def add_and_connect(self, data: dict) -> dict:
        user_id = await self._owner_id()
        password = data["mt5_password"]
        login = data["mt5_login"]
        server = data["mt5_server"]

        status = self._market.connect(login=login, password=password, server=server)
        if not status.connected:
            raise ValueError(status.message or "Failed to connect to MT5")

        info = self._market.get_account()
        settings = get_settings()
        encrypted = encrypt_secret(password, settings.secret_key)

        existing = await self._repo.get_by_login(user_id, login)
        await self._repo.deactivate_all(user_id)

        if existing:
            account = existing
            account.name = data.get("name", account.name)
            account.broker = data.get("broker", account.broker)
            account.account_type = data.get("account_type", account.account_type)
            account.mt5_server = server
            account.encrypted_password = encrypted
        else:
            account = TradingAccount(
                user_id=user_id,
                name=data.get("name", "XM Account"),
                broker=data.get("broker", "XM"),
                account_type=data.get("account_type", AccountType.DEMO.value),
                mt5_login=login,
                mt5_server=server,
                encrypted_password=encrypted,
            )
            await self._repo.create(account)

        self._sync_from_provider(account, info)
        account.is_active = True
        account.is_connected = True
        await self._repo.update(account)

        logger.info("Broker account connected: login=%s server=%s", login, server)
        return {
            "account": self._to_response(account),
            "connection": asdict(status),
            "message": f"Connected to {server} (login {login})",
        }

    async def connect_account(self, account_id: int) -> dict:
        user_id = await self._owner_id()
        account = await self._repo.get_by_id(account_id, user_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        password = decrypt_secret(account.encrypted_password, get_settings().secret_key)
        status = self._market.connect(
            login=account.mt5_login,
            password=password,
            server=account.mt5_server,
        )
        if not status.connected:
            account.is_connected = False
            await self._repo.update(account)
            raise ValueError(status.message or "Failed to connect to MT5")

        await self._repo.deactivate_all(user_id)
        info = self._market.get_account()
        self._sync_from_provider(account, info)
        account.is_active = True
        account.is_connected = True
        await self._repo.update(account)

        return {
            "account": self._to_response(account),
            "connection": asdict(status),
            "message": f"Reconnected to {account.mt5_server}",
        }

    async def disconnect_active(self) -> dict:
        user_id = await self._owner_id()
        account = await self._repo.get_active(user_id)
        status = self._market.disconnect()

        if account:
            account.is_connected = False
            await self._repo.update(account)

        return {
            "connection": asdict(status),
            "message": "Disconnected from MT5",
        }

    async def activate_account(self, account_id: int) -> dict:
        return await self.connect_account(account_id)

    async def delete_account(self, account_id: int) -> None:
        user_id = await self._owner_id()
        account = await self._repo.get_by_id(account_id, user_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        was_active = account.is_active
        await self._repo.delete(account)

        if was_active:
            get_provider().disconnect()
            remaining = await self._repo.list_all(user_id)
            if remaining:
                await self.connect_account(remaining[0].id)

    def _sync_from_provider(self, account: TradingAccount, info) -> None:
        account.balance = Decimal(str(info.balance))
        account.equity = Decimal(str(info.equity))
        account.margin = Decimal(str(info.margin))
        account.free_margin = Decimal(str(info.free_margin))
        account.currency = info.currency
        account.leverage = info.leverage
        if info.server:
            account.mt5_server = info.server
