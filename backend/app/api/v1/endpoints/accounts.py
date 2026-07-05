"""Broker account management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.schemas.account import (
    BrokerAccountConnectResponseSchema,
    BrokerAccountCreateSchema,
    BrokerAccountResponseSchema,
)
from app.schemas.market import ConnectionStatusSchema
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Broker Accounts"])


def get_account_service(db: DbSession) -> AccountService:
    return AccountService(db)


AccountSvc = Annotated[AccountService, Depends(get_account_service)]


@router.get("", response_model=list[BrokerAccountResponseSchema])
async def list_broker_accounts(svc: AccountSvc) -> list[BrokerAccountResponseSchema]:
    """List saved broker accounts (passwords are never returned)."""
    return [BrokerAccountResponseSchema(**a) for a in await svc.list_accounts()]


@router.get("/active", response_model=BrokerAccountResponseSchema | None)
async def get_active_broker_account(svc: AccountSvc) -> BrokerAccountResponseSchema | None:
    """Get the currently active broker account."""
    account = await svc.get_active_account()
    return BrokerAccountResponseSchema(**account) if account else None


@router.post("", response_model=BrokerAccountConnectResponseSchema, status_code=201)
async def add_broker_account(
    body: BrokerAccountCreateSchema, svc: AccountSvc
) -> BrokerAccountConnectResponseSchema:
    """
    Add a broker account and connect to MT5.
    On macOS/Linux this uses the mock provider for development.
    On Windows with MT5_USE_MOCK=false, connects to the real terminal.
    """
    try:
        result = await svc.add_and_connect(body.model_dump())
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BrokerAccountConnectResponseSchema(
        account=BrokerAccountResponseSchema(**result["account"]),
        connection=ConnectionStatusSchema.model_validate(result["connection"]),
        message=result["message"],
    )


@router.post("/{account_id}/connect", response_model=BrokerAccountConnectResponseSchema)
async def connect_broker_account(
    account_id: int, svc: AccountSvc
) -> BrokerAccountConnectResponseSchema:
    """Reconnect using stored credentials."""
    try:
        result = await svc.connect_account(account_id)
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BrokerAccountConnectResponseSchema(
        account=BrokerAccountResponseSchema(**result["account"]),
        connection=ConnectionStatusSchema.model_validate(result["connection"]),
        message=result["message"],
    )


@router.post("/disconnect")
async def disconnect_broker(svc: AccountSvc) -> dict:
    """Disconnect from MT5."""
    result = await svc.disconnect_active()
    await svc._session.commit()
    return {
        "connection": ConnectionStatusSchema.model_validate(result["connection"]),
        "message": result["message"],
    }


@router.delete("/{account_id}", status_code=204)
async def delete_broker_account(account_id: int, svc: AccountSvc) -> None:
    """Remove a saved broker account."""
    try:
        await svc.delete_account(account_id)
        await svc._session.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
