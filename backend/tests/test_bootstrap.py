"""Bootstrap service tests."""

import pytest
from sqlalchemy import select

from app.models.settings import UserSettings
from app.models.user import User
from app.services.bootstrap import ensure_default_owner


@pytest.mark.asyncio
async def test_ensure_default_owner_creates_user(db_session) -> None:
    user = await ensure_default_owner(db_session)
    assert user.id is not None
    assert user.display_name == "Owner"

    result = await db_session.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_ensure_default_owner_creates_settings(db_session) -> None:
    user = await ensure_default_owner(db_session)
    result = await db_session.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one()
    assert settings.trading_mode == "demo"
    assert "EURUSD" in settings.watchlist_symbols


@pytest.mark.asyncio
async def test_ensure_default_owner_idempotent(db_session) -> None:
    user1 = await ensure_default_owner(db_session)
    user2 = await ensure_default_owner(db_session)
    assert user1.id == user2.id
