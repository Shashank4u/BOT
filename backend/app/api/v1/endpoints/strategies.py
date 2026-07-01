"""Strategy management and evaluation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.strategy import (
    EvaluateRequestSchema,
    SampleStrategySchema,
    SeedSamplesResponse,
    StrategyCreateSchema,
    StrategyResponseSchema,
    StrategySignalSchema,
    StrategyUpdateSchema,
)
from app.services.strategy_service import StrategyService, strategy_to_response
from app.trading.types import Timeframe

router = APIRouter(prefix="/strategies", tags=["Strategies"])


def get_strategy_service(db: DbSession) -> StrategyService:
    return StrategyService(db)


StrategySvc = Annotated[StrategyService, Depends(get_strategy_service)]


@router.get("/samples", response_model=list[SampleStrategySchema])
async def list_sample_templates(svc: StrategySvc) -> list[SampleStrategySchema]:
    """List built-in sample strategy templates (not yet saved to DB)."""
    return [SampleStrategySchema(**s) for s in svc.list_sample_templates()]


@router.get("/evaluate/{symbol}", response_model=StrategySignalSchema)
async def evaluate_by_type(
    symbol: str,
    svc: StrategySvc,
    strategy_type: str = Query(default="ema_cross"),
    timeframe: Timeframe = Timeframe.H1,
) -> StrategySignalSchema:
    """Evaluate a strategy type without saving it to the database."""
    try:
        signal = svc.evaluate_by_type(strategy_type, symbol, timeframe)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StrategySignalSchema(**signal.to_dict())


@router.post("/seed-samples", response_model=SeedSamplesResponse)
async def seed_sample_strategies(svc: StrategySvc) -> SeedSamplesResponse:
    """Load all 8 sample strategies into the database (skips duplicates)."""
    result = await svc.seed_samples()
    return SeedSamplesResponse(
        created=result["created"],
        skipped=result["skipped"],
        message=f"Created {result['created']} sample strategies, skipped {result['skipped']}",
    )


@router.get("", response_model=list[StrategyResponseSchema])
async def list_strategies(svc: StrategySvc) -> list[StrategyResponseSchema]:
    """List all saved strategies for the owner."""
    strategies = await svc.list_strategies()
    return [StrategyResponseSchema(**strategy_to_response(s)) for s in strategies]


@router.post("", response_model=StrategyResponseSchema, status_code=201)
async def create_strategy(
    body: StrategyCreateSchema, svc: StrategySvc
) -> StrategyResponseSchema:
    """Create a custom strategy."""
    try:
        strategy = await svc.create_strategy(body.model_dump())
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StrategyResponseSchema(**strategy_to_response(strategy))


@router.get("/{strategy_id}", response_model=StrategyResponseSchema)
async def get_strategy(strategy_id: int, svc: StrategySvc) -> StrategyResponseSchema:
    try:
        strategy = await svc.get_strategy(strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StrategyResponseSchema(**strategy_to_response(strategy))


@router.patch("/{strategy_id}", response_model=StrategyResponseSchema)
async def update_strategy(
    strategy_id: int, body: StrategyUpdateSchema, svc: StrategySvc
) -> StrategyResponseSchema:
    try:
        strategy = await svc.update_strategy(
            strategy_id, body.model_dump(exclude_unset=True)
        )
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StrategyResponseSchema(**strategy_to_response(strategy))


@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(strategy_id: int, svc: StrategySvc) -> None:
    try:
        await svc.delete_strategy(strategy_id)
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{strategy_id}/evaluate", response_model=StrategySignalSchema)
async def evaluate_saved_strategy(
    strategy_id: int,
    body: EvaluateRequestSchema,
    svc: StrategySvc,
) -> StrategySignalSchema:
    """
    Evaluate a saved strategy on a symbol.
    Returns buy/sell/hold with reasons — not a prediction.
    """
    try:
        signal = await svc.evaluate_strategy(
            strategy_id, body.symbol, body.timeframe
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StrategySignalSchema(**signal.to_dict())
