"""Analytics API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class AnalyticsOverviewSchema(BaseModel):
    period_days: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_win: float
    average_loss: float
    best_trade: float
    worst_trade: float
    current_balance: float
    starting_balance: float


class EquityPointSchema(BaseModel):
    time: str
    equity: float
    trade_id: int | None = None
    pnl: float | None = None


class EquityCurveSchema(BaseModel):
    days: int
    points: list[EquityPointSchema]


class SymbolPnlSchema(BaseModel):
    symbol: str
    pnl: float
    trades: int
    win_rate: float


class PnlBySymbolSchema(BaseModel):
    days: int
    symbols: list[SymbolPnlSchema]


class DailyPnlPointSchema(BaseModel):
    date: str
    pnl: float


class DailyPnlSchema(BaseModel):
    days: int
    series: list[DailyPnlPointSchema]


class WinRateSchema(BaseModel):
    days: int
    win_rate: float
    winning_trades: int
    losing_trades: int
    total_trades: int


class HeatmapCellSchema(BaseModel):
    day: str
    hour: int
    pnl: float
    trades: int


class HeatmapSchema(BaseModel):
    days: int
    session_heatmap: list[HeatmapCellSchema]
    symbol_performance: list[SymbolPnlSchema]
