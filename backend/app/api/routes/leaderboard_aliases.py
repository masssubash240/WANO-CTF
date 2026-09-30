"""Spec-compatibility alias for leaderboard."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.api.routes.scoreboard import read_scoreboard
from app.schemas.scoreboard import ScoreboardResponse
from app.security.deps import OptionalPrincipalDep

router = APIRouter(prefix="/leaderboard", tags=["scoreboard"])


@router.get("", response_model=ScoreboardResponse)
async def get_leaderboard_alias(
    principal: OptionalPrincipalDep,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> ScoreboardResponse:
    return await read_scoreboard(principal=principal, session=session, limit=limit)
