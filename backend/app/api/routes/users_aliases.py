"""Spec-compatibility aliases: /user/profile and /user/solves."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.submissions import Solve
from app.schemas.challenge import SolveRecord
from app.schemas.profile import ProfileSelf
from app.security.deps import Principal, get_active_principal

router = APIRouter(prefix="/user", tags=["user"])
ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]


@router.get("/profile", response_model=ProfileSelf)
async def read_user_profile_alias(principal: ActivePrincipal) -> ProfileSelf:
    from app.api.routes.users import _to_self

    return _to_self(principal)


@router.get("/solves", response_model=list[SolveRecord])
async def read_user_solves_alias(principal: ActivePrincipal, session: SessionDep) -> list[SolveRecord]:
    team_id = principal.team.id if principal.team else None
    if team_id is None:
        return []
    rows = list(
        (await session.execute(select(Solve).where(Solve.team_id == team_id).order_by(Solve.solved_at.desc()))).scalars()
    )
    out: list[SolveRecord] = []
    for solve in rows:
        challenge = solve.challenge
        category = challenge.category if challenge else None
        out.append(
            SolveRecord(
                challenge_id=solve.challenge_id,
                challenge_title=challenge.title if challenge else "Unknown",
                challenge_slug=challenge.slug if challenge else "",
                category_slug=category.slug if category else "",
                category_name=category.name if category else "Uncategorised",
                points=solve.points,
                hint_penalty=solve.hint_penalty,
                solved_at=solve.solved_at,
                first_blood=solve.is_first_blood,
            )
        )
    return out
