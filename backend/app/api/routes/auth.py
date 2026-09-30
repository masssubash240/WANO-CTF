"""Participant authentication.

In production Supabase Auth owns passwords and this router only advertises the
project's public URL/anon key. The local register/login endpoints exist purely
for offline development and are hard-disabled unless ``DEV_AUTH_ENABLED`` is on
(and never when ``ENVIRONMENT`` is production).
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime

from fastapi import APIRouter, Request, status
from sqlalchemy import select

from app.api.deps import SessionDep, client_ip, user_agent
from app.config import settings
from app.errors import BadRequest, Forbidden, Unauthorized
from app.models.accounts import Profile
from app.models.enums import UserRole
from app.schemas.auth import (
    AuthConfigResponse,
    LocalLoginRequest,
    LocalRegisterRequest,
    PasswordResetRequest,
    TokenResponse,
)
from app.schemas.common import Message
from app.security.passwords import verify_password
from app.security.rate_limit import enforce
from app.security.supabase_auth import supabase_admin
from app.security.tokens import create_user_token
from app.services.audit import record_login_event
from app.services.competition import require_registration_open

router = APIRouter(prefix="/auth", tags=["auth"])


def _dev_guard() -> None:
    if not settings.dev_auth_enabled or settings.is_production:
        raise NotImplementedErrorRoute()


class NotImplementedErrorRoute(BadRequest):
    """Local auth is unavailable in this deployment."""

    def __init__(self) -> None:
        super().__init__(
            "Local authentication is disabled. Use the configured auth provider.",
            code="dev_auth_disabled",
            status_code=status.HTTP_404_NOT_FOUND,
        )


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config() -> AuthConfigResponse:
    """Which provider the browser should use. Exposes public keys only."""
    return AuthConfigResponse(
        provider=settings.auth_provider,
        supabase_url=settings.supabase_url if settings.supabase_configured else None,
        supabase_anon_key=(
            settings.supabase_anon_key if settings.supabase_configured else None
        ),
        email_verification_required=settings.email_verification_required,
        google_oauth_enabled=settings.google_oauth_enabled,
        password_reset_enabled=settings.password_reset_enabled,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: LocalRegisterRequest, request: Request, session: SessionDep
) -> TokenResponse:
    """Dev-only signup. Creates the Supabase user and its local profile row."""
    _dev_guard()
    if settings.auth_provider != "local":
        raise Forbidden("Registration is handled by the configured auth provider.")

    await enforce(f"register:{client_ip(request)}", limit=settings.rate_limit_register_per_minute)
    await require_registration_open(session)

    try:
        created = await supabase_admin.create_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            email_confirm=not settings.email_verification_required,
        )
    except Exception:
        await record_login_event(
            session, success=False, email=payload.email, reason="register_failed",
            ip_address=client_ip(request), user_agent=user_agent(request),
        )
        await session.commit()
        # Deliberately vague: never confirm whether an address already exists.
        raise BadRequest("Unable to create that account.", code="registration_failed") from None

    profile = Profile(
        id=created["id"],
        email=payload.email,
        full_name=payload.full_name,
        college=payload.college,
        department=payload.department,
        year=payload.year,
        phone=payload.phone,
        role=UserRole.PARTICIPANT,
        email_verified=not settings.email_verification_required,
    )
    session.add(profile)
    await record_login_event(
        session, success=True, email=payload.email, user_id=profile.id,
        reason="register", ip_address=client_ip(request), user_agent=user_agent(request),
    )
    await session.commit()

    if payload.team_name and payload.team_name.strip():
        from app.schemas.team import TeamCreateRequest
        from app.services.teams import create_team
        try:
            await create_team(
                session,
                user=profile.id,
                payload=TeamCreateRequest(
                    name=payload.team_name.strip(),
                    college=payload.college,
                    description=f"{payload.college or 'College'} CTF Team",
                ),
            )
            await session.commit()
        except Exception:
            # If team creation fails (e.g. duplicate name), user registration still succeeds
            await session.rollback()

    issued = create_user_token(str(profile.id), email=profile.email, role=profile.role.value)
    return TokenResponse(
        access_token=issued.token,
        expires_in=settings.access_token_ttl_minutes * 60,
        expires_at=issued.expires_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LocalLoginRequest, request: Request, session: SessionDep
) -> TokenResponse:
    """Dev-only password sign-in with brute-force throttling."""
    _dev_guard()
    ip = client_ip(request)
    agent = user_agent(request)
    await enforce(f"login:{ip}", limit=settings.rate_limit_login_per_minute)

    profile = (
        await session.execute(select(Profile).where(Profile.email == payload.email))
    ).scalar_one_or_none()
    if profile is None:
        await record_login_event(
            session, success=False, email=payload.email, reason="unknown_account",
            ip_address=ip, user_agent=agent,
        )
        await session.commit()
        raise Unauthorized("Incorrect email or password.", code="invalid_credentials")

    if not verify_password(payload.password, profile.password_hash):
        profile.failed_login_count = (profile.failed_login_count or 0) + 1
        await record_login_event(
            session, success=False, email=payload.email, user_id=profile.id,
            reason="bad_password", ip_address=ip, user_agent=agent,
        )
        await session.commit()
        raise Unauthorized("Incorrect email or password.", code="invalid_credentials")

    if profile.is_banned:
        await record_login_event(
            session, success=False, email=payload.email, user_id=profile.id,
            reason="banned", ip_address=ip, user_agent=agent,
        )
        await session.commit()
        raise Forbidden(
            profile.ban_reason or "This account has been disabled by the organisers.",
            code="account_banned",
        )

    profile.failed_login_count = 0
    profile.last_login_at = datetime.now(UTC)
    profile.last_login_ip = ip
    await record_login_event(
        session, success=True, email=payload.email, user_id=profile.id,
        reason="login", ip_address=ip, user_agent=agent,
    )
    await session.commit()

    issued = create_user_token(str(profile.id), email=profile.email, role=profile.role.value)
    return TokenResponse(
        access_token=issued.token,
        expires_in=settings.access_token_ttl_minutes * 60,
        expires_at=issued.expires_at,
    )


@router.post("/password-reset", response_model=Message)
async def password_reset(payload: PasswordResetRequest, request: Request, session: SessionDep) -> Message:
    """Always reports success so the endpoint cannot be used to enumerate accounts."""
    if settings.password_reset_enabled:
        await enforce(
            f"reset:{client_ip(request)}", limit=settings.rate_limit_password_reset_per_minute
        )
        with suppress(Exception):
            # Upstream failure must not leak whether the address is registered.
            await supabase_admin.send_recovery(
                payload.email, redirect_to=f"{settings.frontend_url}/reset-password"
            )
    return Message(message="If that email is registered, a reset link is on its way.")
