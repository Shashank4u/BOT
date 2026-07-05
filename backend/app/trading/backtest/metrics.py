"""Backtest performance metrics."""

import math
from statistics import mean, stdev

from app.trading.backtest.types import BacktestMetrics, BacktestTrade


def calculate_trade_pnl(
    symbol: str,
    direction: str,
    entry_price: float,
    exit_price: float,
    lot_size: float,
) -> float:
    """Approximate P/L in account currency using pip value."""
    from app.trading.risk.calculator import pip_size, pip_value_per_lot

    pip = pip_size(symbol)
    pv = pip_value_per_lot(symbol, entry_price)
    if direction == "buy":
        pips = (exit_price - entry_price) / pip
    else:
        pips = (entry_price - exit_price) / pip
    return round(pips * pv * lot_size, 2)


def compute_metrics(
    trades: list[BacktestTrade],
    equity_curve: list[dict],
    initial_balance: float,
) -> BacktestMetrics:
    """Compute profit factor, Sharpe, drawdown, expectancy, and related stats."""
    if not trades:
        final = equity_curve[-1]["equity"] if equity_curve else initial_balance
        return BacktestMetrics(
            final_balance=final,
            return_percent=round((final - initial_balance) / initial_balance * 100, 2),
        )

    wins = [t for t in trades if t.profit_loss > 0]
    losses = [t for t in trades if t.profit_loss < 0]
    gross_profit = sum(t.profit_loss for t in wins)
    gross_loss = abs(sum(t.profit_loss for t in losses))
    total_pnl = sum(t.profit_loss for t in trades)

    profit_factor = round(gross_profit / gross_loss, 4) if gross_loss > 0 else None

    avg_win = mean([t.profit_loss for t in wins]) if wins else 0.0
    avg_loss = mean([t.profit_loss for t in losses]) if losses else 0.0
    win_rate = len(wins) / len(trades) * 100
    loss_rate = len(losses) / len(trades)
    expectancy = (len(wins) / len(trades) * avg_win) + (loss_rate * avg_loss)

    sharpe = _sharpe_ratio(trades, initial_balance)
    max_dd = _max_drawdown(equity_curve, initial_balance)

    final_balance = equity_curve[-1]["equity"] if equity_curve else initial_balance + total_pnl

    return BacktestMetrics(
        total_trades=len(trades),
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=win_rate,
        total_pnl=total_pnl,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        expectancy=expectancy,
        average_win=avg_win,
        average_loss=avg_loss,
        final_balance=final_balance,
        return_percent=round((final_balance - initial_balance) / initial_balance * 100, 2),
    )


def _sharpe_ratio(trades: list[BacktestTrade], initial_balance: float) -> float | None:
    if len(trades) < 2:
        return None

    balance = initial_balance
    returns: list[float] = []
    for trade in trades:
        if balance <= 0:
            break
        returns.append(trade.profit_loss / balance)
        balance += trade.profit_loss

    if len(returns) < 2:
        return None

    std = stdev(returns)
    if std == 0:
        return None

    return round(mean(returns) / std * math.sqrt(252), 4)


def _max_drawdown(equity_curve: list[dict], initial_balance: float) -> float:
    if not equity_curve:
        return 0.0

    peak = initial_balance
    max_dd = 0.0
    for point in equity_curve:
        equity = point["equity"]
        peak = max(peak, equity)
        if peak > 0:
            dd = (peak - equity) / peak * 100
            max_dd = max(max_dd, dd)
    return round(max_dd, 4)
