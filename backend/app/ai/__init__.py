"""AI module — OpenAI integration with mock fallback."""

from app.ai.client import AIClient
from app.ai.service import AIService

__all__ = ["AIClient", "AIService"]
