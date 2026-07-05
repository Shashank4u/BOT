"""Mock economic calendar for development and testing."""

from datetime import UTC, datetime, timedelta

import numpy as np

# Recurring high-impact event templates
EVENT_TEMPLATES = [
    {"title": "US Non-Farm Payrolls", "country": "US", "currency": "USD", "impact": "high"},
    {"title": "FOMC Interest Rate Decision", "country": "US", "currency": "USD", "impact": "high"},
    {"title": "US CPI m/m", "country": "US", "currency": "USD", "impact": "high"},
    {"title": "ECB Interest Rate Decision", "country": "EU", "currency": "EUR", "impact": "high"},
    {"title": "German ZEW Economic Sentiment", "country": "DE", "currency": "EUR", "impact": "medium"},
    {"title": "UK GDP q/q", "country": "GB", "currency": "GBP", "impact": "high"},
    {"title": "BoE Interest Rate Decision", "country": "GB", "currency": "GBP", "impact": "high"},
    {"title": "BoJ Interest Rate Decision", "country": "JP", "currency": "JPY", "impact": "high"},
    {"title": "US Retail Sales m/m", "country": "US", "currency": "USD", "impact": "medium"},
    {"title": "US Initial Jobless Claims", "country": "US", "currency": "USD", "impact": "medium"},
    {"title": "AUD Employment Change", "country": "AU", "currency": "AUD", "impact": "high"},
    {"title": "RBA Interest Rate Decision", "country": "AU", "currency": "AUD", "impact": "high"},
    {"title": "US ISM Manufacturing PMI", "country": "US", "currency": "USD", "impact": "medium"},
    {"title": "Eurozone CPI y/y", "country": "EU", "currency": "EUR", "impact": "high"},
    {"title": "US GDP q/q", "country": "US", "currency": "USD", "impact": "high"},
]


class MockEconomicCalendar:
    """Generates deterministic mock calendar events (not real market data)."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = np.random.default_rng(seed)

    def fetch_events(self, days_ahead: int = 7, days_back: int = 1) -> list[dict]:
        now = datetime.now(UTC)
        events: list[dict] = []
        total_days = days_back + days_ahead

        for day_offset in range(-days_back, days_ahead):
            day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            # 2-4 events per day
            count = int(self._rng.integers(2, 5))
            chosen = self._rng.choice(len(EVENT_TEMPLATES), size=count, replace=False)

            for idx in chosen:
                template = EVENT_TEMPLATES[int(idx)]
                hour = int(self._rng.integers(8, 18))
                minute = int(self._rng.choice([0, 15, 30, 45]))
                event_time = day.replace(hour=hour, minute=minute)

                event_id = f"mock-{template['currency']}-{event_time.strftime('%Y%m%d%H%M')}-{template['title'][:20].replace(' ', '-')}"

                forecast = f"{self._rng.uniform(-2, 5):.1f}%"
                previous = f"{self._rng.uniform(-2, 5):.1f}%"

                events.append({
                    "event_id": event_id,
                    "title": template["title"],
                    "country": template["country"],
                    "currency": template["currency"],
                    "impact": template["impact"],
                    "event_time": event_time,
                    "forecast": forecast,
                    "previous": previous,
                    "actual": None,
                })

        events.sort(key=lambda e: e["event_time"])
        return events
