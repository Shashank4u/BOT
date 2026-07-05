"""Order execution with retry logic."""

import time

from app.core.logging import get_logger
from app.trading.connection import get_provider
from app.trading.types import OrderRequest, OrderResult

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_SEC = 0.5


class OrderExecutor:
    """Execute orders via MT5 provider with retry on failure."""

    def place_market(self, request: OrderRequest) -> OrderResult:
        return self._with_retry(lambda: get_provider().place_market_order(request))

    def place_pending(self, request: OrderRequest) -> OrderResult:
        return self._with_retry(lambda: get_provider().place_pending_order(request))

    def close(self, ticket: int, lot_size: float | None = None) -> OrderResult:
        return self._with_retry(lambda: get_provider().close_position(ticket, lot_size))

    def modify(
        self, ticket: int, stop_loss: float | None, take_profit: float | None
    ) -> OrderResult:
        return self._with_retry(
            lambda: get_provider().modify_position(ticket, stop_loss, take_profit)
        )

    def _with_retry(self, fn) -> OrderResult:
        last_result: OrderResult | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = fn()
                if result.success:
                    return result
                last_result = result
                logger.warning("Order attempt %d failed: %s", attempt, result.message)
            except Exception as exc:
                logger.warning("Order attempt %d exception: %s", attempt, exc)
                last_result = OrderResult(
                    success=False, ticket=None, symbol="", side="", lot_size=0, price=0,
                    stop_loss=None, take_profit=None, message=str(exc), is_demo=True,
                )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
        return last_result  # type: ignore[return-value]
