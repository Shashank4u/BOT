"""In-app and Telegram notification orchestration."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.settings import Notification, UserSettings
from app.models.trade import Trade
from app.models.user import User
from app.notifications.telegram_client import TelegramClient
from app.notifications import templates

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._telegram = TelegramClient()

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def _get_settings(self) -> UserSettings | None:
        user_id = await self._owner_id()
        result = await self._session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _create_notification(
        self,
        title: str,
        message: str,
        category: str,
        metadata: dict | None = None,
    ) -> Notification:
        user_id = await self._owner_id()
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            metadata_=metadata,
        )
        self._session.add(notif)
        await self._session.flush()
        return notif

    async def _send_telegram(self, text: str, settings: UserSettings | None) -> dict[str, Any]:
        if settings and not settings.telegram_enabled:
            return {"sent": False, "reason": "telegram_disabled"}
        result = await self._telegram.send_message(text)
        return {"sent": result.success, "is_mock": result.is_mock, "message": result.message}

    async def notify_trade_opened(self, trade: Trade) -> dict[str, Any]:
        settings = await self._get_settings()
        is_demo = get_settings().is_demo_mode
        title = f"Trade opened: {trade.symbol} {trade.direction.upper()}"
        message = f"{trade.direction.upper()} {float(trade.lot_size)} lots @ {float(trade.entry_price):.5f}"

        await self._create_notification(
            title, message, "trade_open", {"trade_id": trade.id, "symbol": trade.symbol}
        )

        tg_result = {"sent": False}
        if not settings or settings.notify_trade_open:
            tg_result = await self._send_telegram(
                templates.trade_opened_message(trade, is_demo), settings
            )
        return {"notification": title, "telegram": tg_result}

    async def notify_trade_closed(self, trade: Trade) -> dict[str, Any]:
        settings = await self._get_settings()
        is_demo = get_settings().is_demo_mode
        pnl = float(trade.profit_loss or 0)
        title = f"Trade closed: {trade.symbol} ${pnl:+.2f}"
        message = f"Exit @ {float(trade.exit_price):.5f} — P/L ${pnl:+.2f}" if trade.exit_price else f"P/L ${pnl:+.2f}"

        await self._create_notification(
            title, message, "trade_close", {"trade_id": trade.id, "pnl": pnl}
        )

        tg_result = {"sent": False}
        if not settings or settings.notify_trade_close:
            tg_result = await self._send_telegram(
                templates.trade_closed_message(trade, is_demo), settings
            )
        return {"notification": title, "telegram": tg_result}

    async def notify_risk_alert(self, violations: list[str]) -> dict[str, Any]:
        settings = await self._get_settings()
        title = "Risk alert: trade blocked"
        message = "; ".join(violations)

        await self._create_notification(title, message, "risk_alert", {"violations": violations})

        tg_result = {"sent": False}
        if settings and settings.notify_risk_alert:
            tg_result = await self._send_telegram(templates.risk_alert_message(violations), settings)
        return {"notification": title, "telegram": tg_result}

    async def send_test_message(self) -> dict[str, Any]:
        result = await self._telegram.send_message(templates.test_message())
        return {
            "sent": result.success,
            "is_mock": result.is_mock,
            "message": result.message,
        }

    async def send_report(self, report_type: str, content: str) -> dict[str, Any]:
        settings = await self._get_settings()
        if settings and not settings.notify_daily_report:
            return {"sent": False, "reason": "daily_report_disabled"}
        summary = content[:500]
        await self._create_notification(
            f"{report_type.title()} report",
            summary,
            "report",
            {"report_type": report_type},
        )
        return await self._send_telegram(templates.report_message(report_type, content), settings)

    def telegram_status(self) -> dict[str, Any]:
        return {
            "configured": self._telegram.is_configured,
            "is_mock": self._telegram.is_mock,
            "bot_token_set": bool(get_settings().telegram_bot_token),
            "chat_id_set": bool(get_settings().telegram_chat_id),
        }

    async def list_notifications(self, limit: int = 50, unread_only: bool = False) -> list[dict]:
        user_id = await self._owner_id()
        q = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read.is_(False))
        q = q.order_by(Notification.created_at.desc()).limit(limit)
        result = await self._session.execute(q)
        return [self._notif_dict(n) for n in result.scalars()]

    async def mark_read(self, notification_id: int) -> bool:
        user_id = await self._owner_id()
        result = await self._session.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return False
        notif.is_read = True
        await self._session.flush()
        return True

    async def mark_all_read(self) -> int:
        user_id = await self._owner_id()
        result = await self._session.execute(
            select(Notification).where(
                Notification.user_id == user_id, Notification.is_read.is_(False)
            )
        )
        count = 0
        for notif in result.scalars():
            notif.is_read = True
            count += 1
        await self._session.flush()
        return count

    def _notif_dict(self, notif: Notification) -> dict[str, Any]:
        return {
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "category": notif.category,
            "is_read": notif.is_read,
            "metadata": notif.metadata_,
            "created_at": notif.created_at.isoformat(),
        }
