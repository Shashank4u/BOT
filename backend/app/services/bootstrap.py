"""Bootstrap single owner and default settings on first run."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.auto_trading import AutoTradingConfig
from app.models.settings import UserSettings
from app.models.user import User

logger = get_logger(__name__)

DEFAULT_WATCHLIST = [
    "XAUUSD",
    "XAGUSD",
    "BTCUSD",
    "ETHUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "US30",
    "NAS100",
]


async def ensure_default_owner(session: AsyncSession) -> User:
    """Create the implicit owner user and settings if they do not exist."""
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(display_name="Owner")
        session.add(user)
        await session.flush()
        logger.info("Created default owner user (id=%s)", user.id)

    settings_result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = settings_result.scalar_one_or_none()

    if settings is None:
        settings = UserSettings(
            user_id=user.id,
            watchlist_symbols=DEFAULT_WATCHLIST,
            trading_mode="demo",
            live_trading_confirmed=False,
        )
        session.add(settings)
        logger.info("Created default settings for owner")

    config_result = await session.execute(
        select(AutoTradingConfig).where(AutoTradingConfig.id == 1)
    )
    if config_result.scalar_one_or_none() is None:
        session.add(AutoTradingConfig(id=1))
        logger.info("Created default auto-trading config")

    await session.commit()
    return user
