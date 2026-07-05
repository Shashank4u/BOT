"""OpenAI client with mock fallback for development and tests."""

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ai.prompts.system import DISCLAIMER, SYSTEM_PROMPT

logger = get_logger(__name__)


@dataclass
class AIResponse:
    content: str
    model: str
    tokens_used: int
    is_mock: bool


class AIClient:
    """Wraps OpenAI API. Falls back to mock responses when no API key is set."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def is_mock(self) -> bool:
        return not self._settings.openai_api_key

    async def complete(self, prompt: str, max_tokens: int = 1500) -> AIResponse:
        if self.is_mock:
            return self._mock_response(prompt)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._settings.openai_api_key)
            response = await client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.4,
            )
            content = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else 0
            logger.info("OpenAI response: %d tokens, model=%s", tokens, self._settings.openai_model)
            return AIResponse(
                content=content,
                model=self._settings.openai_model,
                tokens_used=tokens,
                is_mock=False,
            )
        except Exception as exc:
            logger.error("OpenAI API error: %s — falling back to mock", exc)
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> AIResponse:
        """Generate a structured mock response for dev/CI without OpenAI."""
        if "completed trade" in prompt.lower() or "trade data" in prompt.lower():
            content = f"""## Trade Analysis (Mock — set OPENAI_API_KEY for real analysis)

**What happened:** The trade followed your strategy rules on the given symbol. The outcome reflects market conditions during the holding period.

**What went well:** You recorded the trade with an entry reason, which supports good discipline.

**What could improve:** Review whether stop-loss placement matched your risk plan. Consider if position size aligned with your 1% risk rule.

**Risk assessment:** Verify lot size against account balance and stop distance before future similar trades.

**Behavioral note:** Journaling emotions after each trade helps identify patterns over time.

{DISCLAIMER}"""
        elif "signal" in prompt.lower() and "strategy" in prompt.lower():
            content = f"""## Signal Explanation (Mock)

The strategy conditions you configured were met based on the indicator values provided. This explains why the rule triggered — it does **not** predict future price movement.

**Uncertainties:** Market conditions can change quickly. A signal is one input to your decision, not a guarantee.

**Risk:** Always confirm position size and stop-loss before executing.

{DISCLAIMER}"""
        elif "report" in prompt.lower() or "performance" in prompt.lower():
            content = f"""## Performance Report (Mock)

**Summary:** Review the metrics provided for this period. Focus on process consistency rather than short-term P/L.

**Highlights:** Track which symbols and sessions perform best for your strategies.

**Improvements:** Watch for overtrading after losses. Stick to max daily loss limits.

**Recommendations:** Continue journaling. Review losing trades for repeated mistakes.

{DISCLAIMER}"""
        elif "journal" in prompt.lower():
            content = f"""## Journal Analysis (Mock)

Recording emotions and lessons after trades builds self-awareness. Look for patterns where frustration leads to larger positions or deviating from your plan.

{DISCLAIMER}"""
        else:
            content = f"""I'm your AI Trading Assistant (mock mode — set OPENAI_API_KEY for full responses).

I can help explain trades, signals, and performance based on your data. I do not predict markets or guarantee profits.

Ask me to analyze a specific trade, explain a signal, or generate a performance report.

{DISCLAIMER}"""

        return AIResponse(
            content=content,
            model="mock",
            tokens_used=0,
            is_mock=True,
        )
