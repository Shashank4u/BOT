"""Backtesting domain types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BacktestTrade:
    """Single simulated trade from a backtest run."""

    direction: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    lot_size: float
    profit_loss: float
    exit_reason: str
    stop_loss: float | None = None
    take_profit: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "entry_price": round(self.entry_price, 6),
            "exit_price": round(self.exit_price, 6),
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "lot_size": self.lot_size,
            "profit_loss": round(self.profit_loss, 2),
            "exit_reason": self.exit_reason,
            "stop_loss": round(self.stop_loss, 6) if self.stop_loss else None,
            "take_profit": round(self.take_profit, 6) if self.take_profit else None,
        }


@dataclass
class BacktestMetrics:
    """Aggregated backtest performance metrics."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    profit_factor: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float = 0.0
    expectancy: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    final_balance: float = 0.0
    return_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(self.win_rate, 2),
            "total_pnl": round(self.total_pnl, 2),
            "profit_factor": round(self.profit_factor, 4) if self.profit_factor is not None else None,
            "sharpe_ratio": round(self.sharpe_ratio, 4) if self.sharpe_ratio is not None else None,
            "max_drawdown": round(self.max_drawdown, 4),
            "expectancy": round(self.expectancy, 4),
            "average_win": round(self.average_win, 2),
            "average_loss": round(self.average_loss, 2),
            "final_balance": round(self.final_balance, 2),
            "return_percent": round(self.return_percent, 2),
        }


@dataclass
class BacktestResult:
    """Complete backtest output."""

    symbol: str
    timeframe: str
    initial_balance: float
    start_date: datetime
    end_date: datetime
    metrics: BacktestMetrics
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "initial_balance": self.initial_balance,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "metrics": self.metrics.to_dict(),
            "trades": [t.to_dict() for t in self.trades],
            "equity_curve": self.equity_curve,
            "disclaimer": (
                "Backtest results are based on historical/simulated data. "
                "Past performance does not guarantee future results."
            ),
        }
