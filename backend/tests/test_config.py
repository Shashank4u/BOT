"""Configuration module unit tests."""

from app.core.config import Settings, TradingMode, get_settings


def test_default_trading_mode_is_demo() -> None:
    settings = Settings()
    assert settings.trading_mode == TradingMode.DEMO
    assert settings.is_demo_mode is True


def test_settings_singleton() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_effective_database_url_sqlite_by_default() -> None:
    settings = Settings()
    assert "sqlite" in settings.effective_database_url


def test_cors_origins_parsed_from_string() -> None:
    settings = Settings(cors_origins="http://a.com, http://b.com")
    assert settings.cors_origins == ["http://a.com", "http://b.com"]
