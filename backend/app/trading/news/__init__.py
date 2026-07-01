"""Economic calendar provider."""

from app.trading.news.mock_calendar import MockEconomicCalendar

__all__ = ["MockEconomicCalendar", "get_calendar_provider"]


def get_calendar_provider() -> MockEconomicCalendar:
    return MockEconomicCalendar()
