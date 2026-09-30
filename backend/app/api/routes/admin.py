"""Minimal organiser routes required by the frontend Admin panel.

Full RBAC/mutation coverage lives in the admin service layer; these endpoints
expose stats + challenge creation behind the organiser identity so the
``/admin`` frontend route is functional.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.challenges import Category, Challenge
from app.schemas.admin import AdminChallengeCreate, AdminStats
from app.security.deps import AdminDep
from app.security.flags import hash_flag
from app.services.admin import build_stats, leaderboard
from app.services.competition import get_settings_row

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def read_admin_stats(admin: AdminDep, session: SessionDep) -> AdminStats:
    row = await get_settings_row(session)
    from app.services.competition import compute_state

    state = compute_state(row)
    return await build_stats(session, status=state.status)


@router.get("/leaderboard")
async def read_admin_leaderboard(admin: AdminDep, session: SessionDep) -> dict:
    return {"entries": await leaderboard(session)}


@router.post("/challenges", response_model=dict, status_code=status.HTTP_201_CREATED)
async def post_admin_challenge(
    payload: AdminChallengeCreate, admin: AdminDep, session: SessionDep
) -> dict:
    category_id: UUID | None = payload.category_id
    if category_id is None and payload.category_slug:
        row = (
            await session.execute(
                select(Category).where(Category.slug == payload.category_slug).limit(1)
            )
        ).scalar_one_or_none()
        # Auto-create a visible category for the requested slug so the
        # frontend simple string-based form works without extra admin steps.
        if row is None:
            row = Category(
                slug=payload.category_slug,
                name=payload.category_slug.replace("-", " ").title(),
            )
            session.add(row)
            await session.flush()
        category_id = row.id
    if category_id is None:
        # Fall back to the first visible category.
        row = (
            await session.execute(select(Category).order_by(Category.display_order).limit(1))
        ).scalar_one_or_none()
        if row is None:
            from app.errors import BadRequest

            raise BadRequest("No categories exist. Create one first.", code="no_categories")
        category_id = row.id

    slug = payload.slug or payload.title.lower().strip().replace(" ", "-")[:80]
    challenge = Challenge(
        title=payload.title.strip(),
        slug=slug,
        category_id=category_id,
        description=payload.description,
        difficulty=payload.difficulty,
        points=payload.points,
        flag_hash=hash_flag(payload.flag),
        flag_format_hint=payload.flag_format_hint,
        connection_info=payload.connection_info,
        author=payload.author,
        visible=payload.visible,
        requires_team=payload.requires_team,
        max_attempts_per_minute=payload.max_attempts_per_minute,
        released_at=payload.released_at,
        is_demo=payload.is_demo,
    )
    session.add(challenge)
    await session.flush()
    if payload.hints:
        from app.models.challenges import ChallengeHint

        for idx, hint in enumerate(payload.hints):
            session.add(
                ChallengeHint(
                    challenge_id=challenge.id,
                    text=hint.text,
                    cost=hint.cost,
                    display_order=hint.display_order or idx,
                    is_visible=hint.is_visible,
                )
            )
    await session.commit()
    return {"id": str(challenge.id), "slug": challenge.slug}
