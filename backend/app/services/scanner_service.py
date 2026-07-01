"""Market scanner service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketScan
from app.models.user import User
from app.repositories.scanner_repository import ScannerRepository
from app.services.risk_service import RiskService
from app.trading.constants import DEFAULT_SYMBOLS
from app.trading.scanner.engine import MarketScanner
from app.trading.types import Timeframe


class ScannerService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._scanner = MarketScanner()
        self._repo = ScannerRepository(session)
        self._risk = RiskService(session)

    async def _owner_id(self) -> int:
        result = await self._session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Owner not found")
        return user.id

    async def _resolve_symbols(self, symbols: list[str] | None) -> list[str]:
        if symbols:
            return [s.upper() for s in symbols]
        settings = await self._risk.get_settings()
        watchlist = settings.watchlist_symbols
        if isinstance(watchlist, list) and watchlist:
            return [s.upper() for s in watchlist]
        return list(DEFAULT_SYMBOLS)

    async def run_scan(
        self,
        symbols: list[str] | None = None,
        timeframe: Timeframe = Timeframe.H1,
        strategy_type: str = "ema_cross",
        scan_type: str = "full",
        save: bool = True,
    ) -> dict[str, Any]:
        user_id = await self._owner_id()
        symbol_list = await self._resolve_symbols(symbols)
        results = self._scanner.scan_many(symbol_list, timeframe, strategy_type)

        summary = {
            "total": len(results),
            "buy_signals": len([r for r in results if r.get("signal") == "buy"]),
            "sell_signals": len([r for r in results if r.get("signal") == "sell"]),
            "top_symbol": results[0]["symbol"] if results else None,
            "top_score": results[0].get("score", 0) if results else 0,
        }

        scan_id = None
        if save:
            scan = MarketScan(
                user_id=user_id,
                symbols={"list": symbol_list},
                results={
                    "items": results,
                    "summary": summary,
                    "timeframe": timeframe.value,
                    "strategy_type": strategy_type,
                },
                scan_type=scan_type,
            )
            saved = await self._repo.create(scan)
            scan_id = saved.id

        return {
            "id": scan_id,
            "scan_type": scan_type,
            "timeframe": timeframe.value,
            "strategy_type": strategy_type,
            "symbols": symbol_list,
            "results": results,
            "summary": summary,
        }

    async def list_scans(self, limit: int = 20) -> list[dict[str, Any]]:
        user_id = await self._owner_id()
        scans = await self._repo.list_scans(user_id, limit)
        return [self._scan_summary(s) for s in scans]

    async def get_scan(self, scan_id: int) -> dict[str, Any]:
        user_id = await self._owner_id()
        scan = await self._repo.get_by_id(scan_id, user_id)
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        return self._scan_detail(scan)

    def _scan_summary(self, scan: MarketScan) -> dict[str, Any]:
        summary = (scan.results or {}).get("summary", {})
        symbols = scan.symbols.get("list", []) if isinstance(scan.symbols, dict) else []
        return {
            "id": scan.id,
            "scan_type": scan.scan_type,
            "symbol_count": len(symbols),
            "summary": summary,
            "created_at": scan.created_at.isoformat(),
        }

    def _scan_detail(self, scan: MarketScan) -> dict[str, Any]:
        results = scan.results or {}
        symbols = scan.symbols.get("list", []) if isinstance(scan.symbols, dict) else []
        return {
            "id": scan.id,
            "scan_type": scan.scan_type,
            "timeframe": results.get("timeframe", "H1"),
            "strategy_type": results.get("strategy_type", "ema_cross"),
            "symbols": symbols,
            "results": results.get("items", []),
            "summary": results.get("summary", {}),
            "created_at": scan.created_at.isoformat(),
        }
