"""Risk management API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.risk import (
    ConfirmLiveResponse,
    LotSizeRequest,
    LotSizeResponse,
    MarginRequest,
    MarginResponse,
    RiskCheckRequest,
    RiskCheckResponse,
    RiskRewardRequest,
    RiskRewardResponse,
    RiskSettingsResponse,
    RiskSettingsUpdate,
)
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Risk Management"])


def get_risk_service(db: DbSession) -> RiskService:
    return RiskService(db)


RiskSvc = Annotated[RiskService, Depends(get_risk_service)]


@router.get("/settings", response_model=RiskSettingsResponse)
async def get_risk_settings(svc: RiskSvc) -> RiskSettingsResponse:
    settings = await svc.get_settings()
    return RiskSettingsResponse(**svc.settings_response(settings))


@router.patch("/settings", response_model=RiskSettingsResponse)
async def update_risk_settings(
    body: RiskSettingsUpdate, svc: RiskSvc
) -> RiskSettingsResponse:
    settings = await svc.update_settings(body.model_dump(exclude_unset=True))
    await svc._session.commit()
    return RiskSettingsResponse(**svc.settings_response(settings))


@router.get("/status")
async def risk_status(svc: RiskSvc) -> dict:
    """Current risk exposure: P&L, open trades, limits remaining."""
    return await svc.get_status()


@router.post("/calculate-lot-size", response_model=LotSizeResponse)
async def calculate_lot_size(body: LotSizeRequest) -> LotSizeResponse:
    from app.trading.risk.calculator import calculate_lot_size as calc

    result = calc(body.balance, body.risk_percent, body.stop_loss_pips, body.symbol)
    return LotSizeResponse(
        lot_size=result.lot_size,
        risk_amount=result.risk_amount,
        risk_percent=result.risk_percent,
        stop_loss_pips=result.stop_loss_pips,
        pip_value=result.pip_value,
        symbol=result.symbol,
    )


@router.post("/calculate-rr", response_model=RiskRewardResponse)
async def calculate_risk_reward(body: RiskRewardRequest) -> RiskRewardResponse:
    from app.trading.risk.calculator import calculate_risk_reward as calc

    result = calc(body.entry_price, body.stop_loss, body.take_profit, body.symbol, body.side)
    return RiskRewardResponse(
        risk_pips=result.risk_pips,
        reward_pips=result.reward_pips,
        risk_reward_ratio=result.risk_reward_ratio,
        entry_price=result.entry_price,
        stop_loss=result.stop_loss,
        take_profit=result.take_profit,
    )


@router.post("/calculate-margin", response_model=MarginResponse)
async def calculate_margin(body: MarginRequest) -> MarginResponse:
    from app.trading.risk.calculator import calculate_margin as calc

    result = calc(body.lot_size, body.symbol, body.price, body.leverage, body.free_margin)
    return MarginResponse(
        required_margin=result.required_margin,
        free_margin=result.free_margin,
        margin_level_after=result.margin_level_after,
        lot_size=result.lot_size,
        leverage=result.leverage,
        symbol=result.symbol,
    )


@router.post("/check", response_model=RiskCheckResponse)
async def check_trade_risk(body: RiskCheckRequest, svc: RiskSvc) -> RiskCheckResponse:
    """Validate a proposed trade against all risk limits."""
    result = await svc.check_trade(
        body.symbol, body.lot_size, body.stop_loss_pips, body.balance
    )
    return RiskCheckResponse(**result.to_dict())


@router.post("/confirm-live", response_model=ConfirmLiveResponse)
async def confirm_live_trading(svc: RiskSvc) -> ConfirmLiveResponse:
    """
    Explicitly confirm live trading. Required before real-money orders when TRADING_MODE=live.
    """
    if get_settings().is_demo_mode:
        return ConfirmLiveResponse(
            live_trading_confirmed=False,
            message="App is in DEMO mode. Set TRADING_MODE=live in .env to enable live trading.",
            warning="No real money will be used in DEMO mode.",
        )
    await svc.confirm_live_trading()
    await svc._session.commit()
    return ConfirmLiveResponse(
        live_trading_confirmed=True,
        message="Live trading confirmed. You accept all trading risks.",
        warning=(
            "Real money is at risk. This app does not guarantee profits. "
            "Only trade what you can afford to lose."
        ),
    )
