"""Authenticated profile + dashboard session endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep
from app.errors import NotFound
from app.models.enums import UserRole
from app.schemas.profile import ProfilePublic, ProfileSelf, ProfileUpdate, SessionResponse
from app.security.deps import Principal, get_active_principal
from app.services.competition import get_public_state
from app.services.teams import to_membership_summary

router = APIRouter(prefix="/users", tags=["users"])


def _to_self(principal: Principal) -> ProfileSelf:
    profile = principal.profile
    return ProfileSelf(
        id=profile.id,
        email=profile.email,
        full_name=profile.display_name,
        college=profile.college,
        department=profile.department,
        year=profile.year,
        phone=profile.phone,
        role=profile.role.value,
        email_verified=profile.email_verified,
        is_active=profile.is_active,
        is_banned=profile.is_banned,
        ban_reason=profile.ban_reason,
        last_login_at=profile.last_login_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]


@router.get("/me", response_model=SessionResponse)
async def read_session(principal: ActivePrincipal, session: SessionDep) -> SessionResponse:
    """One round trip with everything the dashboard needs."""
    # Always loaded: `teams_locked` gates the "create a team" affordance even
    # for participants who are not in a team yet.
    competition = await get_public_state(session)

    team_summary = None
    if principal.team is not None and principal.membership is not None:
        team_summary = await to_membership_summary(
            session,
            principal.team,
            principal.membership,
            max_team_size=competition.max_team_size,
        )

    is_staff = principal.role == UserRole.ADMIN
    return SessionResponse(
        profile=_to_self(principal),
        team=team_summary,
        is_captain=principal.is_captain,
        is_admin=is_staff,
        auth_provider=principal.auth_method,
        permissions={
            "can_create_team": team_summary is None and not competition.teams_locked,
            "can_edit_profile": True,
            "can_unlock_hints": team_summary is not None,
            "can_submit_flags": team_summary is not None,
            "is_staff": is_staff,
        },
    )


@router.get("/me/profile", response_model=ProfileSelf)
async def read_profile(principal: ActivePrincipal) -> ProfileSelf:
    return _to_self(principal)


@router.patch("/me/profile", response_model=ProfileSelf)
async def update_profile(
    payload: ProfileUpdate, principal: ActivePrincipal, session: SessionDep
) -> ProfileSelf:
    """Self-service edit. Role and moderation fields are not part of the schema."""
    profile = principal.profile
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await session.commit()
    await session.refresh(profile)
    return _to_self(principal)


@router.get("/{user_id}", response_model=ProfilePublic)
async def read_public_profile(user_id, session: SessionDep) -> ProfilePublic:
    """Public projection only — email and phone are never exposed here."""
    from app.models.accounts import Profile

    profile = await session.get(Profile, user_id)
    if profile is None:
        raise NotFound("That participant could not be found.")
    return ProfilePublic(
        id=profile.id,
        full_name=profile.display_name,
        college=profile.college,
        department=profile.department,
        year=profile.year,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
