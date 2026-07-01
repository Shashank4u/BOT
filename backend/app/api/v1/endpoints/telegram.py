"""Telegram notification endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.notifications import (
    TelegramSettingsUpdate,
    TelegramStatusSchema,
    TelegramTestResponse,
)
from app.notifications.service import NotificationService
from app.services.risk_service import RiskService

router = APIRouter(prefix="/telegram", tags=["Telegram"])


def get_notification_service(db: DbSession) -> NotificationService:
    return NotificationService(db)


def get_risk_service(db: DbSession) -> RiskService:
    return RiskService(db)


NotifySvc = Annotated[NotificationService, Depends(get_notification_service)]
RiskSvc = Annotated[RiskService, Depends(get_risk_service)]


@router.get("/status", response_model=TelegramStatusSchema)
async def telegram_status(svc: NotifySvc) -> TelegramStatusSchema:
    """Check Telegram bot configuration status."""
    return TelegramStatusSchema(**svc.telegram_status())


@router.post("/test", response_model=TelegramTestResponse)
async def send_test_message(svc: NotifySvc) -> TelegramTestResponse:
    """Send a test message to verify Telegram integration."""
    result = await svc.send_test_message()
    return TelegramTestResponse(
        sent=result.get("sent", False),
        is_mock=result.get("is_mock", True),
        message=result.get("message", ""),
    )


@router.patch("/settings")
async def update_telegram_settings(body: TelegramSettingsUpdate, risk: RiskSvc) -> dict:
    """Enable/disable Telegram and notification toggles."""
    settings = await risk.update_settings(body.model_dump(exclude_unset=True))
    await risk._session.commit()
    return {
        "telegram_enabled": settings.telegram_enabled,
        "notify_trade_open": settings.notify_trade_open,
        "notify_trade_close": settings.notify_trade_close,
        "notify_risk_alert": settings.notify_risk_alert,
        "notify_daily_report": settings.notify_daily_report,
    }
