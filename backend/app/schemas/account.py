"""Broker account API schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.market import ConnectionStatusSchema


class BrokerAccountCreateSchema(BaseSchema):
    name: str = Field(default="XM Account", min_length=1, max_length=100)
    broker: str = Field(default="XM", max_length=50)
    account_type: str = Field(default="demo", pattern="^(demo|live)$")
    mt5_login: int = Field(gt=0)
    mt5_password: str = Field(min_length=1)
    mt5_server: str = Field(min_length=1, max_length=100)


class BrokerAccountResponseSchema(BaseSchema):
    id: int
    name: str
    broker: str
    account_type: str
    mt5_login: int
    mt5_server: str
    currency: str
    leverage: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    is_active: bool
    is_connected: bool
    created_at: datetime | None = None


class BrokerAccountConnectResponseSchema(BaseSchema):
    account: BrokerAccountResponseSchema
    connection: ConnectionStatusSchema
    message: str
