"""Risk manager — validates trades against user limits."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import TradingNotAllowedError
from app.models.settings import UserSettings
from app.models.trade import Trade, TradeStatus
from app.trading.risk.calculator import calculate_lot_size
from app.trading.risk.types import RiskCheckResult


class RiskManager:
    """Enforce risk rules before order execution."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_settings(self, user_id: int) -> UserSettings:
        result = await self._session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            raise ValueError("User settings not found")
        return settings

    def check_live_trading_allowed(self, user_settings: UserSettings) -> None:
        """Block live trading unless explicitly confirmed by user."""
        app_settings = get_settings()
        if app_settings.is_demo_mode:
            return  # Demo mode always allowed on demo/mock
        if not user_settings.live_trading_confirmed:
            raise TradingNotAllowedError()

    async def validate_trade(
        self,
        user_id: int,
        balance: float,
        symbol: str,
        lot_size: float,
        stop_loss_pips: float,
        open_trades_count: int,
    ) -> RiskCheckResult:
        """Run all risk checks for a proposed trade."""
        settings = await self.get_settings(user_id)
        violations: list[str] = []
        warnings: list[str] = []

        # Lot size vs max risk per trade
        pos = calculate_lot_size(
            balance, float(settings.max_risk_per_trade), stop_loss_pips, symbol
        )
        if lot_size > pos.lot_size * 1.1:  # 10% tolerance
            violations.append(
                f"Lot size {lot_size} exceeds max risk "
                f"({settings.max_risk_per_trade}% = {pos.lot_size} lots)"
            )

        # Max open trades
        if open_trades_count >= settings.max_open_trades:
            violations.append(
                f"Max open trades reached ({settings.max_open_trades})"
            )

        # Daily loss limit
        daily_pnl = await self._period_pnl(user_id, days=1)
        if daily_pnl < 0 and abs(daily_pnl) >= float(settings.max_daily_loss):
            violations.append(
                f"Daily loss limit reached (${abs(daily_pnl):.2f} / ${settings.max_daily_loss})"
            )

        # Weekly loss limit
        weekly_pnl = await self._period_pnl(user_id, days=7)
        if weekly_pnl < 0 and abs(weekly_pnl) >= float(settings.max_weekly_loss):
            violations.append(
                f"Weekly loss limit reached (${abs(weekly_pnl):.2f} / ${settings.max_weekly_loss})"
            )

        # Monthly loss limit
        monthly_pnl = await self._period_pnl(user_id, days=30)
        if monthly_pnl < 0 and abs(monthly_pnl) >= float(settings.max_monthly_loss):
            violations.append(
                f"Monthly loss limit reached (${abs(monthly_pnl):.2f} / ${settings.max_monthly_loss})"
            )

        # Consecutive losses
        consec = await self._consecutive_losses(user_id)
        if consec >= settings.max_consecutive_losses:
            violations.append(
                f"Max consecutive losses reached ({consec}/{settings.max_consecutive_losses})"
            )

        # News pause
        if settings.pause_trading_during_news:
            news_violation = await self._check_news_pause(symbol, settings)
            if news_violation:
                violations.append(news_violation)

        if not violations and lot_size > pos.lot_size:
            warnings.append(
                f"Lot size slightly above ideal risk sizing ({pos.lot_size} recommended)"
            )

        return RiskCheckResult(
            allowed=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            lot_size=pos.lot_size,
            risk_amount=pos.risk_amount,
        )

    async def _period_pnl(self, user_id: int, days: int) -> float:
        since = datetime.now(UTC) - timedelta(days=days)
        result = await self._session.execute(
            select(Trade).where(
                Trade.status == TradeStatus.CLOSED.value,
                Trade.closed_at >= since,
            )
        )
        trades = result.scalars().all()
        return sum(float(t.profit_loss or 0) for t in trades)

    async def _consecutive_losses(self, user_id: int) -> int:
        result = await self._session.execute(
            select(Trade)
            .where(Trade.status == TradeStatus.CLOSED.value)
            .order_by(Trade.closed_at.desc())
            .limit(20)
        )
        count = 0
        for trade in result.scalars():
            if trade.profit_loss is not None and float(trade.profit_loss) < 0:
                count += 1
            else:
                break
        return count

    async def _check_news_pause(self, symbol: str, settings: UserSettings) -> str | None:
        from app.repositories.news_repository import NewsRepository
        from app.trading.news.guard import is_trading_paused

        impact_filter = settings.news_impact_filter or ["high"]
        if isinstance(impact_filter, str):
            impact_filter = [impact_filter]

        repo = NewsRepository(self._session)
        events = await repo.list_events(hours_ahead=24, hours_back=1, impact=impact_filter)
        if not events:
            return None

        paused, reason = is_trading_paused(symbol, events, impact_filter)
        return reason if paused else None

    async def get_risk_status(self, user_id: int, open_trades: int) -> dict:
        """Summary of current risk exposure."""
        settings = await self.get_settings(user_id)
        daily = await self._period_pnl(user_id, 1)
        weekly = await self._period_pnl(user_id, 7)
        monthly = await self._period_pnl(user_id, 30)
        consec = await self._consecutive_losses(user_id)

        return {
            "trading_mode": get_settings().trading_mode.value,
            "live_trading_confirmed": settings.live_trading_confirmed,
            "max_risk_per_trade": float(settings.max_risk_per_trade),
            "max_daily_loss": float(settings.max_daily_loss),
            "max_weekly_loss": float(settings.max_weekly_loss),
            "max_monthly_loss": float(settings.max_monthly_loss),
            "max_open_trades": settings.max_open_trades,
            "max_consecutive_losses": settings.max_consecutive_losses,
            "open_trades": open_trades,
            "daily_pnl": round(daily, 2),
            "weekly_pnl": round(weekly, 2),
            "monthly_pnl": round(monthly, 2),
            "consecutive_losses": consec,
            "daily_loss_remaining": round(float(settings.max_daily_loss) + min(daily, 0), 2),
        }
