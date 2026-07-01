"""Risk management service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.settings import UserSettings
from app.models.user import User
from app.trading.risk.calculator import calculate_lot_size, calculate_margin, calculate_risk_reward
from app.trading.risk.manager import RiskManager
from app.trading.connection import get_provider


class RiskService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._manager = RiskManager(session)

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def get_settings(self) -> UserSettings:
        return await self._manager.get_settings(await self._owner_id())

    async def update_settings(self, data: dict) -> UserSettings:
        settings = await self.get_settings()
        for key, value in data.items():
            if value is not None and hasattr(settings, key):
                setattr(settings, key, value)
        await self._session.flush()
        await self._session.refresh(settings)
        return settings

    async def confirm_live_trading(self) -> UserSettings:
        settings = await self.get_settings()
        settings.live_trading_confirmed = True
        await self._session.flush()
        await self._session.refresh(settings)
        return settings

    def calc_lot_size(self, balance, risk_percent, stop_loss_pips, symbol):
        return calculate_lot_size(balance, risk_percent, stop_loss_pips, symbol)

    def calc_risk_reward(self, entry, sl, tp, symbol, side="buy"):
        return calculate_risk_reward(entry, sl, tp, symbol, side)

    def calc_margin(self, lot_size, symbol, price, leverage, free_margin):
        return calculate_margin(lot_size, symbol, price, leverage, free_margin)

    async def check_trade(self, symbol, lot_size, stop_loss_pips, balance):
        user_id = await self._owner_id()
        open_count = 0
        try:
            positions = get_provider().get_positions()
            open_count = len(positions)
        except Exception:
            pass
        return await self._manager.validate_trade(
            user_id, balance, symbol, lot_size, stop_loss_pips, open_count
        )

    async def get_status(self) -> dict:
        user_id = await self._owner_id()
        try:
            open_count = len(get_provider().get_positions())
        except Exception:
            open_count = 0
        return await self._manager.get_risk_status(user_id, open_count)

    def settings_response(self, settings: UserSettings) -> dict:
        return {
            "max_risk_per_trade": float(settings.max_risk_per_trade),
            "max_daily_loss": float(settings.max_daily_loss),
            "max_weekly_loss": float(settings.max_weekly_loss),
            "max_monthly_loss": float(settings.max_monthly_loss),
            "max_open_trades": settings.max_open_trades,
            "max_consecutive_losses": settings.max_consecutive_losses,
            "live_trading_confirmed": settings.live_trading_confirmed,
            "trading_mode": get_settings().trading_mode.value,
        }
