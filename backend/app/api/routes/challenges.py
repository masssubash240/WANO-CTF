"""Challenge browsing and hint unlocks."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.models.challenges import Category, Challenge
from app.schemas.challenge import (
    CategoryPublic,
    ChallengeDetail,
    ChallengeSummary,
    HintUnlockResponse,
)
from app.security.deps import Principal, get_active_principal, get_principal_optional
from app.services.challenges import (
    get_visible_challenge_or_404,
    load_team_progress,
    to_detail,
    to_summary,
    unlock_hint,
)
from app.services.competition import get_public_state

router = APIRouter(prefix="/challenges", tags=["challenges"])

ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]
OptionalPrincipal = Annotated[Principal | None, Depends(get_principal_optional)]


def _viewer_team(principal: Principal | None) -> uuid.UUID | None:
    return principal.team.id if principal is not None and principal.team is not None else None


@router.get("/categories", response_model=list[CategoryPublic])
async def list_categories(session: SessionDep) -> list[CategoryPublic]:
    """Visible categories with their challenge/solve rollups."""
    stmt = (
        select(Category)
        .options(selectinload(Category.challenges))
        .where(Category.is_visible.is_(True))
        .order_by(Category.display_order, Category.name)
    )
    rows = list((await session.execute(stmt)).scalars())
    return [
        CategoryPublic(
            id=row.id,
            slug=row.slug,
            name=row.name,
            description=row.description,
            icon=row.icon,
            accent=row.accent,
            display_order=row.display_order,
            challenge_count=len(row.challenges),
            solved_count=sum(c.solved_count for c in row.challenges if c.visible),
            total_points=sum(c.points for c in row.challenges if c.visible),
        )
        for row in rows
    ]


@router.get("", response_model=list[ChallengeSummary])
async def list_challenges(
    principal: OptionalPrincipal,
    session: SessionDep,
    category: Annotated[str | None, Query(max_length=60)] = None,
    difficulty: Annotated[str | None, Query(max_length=20)] = None,
) -> list[ChallengeSummary]:
    """Visible challenges only; personalisation is limited to is_solved."""
    stmt = select(Challenge).where(Challenge.visible.is_(True))
    if category:
        stmt = stmt.join(Category).where(Category.slug == category)
    if difficulty:
        stmt = stmt.where(Challenge.difficulty == difficulty)
    stmt = stmt.order_by(Challenge.points.desc(), Challenge.title)

    progress = await load_team_progress(session, _viewer_team(principal))
    return [to_summary(row, progress) for row in (await session.execute(stmt)).scalars()]


@router.get("/{slug}", response_model=ChallengeDetail)
async def read_challenge(
    slug: str, principal: OptionalPrincipal, session: SessionDep
) -> ChallengeDetail:
    """Full detail. Locked hints expose their cost but never their text."""
    challenge = await get_visible_challenge_or_404(session, slug)
    competition = await get_public_state(session)
    progress = await load_team_progress(session, _viewer_team(principal))
    return to_detail(challenge, progress, max_attempts=competition.max_attempts_per_challenge)


@router.post("/{slug}/hints/{hint_id}/unlock", response_model=HintUnlockResponse)
async def post_unlock_hint(
    slug: str,
    hint_id: uuid.UUID,
    principal: ActivePrincipal,
    session: SessionDep,
) -> HintUnlockResponse:
    """Spend team points to reveal a hint. Idempotent per team."""
    if principal.team is None:
        from app.errors import TeamRequired

        raise TeamRequired()

    challenge = await get_visible_challenge_or_404(session, slug)
    result = await unlock_hint(
        session,
        challenge=challenge,
        hint_id=hint_id,
        team=principal.team,
        user_id=principal.user_id,
    )
    await session.commit()
    return result
