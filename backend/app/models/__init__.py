"""Import all models so Alembic and SQLAlchemy can discover them."""

from app.models.user import User
from app.models.account import TradingAccount
from app.models.strategy import Strategy
from app.models.trade import Order, Trade, TradeJournal
from app.models.ai import AIAnalysis, Report
from app.models.settings import Notification, UserSettings
from app.models.market import BacktestRun, EconomicEvent, MarketScan
from app.models.auto_trading import AutoTradingConfig

__all__ = [
    "User",
    "TradingAccount",
    "Strategy",
    "Trade",
    "Order",
    "TradeJournal",
    "AIAnalysis",
    "Report",
    "UserSettings",
    "Notification",
    "BacktestRun",
    "MarketScan",
    "EconomicEvent",
    "AutoTradingConfig",
]
