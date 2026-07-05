"""MT5 connection manager — singleton provider lifecycle."""

import sys

from app.core.config import get_settings
from app.core.logging import get_logger
from app.trading.mock_provider import MockMT5Provider
from app.trading.mt5_provider import RealMT5Provider
from app.trading.provider import MT5Provider
from app.trading.types import ConnectionStatus

logger = get_logger(__name__)

_provider: MT5Provider | None = None


def _create_provider() -> MT5Provider:
    """Select mock or real provider based on platform and config."""
    settings = get_settings()
    use_mock = settings.mt5_use_mock or sys.platform != "win32"

    if use_mock:
        logger.info("Using Mock MT5 provider (development mode)")
        return MockMT5Provider()

    logger.info("Using Real MT5 provider (Windows)")
    return RealMT5Provider()


def get_provider() -> MT5Provider:
    """Return the global MT5 provider instance."""
    global _provider
    if _provider is None:
        _provider = _create_provider()
    return _provider


def reset_provider() -> None:
    """Reset provider (for tests)."""
    global _provider
    if _provider is not None:
        try:
            _provider.disconnect()
        except Exception:
            pass
    _provider = None


def auto_connect() -> ConnectionStatus:
    """Connect on startup using env credentials if available."""
    settings = get_settings()
    provider = get_provider()

    if provider.get_status().connected:
        return provider.get_status()

    return provider.connect(
        login=settings.mt5_login,
        password=settings.mt5_password,
        server=settings.mt5_server,
        path=settings.mt5_path,
    )


def shutdown() -> None:
    """Disconnect on application shutdown."""
    global _provider
    if _provider is not None:
        _provider.disconnect()
        _provider = None
