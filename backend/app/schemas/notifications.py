"""Notification API schemas."""

from typing import Any

from pydantic import BaseModel


class NotificationSchema(BaseModel):
    id: int
    title: str
    message: str
    category: str
    is_read: bool
    metadata: dict[str, Any] | None
    created_at: str


class TelegramStatusSchema(BaseModel):
    configured: bool
    is_mock: bool
    bot_token_set: bool
    chat_id_set: bool


class TelegramTestResponse(BaseModel):
    sent: bool
    is_mock: bool
    message: str


class TelegramSettingsUpdate(BaseModel):
    telegram_enabled: bool | None = None
    notify_trade_open: bool | None = None
    notify_trade_close: bool | None = None
    notify_risk_alert: bool | None = None
    notify_daily_report: bool | None = None
