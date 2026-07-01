"""Application configuration loaded from environment variables."""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(str, Enum):
    """Trading execution mode — defaults to DEMO for safety."""

    DEMO = "demo"
    LIVE = "live"


class Settings(BaseSettings):
    """Centralized application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Trading Assistant"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security (optional API key for VPS — no login UI)
    api_key: str | None = None
    secret_key: str = Field(
        default="CHANGE-ME-in-production-use-openssl-rand-hex-32",
        min_length=32,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/trading_assistant.db"
    database_echo: bool = False

    # PostgreSQL (production override)
    postgres_host: str | None = None
    postgres_port: int = 5432
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Trading — ALWAYS defaults to DEMO
    trading_mode: TradingMode = TradingMode.DEMO
    mt5_login: int | None = None
    mt5_password: str | None = None
    mt5_server: str = "XMGlobal-MT5"
    mt5_path: str | None = None  # Path to terminal64.exe on Windows
    mt5_use_mock: bool = True  # Use mock MT5 when real terminal unavailable

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Telegram
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # Email (optional notifications)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str = "noreply@trading-assistant.local"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_demo_mode(self) -> bool:
        """Trading is restricted to demo unless explicitly configured for live."""
        return self.trading_mode == TradingMode.DEMO

    @property
    def effective_database_url(self) -> str:
        """Resolve database URL — PostgreSQL in production, SQLite in dev."""
        if self.postgres_host and self.postgres_user and self.postgres_db:
            password = self.postgres_password or ""
            return str(
                PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=self.postgres_user,
                    password=password,
                    host=self.postgres_host,
                    port=self.postgres_port,
                    path=self.postgres_db,
                )
            )
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
