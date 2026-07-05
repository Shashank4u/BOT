"""Trading pause guard during high-impact news."""

from datetime import UTC, datetime, timedelta

from app.trading.news.currencies import currencies_for_symbol

DEFAULT_MINUTES_BEFORE = 30
DEFAULT_MINUTES_AFTER = 15


def is_trading_paused(
    symbol: str,
    events: list,
    impact_filter: list[str],
    minutes_before: int = DEFAULT_MINUTES_BEFORE,
    minutes_after: int = DEFAULT_MINUTES_AFTER,
    now: datetime | None = None,
) -> tuple[bool, str | None]:
    """
    Return True if trading should be paused for symbol due to nearby news.
    events: objects or dicts with impact, currency, title, event_time.
    """
    if not events or not impact_filter:
        return False, None

    now = now or datetime.now(UTC)
    symbol_currencies = {c.upper() for c in currencies_for_symbol(symbol)}
    allowed_impacts = {i.lower() for i in impact_filter}

    for event in events:
        impact = _field(event, "impact", "").lower()
        if impact not in allowed_impacts:
            continue

        currency = _field(event, "currency", "").upper()
        if currency not in symbol_currencies:
            continue

        event_time = _field(event, "event_time")
        if event_time is None:
            continue
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=UTC)

        window_start = event_time - timedelta(minutes=minutes_before)
        window_end = event_time + timedelta(minutes=minutes_after)

        if window_start <= now <= window_end:
            title = _field(event, "title", "Economic event")
            return True, (
                f"Trading paused: high-impact news '{title}' ({currency}) "
                f"at {event_time.strftime('%H:%M UTC')}"
            )

    return False, None


def _field(obj, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)
