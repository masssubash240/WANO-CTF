"""Shared schema helpers: envelopes, pagination, base model config."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

#: Every ORM-object schema inherits this to allow ``model_validate(orm_obj)``.
ORMBaseConfig = ConfigDict(from_attributes=True, populate_by_name=True, str_strip_whitespace=True)


class ORMModel(BaseModel):
    model_config = ORMBaseConfig


class Message(BaseModel):
    """Generic acknowledgement payload."""

    message: str
    code: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    """Error contract shared by every endpoint (see app.errors)."""

    error: ErrorDetail


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1, le=10_000)] = 1
    page_size: Annotated[int, Field(ge=1, le=200)] = 50
    search: Annotated[str | None, Field(max_length=120)] = None
    sort: Annotated[str | None, Field(max_length=40)] = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def build(cls, items: list[T], *, total: int, params: PaginationParams) -> Page[T]:
        total_pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1,
        )


class TimestampedModel(ORMModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


def normalize_email(value: str) -> str:
    return value.strip().lower()
