"""Telegram Bot API client with mock fallback."""

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TelegramResult:
    success: bool
    message: str
    is_mock: bool


class TelegramClient:
    """Send messages via Telegram Bot API. Mock mode when token/chat_id not set."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.telegram_bot_token and self._settings.telegram_chat_id)

    @property
    def is_mock(self) -> bool:
        return not self.is_configured

    async def send_message(self, text: str, parse_mode: str = "HTML") -> TelegramResult:
        if self.is_mock:
            logger.info("Telegram mock: %s", text[:200])
            return TelegramResult(success=True, message="Mock message logged", is_mock=True)

        try:
            from telegram import Bot

            bot = Bot(token=self._settings.telegram_bot_token)
            await bot.send_message(
                chat_id=self._settings.telegram_chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return TelegramResult(success=True, message="Sent", is_mock=False)
        except Exception as exc:
            logger.error("Telegram send failed: %s", exc)
            return TelegramResult(success=False, message=str(exc), is_mock=False)
