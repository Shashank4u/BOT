"""Trading performance analytics."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import TradingAccount
from app.models.user import User
from app.repositories.trade_repository import TradeRepository
from app.services.market_data import MarketDataService

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._trades = TradeRepository(session)
        self._market = MarketDataService()

    async def _account(self) -> TradingAccount:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        acc_result = await self._session.execute(
            select(TradingAccount).where(TradingAccount.user_id == user.id).limit(1)
        )
        account = acc_result.scalar_one_or_none()
        if not account:
            try:
                self._market._ensure_connected()
                bal = self._market.get_account().balance
            except Exception:
                bal = 10000.0

            class _FallbackAccount:
                id = 0

                def __init__(self, balance: float) -> None:
                    self.balance = balance

            return _FallbackAccount(bal)  # type: ignore[return-value]
        return account

    async def overview(self, days: int = 30) -> dict[str, Any]:
        account = await self._account()
        since = datetime.now(UTC) - timedelta(days=days)
        closed = await self._trades.list_closed_trades(account.id, since=since)

        wins = [t for t in closed if t.profit_loss and float(t.profit_loss) > 0]
        losses = [t for t in closed if t.profit_loss and float(t.profit_loss) < 0]
        total_pnl = sum(float(t.profit_loss or 0) for t in closed)

        try:
            self._market._ensure_connected()
            live_balance = self._market.get_account().balance
        except Exception:
            live_balance = float(account.balance)

        return {
            "period_days": days,
            "total_trades": len(closed),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(len(wins) / len(closed) * 100, 2) if closed else 0,
            "total_pnl": round(total_pnl, 2),
            "average_win": round(sum(float(t.profit_loss) for t in wins) / len(wins), 2) if wins else 0,
            "average_loss": round(sum(float(t.profit_loss) for t in losses) / len(losses), 2) if losses else 0,
            "best_trade": round(max((float(t.profit_loss) for t in closed), default=0), 2),
            "worst_trade": round(min((float(t.profit_loss) for t in closed), default=0), 2),
            "current_balance": round(live_balance, 2),
            "starting_balance": round(float(account.balance), 2),
        }

    async def equity_curve(self, days: int = 30) -> dict[str, Any]:
        account = await self._account()
        since = datetime.now(UTC) - timedelta(days=days)
        closed = await self._trades.list_closed_trades(account.id, since=since)

        running = float(account.balance) - sum(float(t.profit_loss or 0) for t in closed)

        points: list[dict[str, Any]] = [
            {"time": since.isoformat(), "equity": round(running, 2), "trade_id": None}
        ]
        for trade in closed:
            running += float(trade.profit_loss or 0)
            points.append({
                "time": trade.closed_at.isoformat() if trade.closed_at else "",
                "equity": round(running, 2),
                "trade_id": trade.id,
                "pnl": float(trade.profit_loss or 0),
            })

        if not closed:
            points.append({
                "time": datetime.now(UTC).isoformat(),
                "equity": round(float(account.balance), 2),
                "trade_id": None,
            })

        return {"days": days, "points": points}

    async def pnl_by_symbol(self, days: int = 30) -> dict[str, Any]:
        account = await self._account()
        since = datetime.now(UTC) - timedelta(days=days)
        closed = await self._trades.list_closed_trades(account.id, since=since)

        by_symbol: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"pnl": 0.0, "trades": 0, "wins": 0}
        )
        for trade in closed:
            s = by_symbol[trade.symbol]
            pnl = float(trade.profit_loss or 0)
            s["pnl"] = round(s["pnl"] + pnl, 2)
            s["trades"] += 1
            if pnl > 0:
                s["wins"] += 1

        items = [
            {
                "symbol": sym,
                "pnl": data["pnl"],
                "trades": data["trades"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 2) if data["trades"] else 0,
            }
            for sym, data in sorted(by_symbol.items(), key=lambda x: x[1]["pnl"], reverse=True)
        ]
        return {"days": days, "symbols": items}

    async def daily_pnl(self, days: int = 30) -> dict[str, Any]:
        account = await self._account()
        since = datetime.now(UTC) - timedelta(days=days)
        closed = await self._trades.list_closed_trades(account.id, since=since)

        daily: dict[str, float] = defaultdict(float)
        for trade in closed:
            if trade.closed_at:
                day = trade.closed_at.strftime("%Y-%m-%d")
                daily[day] += float(trade.profit_loss or 0)

        series = [
            {"date": day, "pnl": round(pnl, 2)}
            for day, pnl in sorted(daily.items())
        ]
        return {"days": days, "series": series}

    async def win_rate(self, days: int = 30) -> dict[str, Any]:
        overview = await self.overview(days)
        return {
            "days": days,
            "win_rate": overview["win_rate"],
            "winning_trades": overview["winning_trades"],
            "losing_trades": overview["losing_trades"],
            "total_trades": overview["total_trades"],
        }

    async def heatmap(self, days: int = 30) -> dict[str, Any]:
        """Session heatmap: day-of-week x hour-of-day aggregated P/L."""
        account = await self._account()
        since = datetime.now(UTC) - timedelta(days=days)
        closed = await self._trades.list_closed_trades(account.id, since=since)

        grid: dict[str, dict[str, float]] = {
            day: {str(h): 0.0 for h in range(24)} for day in DAY_NAMES
        }
        counts: dict[str, dict[str, int]] = {
            day: {str(h): 0 for h in range(24)} for day in DAY_NAMES
        }

        for trade in closed:
            if not trade.closed_at:
                continue
            day_name = DAY_NAMES[trade.closed_at.weekday()]
            hour = str(trade.closed_at.hour)
            pnl = float(trade.profit_loss or 0)
            grid[day_name][hour] = round(grid[day_name][hour] + pnl, 2)
            counts[day_name][hour] += 1

        cells = []
        for day in DAY_NAMES:
            for hour in range(24):
                h = str(hour)
                cells.append({
                    "day": day,
                    "hour": hour,
                    "pnl": grid[day][h],
                    "trades": counts[day][h],
                })

        symbol_pnl = await self.pnl_by_symbol(days)
        return {
            "days": days,
            "session_heatmap": cells,
            "symbol_performance": symbol_pnl["symbols"],
        }
