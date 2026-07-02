"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import APIKeyMiddleware
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.services.bootstrap import ensure_default_owner
from app.trading.auto_trader_runner import auto_trader_runner
from app.trading.connection import auto_connect, shutdown
import app.models  # noqa: F401 — register all models with SQLAlchemy

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting %s v%s [%s] — trading_mode=%s",
        settings.app_name,
        settings.app_version,
        settings.environment,
        settings.trading_mode.value,
    )

    if settings.is_demo_mode:
        logger.warning(
            "DEMO MODE ACTIVE — live trading is disabled until explicitly confirmed."
        )

    # Initialize database tables and default owner
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await ensure_default_owner(session)
    logger.info("Database ready — single owner bootstrapped")

    # Auto-connect to MT5 (mock on macOS/Linux, real on Windows with credentials)
    try:
        status = auto_connect()
        logger.info("MT5: %s", status.message)
    except Exception as exc:
        logger.warning("MT5 auto-connect skipped: %s", exc)

    await auto_trader_runner.start()

    yield

    await auto_trader_runner.stop()
    shutdown()
    await engine.dispose()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Application factory for FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "AI Trading Assistant API — single-user, no login. "
            "Analyzes markets, executes user-defined strategies, manages risk. "
            "Does NOT predict markets or guarantee profits."
        ),
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(APIKeyMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "mode": "single-user",
            "disclaimer": (
                "This software does not guarantee profits. "
                "Trading involves substantial risk of loss."
            ),
        }

    return app


app = create_app()
