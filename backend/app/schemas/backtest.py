"""Backtest request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.trading.types import Timeframe


class BacktestRunRequest(BaseModel):
    strategy_id: int | None = None
    strategy_type: str | None = None
    symbol: str = "EURUSD"
    timeframe: Timeframe = Timeframe.H1
    bar_count: int = Field(default=500, ge=110, le=5000)
    initial_balance: float = Field(default=10000.0, ge=100, le=10_000_000)
    params: dict[str, Any] | None = None


class BacktestMetricsSchema(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    profit_factor: float | None
    sharpe_ratio: float | None
    max_drawdown: float
    expectancy: float
    average_win: float
    average_loss: float
    final_balance: float
    return_percent: float


class BacktestTradeSchema(BaseModel):
    direction: str
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    lot_size: float
    profit_loss: float
    exit_reason: str
    stop_loss: float | None = None
    take_profit: float | None = None


class BacktestRunResponse(BaseModel):
    id: int
    strategy_id: int | None
    strategy_name: str | None
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    metrics: BacktestMetricsSchema
    total_trades: int
    created_at: datetime


class BacktestDetailResponse(BacktestRunResponse):
    trades: list[BacktestTradeSchema]
    equity_curve: list[dict[str, Any]]
    results_json: dict[str, Any] | None
    disclaimer: str
