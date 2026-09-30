"""Spec-compatibility aliases: GET /auth/me.

Canonical auth lives in ``auth.py``; this module only adds the
``GET /api/auth/me`` alias expected by the public API contract.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep
from app.schemas.profile import SessionResponse
from app.security.deps import Principal, get_active_principal

router = APIRouter(prefix="/auth", tags=["auth"])
ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]


@router.get("/me", response_model=SessionResponse, include_in_schema=False)
async def read_auth_me(principal: ActivePrincipal, session: SessionDep) -> SessionResponse:
    from app.api.routes.users import read_session

    return await read_session(principal, session)
