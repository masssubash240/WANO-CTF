"""Public scoreboard and results endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep
from app.schemas.scoreboard import ResultsResponse, ScoreboardResponse
from app.security.deps import Principal, get_principal_optional
from app.services.competition import compute_state, get_settings_row
from app.services.scoreboard import build_results, build_scoreboard, team_results

router = APIRouter(prefix="/scoreboard", tags=["scoreboard"])

OptionalPrincipal = Annotated[Principal | None, Depends(get_principal_optional)]


@router.get("", response_model=ScoreboardResponse)
@router.get("/", response_model=ScoreboardResponse, include_in_schema=False)
async def read_scoreboard(
    principal: OptionalPrincipal,
    session: SessionDep,
) -> ScoreboardResponse:
    row = await get_settings_row(session)
    state = compute_state(row)
    viewer_team_id = principal.team.id if principal and principal.team else None
    return await build_scoreboard(
        session, state, settings_row=row, viewer_team_id=viewer_team_id
    )


@router.get("/results", response_model=ResultsResponse)
async def read_results(session: SessionDep) -> ResultsResponse:
    row = await get_settings_row(session)
    state = compute_state(row)
    return await build_results(session, state, settings_row=row)


@router.get("/results/team/{team_id}", response_model=ResultsResponse)
async def read_team_results(team_id: UUID, session: SessionDep) -> ResultsResponse:
    row = await get_settings_row(session)
    state = compute_state(row)
    return await team_results(session, team_id=team_id, state=state, settings_row=row)


@router.get("/live", response_model=ScoreboardResponse, include_in_schema=False)
async def read_scoreboard_alias(
    principal: OptionalPrincipal,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> ScoreboardResponse:
    return await read_scoreboard(principal, session)
