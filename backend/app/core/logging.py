"""Structured logging configuration for all application operations."""

import logging
import sys
from pathlib import Path

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure application-wide logging with consistent formatting."""
    settings = get_settings()

    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    # Ensure log directory exists for file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
    ]

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers,
        force=True,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a module."""
    return logging.getLogger(name)
