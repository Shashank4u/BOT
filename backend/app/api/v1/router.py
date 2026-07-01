"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    analytics,
    backtest,
    dashboard,
    health,
    indicators,
    journal,
    market,
    news,
    notifications,
    orders,
    patterns,
    risk,
    scanner,
    strategies,
    telegram,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(market.router)
api_router.include_router(dashboard.router)
api_router.include_router(indicators.router)
api_router.include_router(patterns.router)
api_router.include_router(strategies.router)
api_router.include_router(risk.router)
api_router.include_router(orders.router)
api_router.include_router(journal.router)
api_router.include_router(ai.router)
api_router.include_router(backtest.router)
api_router.include_router(scanner.router)
api_router.include_router(news.router)
api_router.include_router(analytics.router)
api_router.include_router(telegram.router)
api_router.include_router(notifications.router)
