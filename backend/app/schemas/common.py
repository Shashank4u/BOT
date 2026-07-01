"""Common schema types used across API responses."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic model with ORM mode enabled."""

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseSchema):
    message: str
    success: bool = True


class PaginatedResponse(BaseSchema, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    pages: int


class HealthResponse(BaseSchema):
    status: str
    version: str
    environment: str
    trading_mode: str
    database: str
    disclaimer: str = (
        "This application does not predict markets or guarantee profits. "
        "All trading involves risk. Past performance is not indicative of future results."
    )
