"""Shared FastAPI dependencies (DB session, pagination, request metadata)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.schemas.common import PaginationParams

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def client_ip(request: Request) -> str:
    """Best-effort client IP.

    ``X-Forwarded-For`` is only trusted when the app is behind a configured
    proxy, otherwise a client could spoof the first hop and defeat IP rate
    limits and the audit trail.
    """
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


def user_agent(request: Request) -> str | None:
    return (request.headers.get("user-agent") or "")[:400] or None


def pagination(
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    search: Annotated[str | None, Query(max_length=120)] = None,
    sort: Annotated[str | None, Query(max_length=40)] = None,
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size, search=search, sort=sort)


PaginationDep = Annotated[PaginationParams, Depends(pagination)]
