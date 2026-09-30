"""Spec-compatibility aliases for challenges and hint unlocking.

Supports:
- POST /api/challenges/{id}/hints/{hint_id}/unlock
- GET /api/challenges/{id} by UUID or slug
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.errors import NotFound, TeamRequired
from app.models.challenges import Challenge
from app.schemas.challenge import ChallengeDetail, HintUnlockResponse
from app.security.deps import (
    OptionalPrincipalDep,
    Principal,
    get_active_principal,
)
from app.services.challenges import load_team_progress, to_detail, unlock_hint
from app.services.competition import get_public_state

router = APIRouter(prefix="/challenges", tags=["challenges"])
ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]


async def _resolve_challenge(session: SessionDep, identifier: str) -> Challenge:
    """Find challenge by UUID string or slug."""
    try:
        val_uuid = uuid.UUID(identifier)
        stmt = (
            select(Challenge)
            .options(
                selectinload(Challenge.category),
                selectinload(Challenge.hints),
                selectinload(Challenge.files),
            )
            .where(Challenge.id == val_uuid, Challenge.visible.is_(True))
            .limit(1)
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row:
            return row
    except ValueError:
        pass

    stmt = (
        select(Challenge)
        .options(
            selectinload(Challenge.category),
            selectinload(Challenge.hints),
            selectinload(Challenge.files),
        )
        .where(Challenge.slug == identifier, Challenge.visible.is_(True))
        .limit(1)
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise NotFound("Challenge not found.", code="challenge_not_found")
    return row


@router.get("/by-id/{challenge_id}", response_model=ChallengeDetail)
async def get_challenge_by_id(
    challenge_id: uuid.UUID,
    principal: OptionalPrincipalDep,
    session: SessionDep,
) -> ChallengeDetail:
    challenge = await _resolve_challenge(session, str(challenge_id))
    competition = await get_public_state(session)
    viewer_team = principal.team.id if principal and principal.team else None
    progress = await load_team_progress(session, viewer_team)
    return to_detail(challenge, progress, max_attempts=competition.max_attempts_per_challenge)


@router.post("/by-id/{challenge_id}/hints/{hint_id}/unlock", response_model=HintUnlockResponse)
async def post_unlock_hint_by_id(
    challenge_id: uuid.UUID,
    hint_id: uuid.UUID,
    principal: ActivePrincipal,
    session: SessionDep,
) -> HintUnlockResponse:
    if principal.team is None:
        raise TeamRequired()

    challenge = await _resolve_challenge(session, str(challenge_id))
    result = await unlock_hint(
        session,
        challenge=challenge,
        hint_id=hint_id,
        team=principal.team,
        user_id=principal.user_id,
    )
    await session.commit()
    return result
