"""Background auto-trading loop."""

import asyncio
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.services.auto_trader_service import AutoTraderService

logger = get_logger(__name__)


class AutoTraderRunner:
    """Runs periodic strategy scans when auto-trading is enabled."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop(), name="auto-trader")
        logger.info("Auto-trader background loop started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Auto-trader background loop stopped")

    async def run_once(self) -> list:
        """Manual scan trigger (also used by API)."""
        async with AsyncSessionLocal() as session:
            svc = AutoTraderService(session)
            results = await svc.run_scan()
            await session.commit()
            return [r.to_dict() for r in results]

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            interval = 300
            try:
                async with AsyncSessionLocal() as session:
                    svc = AutoTraderService(session)
                    config = await svc.get_config()
                    interval = max(60, config.interval_seconds)

                    if config.enabled:
                        await svc.run_scan()
                        await session.commit()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Auto-trader scan error: %s", exc)
                try:
                    async with AsyncSessionLocal() as session:
                        svc = AutoTraderService(session)
                        config = await svc.get_config()
                        config.last_error = str(exc)[:500]
                        config.last_scan_at = datetime.now(UTC)
                        await session.commit()
                except Exception:
                    pass

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
                break
            except asyncio.TimeoutError:
                continue


auto_trader_runner = AutoTraderRunner()
