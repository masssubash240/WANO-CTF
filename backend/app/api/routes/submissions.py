"""Flag submission endpoint (delegates to the scoring service)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import SessionDep, client_ip, user_agent
from app.schemas.challenge import FlagSubmitRequest, FlagSubmitResponse
from app.security.deps import (
    Principal,
    get_active_principal,
    get_team_principal,
)
from app.services.challenges import get_visible_challenge_or_404, load_team_progress
from app.services.competition import get_public_state, require_submissions_open
from app.services.scoring import submit_flag

router = APIRouter(prefix="/submissions", tags=["submissions"])

TeamPrincipal = Annotated[Principal, Depends(get_team_principal)]
ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]


@router.post("/{slug}/submit", response_model=FlagSubmitResponse)
async def post_submit_flag(
    slug: str,
    payload: FlagSubmitRequest,
    request: Request,
    principal: TeamPrincipal,
    session: SessionDep,
) -> FlagSubmitResponse:
    """Submit a flag for a challenge. Requires an active team membership."""
    await require_submissions_open(session)
    challenge = await get_visible_challenge_or_404(session, slug)
    competition = await get_public_state(session)
    progress = await load_team_progress(session, principal.team.id if principal.team else None)
    result = await submit_flag(
        session,
        challenge=challenge,
        team=principal.team,  # type: ignore[arg-type]
        user_id=principal.user_id,
        submitted_flag=payload.flag,
        ip_address=client_ip(request),
        user_agent=user_agent(request),
        max_attempts=competition.max_attempts_per_challenge,
        rate_limit_per_minute=competition.submission_rate_limit_per_minute,
        hint_cost=progress.cost_for(challenge.id),
    )
    return result
