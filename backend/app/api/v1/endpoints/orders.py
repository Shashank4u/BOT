"""Order execution and trade management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.core.exceptions import AppException, RiskViolationError
from app.schemas.orders import (
    CloseOrderRequest,
    MarketOrderRequest,
    OrderResultSchema,
    PositionSchema,
    TradeResponseSchema,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(db)


OrderSvc = Annotated[OrderService, Depends(get_order_service)]


@router.post("/market", response_model=OrderResultSchema)
async def place_market_order(body: MarketOrderRequest, svc: OrderSvc) -> OrderResultSchema:
    """
    Place a market buy/sell order.
    Runs risk checks unless skip_risk_check=true.
  Records order and trade in database.
    """
    try:
        result = await svc.place_market_order(body.model_dump())
        await svc._session.commit()
    except RiskViolationError as exc:
        raise HTTPException(status_code=403, detail=exc.message) from exc
    except AppException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderResultSchema(**result)


@router.get("/trades", response_model=list[TradeResponseSchema])
async def list_trades(
    svc: OrderSvc, status: str | None = None
) -> list[TradeResponseSchema]:
    trades = await svc.list_trades(status)
    return [
        TradeResponseSchema(
            id=t.id,
            symbol=t.symbol,
            direction=t.direction,
            status=t.status,
            lot_size=float(t.lot_size),
            entry_price=float(t.entry_price),
            exit_price=float(t.exit_price) if t.exit_price else None,
            stop_loss=float(t.stop_loss) if t.stop_loss else None,
            take_profit=float(t.take_profit) if t.take_profit else None,
            profit_loss=float(t.profit_loss) if t.profit_loss else None,
            opened_at=t.opened_at,
            closed_at=t.closed_at,
            entry_reason=t.entry_reason,
            exit_reason=t.exit_reason,
            strategy_id=t.strategy_id,
            mt5_ticket=t.mt5_ticket,
        )
        for t in trades
    ]


@router.get("/positions", response_model=list[PositionSchema])
async def list_positions(svc: OrderSvc) -> list[PositionSchema]:
    positions = await svc.get_positions()
    return [
        PositionSchema(
            ticket=p.ticket,
            symbol=p.symbol,
            side=p.side,
            lot_size=p.lot_size,
            open_price=p.open_price,
            current_price=p.current_price,
            stop_loss=p.stop_loss,
            take_profit=p.take_profit,
            profit=p.profit,
            magic_number=p.magic_number,
        )
        for p in positions
    ]


@router.post("/trades/{trade_id}/close", response_model=OrderResultSchema)
async def close_trade(
    trade_id: int, body: CloseOrderRequest, svc: OrderSvc
) -> OrderResultSchema:
    try:
        result = await svc.close_trade(trade_id, body.model_dump())
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OrderResultSchema(**result)
