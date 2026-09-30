"""Team lifecycle endpoints for participants."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep
from app.schemas.common import Message
from app.schemas.team import (
    TeamCreateRequest,
    TeamDetail,
    TeamJoinRequest,
    TeamUpdateRequest,
)
from app.security.deps import (
    Principal,
    get_active_principal,
    get_principal_optional,
    get_team_principal,
)
from app.services import teams as team_service
from app.services.competition import get_public_state, require_team_changes_allowed
from app.services.teams import (
    create_team,
    get_team_or_404,
    join_team,
    leave_team,
    to_detail,
)

router = APIRouter(prefix="/teams", tags=["teams"])

ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]
OptionalPrincipal = Annotated[Principal | None, Depends(get_principal_optional)]
TeamPrincipal = Annotated[Principal, Depends(get_team_principal)]


@router.get("/mine", response_model=TeamDetail)
async def read_my_team(principal: ActivePrincipal, session: SessionDep) -> TeamDetail:
    if principal.team is None:
        return None  # type: ignore[return-value]
    return await to_detail(session, principal.team, viewer_id=principal.user_id)


@router.post("", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TeamDetail, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def post_create_team(
    payload: TeamCreateRequest, principal: ActivePrincipal, session: SessionDep
) -> TeamDetail:
    """Creating a team is blocked once the organiser locks rosters."""
    await require_team_changes_allowed(session)
    team = await create_team(session, user=principal.user_id, payload=payload)
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await to_detail(session, team, viewer_id=principal.user_id)


@router.post("/join", response_model=TeamDetail)
async def post_join_team(
    payload: TeamJoinRequest, principal: ActivePrincipal, session: SessionDep
) -> TeamDetail:
    competition = await get_public_state(session)
    await require_team_changes_allowed(session)
    team = await join_team(
        session,
        user=principal.user_id,
        code=payload.team_code,
        max_team_size=competition.max_team_size,
    )
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await to_detail(session, team, viewer_id=principal.user_id)


@router.post("/leave", response_model=Message)
async def post_leave_team(principal: ActivePrincipal, session: SessionDep) -> Message:
    await require_team_changes_allowed(session)
    await leave_team(session, user=principal.user_id)
    await session.commit()
    return Message(message="You have left the team.")


@router.patch("/mine", response_model=TeamDetail)
async def patch_my_team(
    payload: TeamUpdateRequest, principal: TeamPrincipal, session: SessionDep
) -> TeamDetail:
    """Captain-only in spirit: the shared schema only exposes cosmetic fields."""
    team = principal.team
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await to_detail(session, team, viewer_id=principal.user_id)


@router.get("/{team_id}", response_model=TeamDetail)
async def read_team(
    team_id: uuid.UUID,
    principal: OptionalPrincipal,
    session: SessionDep,
) -> TeamDetail:
    """Public view. ``team_code`` is withheld unless the caller is a member."""
    team = await get_team_or_404(session, team_id)
    viewer_id = principal.user_id if principal is not None else None
    return await to_detail(session, team, viewer_id=viewer_id)
