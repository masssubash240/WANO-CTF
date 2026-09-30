"""FastAPI dependencies: identity resolution, RBAC, and request context.

Design rules enforced here
--------------------------
* Participants authenticate with a Supabase access token (production) or a
  locally issued token (dev/test provider only).
* Organisers authenticate through a **separate** admin token validated against
  ``admin_sessions`` so it can be revoked server-side.
* Nothing is ever trusted from the client: role, team id, score and admin status
  are always re-read from the database inside the request.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --------------------------------------------------------------------------- ctx
# `client_ip` lives in app.api.deps (it owns the proxy-trust policy). It is
# re-exported here so security consumers keep a single import path. Do NOT
# re-implement it: an unconditional trust of X-Forwarded-For would let a client
# spoof its address and defeat IP rate limits and the audit trail.
from app.api.deps import client_ip  # noqa: E402  (re-export)
from app.config import settings
from app.database import get_session
from app.errors import AccountDisabled, Forbidden, Unauthorized
from app.models.accounts import AdminSession, AdminUser, Profile
from app.models.enums import AdminRole, TeamRole, TeamStatus, UserRole
from app.models.teams import Team, TeamMember
from app.security.supabase_auth import SupabaseAuthError, verify_supabase_token
from app.security.tokens import TokenError, decode_admin_token, decode_user_token


def user_agent(request: Request) -> str:
    return (request.headers.get("user-agent") or "unknown")[:400]


@dataclass(slots=True)
class RequestContext:
    ip: str
    user_agent: str
    request_id: str
    path: str
    method: str


def get_request_context(request: Request) -> RequestContext:
    return RequestContext(
        ip=client_ip(request),
        user_agent=user_agent(request),
        request_id=getattr(request.state, "request_id", "-"),
        path=request.url.path,
        method=request.method,
    )


# ------------------------------------------------------------------- principals
@dataclass(slots=True)
class Principal:
    """Authenticated participant."""

    user_id: uuid.UUID
    email: str
    role: UserRole
    auth_method: Literal["supabase", "local"]
    profile: Profile
    team: Team | None = None
    membership: TeamMember | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def has_team(self) -> bool:
        return self.team is not None

    @property
    def team_id(self) -> uuid.UUID | None:
        return self.team.id if self.team else None

    @property
    def is_captain(self) -> bool:
        return bool(self.membership and self.membership.role == TeamRole.CAPTAIN)

    @property
    def team_status(self) -> TeamStatus | None:
        return self.team.status if self.team else None


@dataclass(slots=True)
class AdminPrincipal:
    """Authenticated organiser (admin panel identity, fully separate)."""

    admin_id: uuid.UUID
    email: str
    role: AdminRole
    display_name: str = "Admin"
    jti: str | None = None
    source: Literal["admin_login", "supabase"] = "admin_login"

    @property
    def is_superadmin(self) -> bool:
        return self.role == AdminRole.SUPERADMIN

    def can(self, *roles: AdminRole) -> bool:
        return self.role == AdminRole.SUPERADMIN or not roles or self.role in roles


# ------------------------------------------------------------------ token utils
def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _parse_uuid(value: Any) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError) as exc:
        raise Unauthorized("Invalid session. Please sign in again.", code="invalid_session") from exc


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


# ------------------------------------------------------- profile provisioning
async def ensure_profile(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    email: str,
    full_name: str = "",
    email_verified: bool = False,
    commit: bool = True,
) -> Profile:
    """Get-or-create the participant profile row for an authenticated identity."""
    profile = await session.get(Profile, user_id)
    if profile is not None:
        if email and profile.email != email.lower():
            profile.email = email.lower()
        if email_verified and not profile.email_verified:
            profile.email_verified = True
        if commit:
            await session.commit()
        return profile

    profile = Profile(
        id=user_id,
        email=email.lower(),
        full_name=(full_name or email.split("@")[0])[:160],
        email_verified=email_verified,
        role=UserRole.PARTICIPANT,
    )
    session.add(profile)
    try:
        if commit:
            await session.commit()
        else:
            await session.flush()
    except Exception:
        # Concurrent first request: another worker inserted it first.
        await session.rollback()
        existing = await session.get(Profile, user_id)
        if existing is None:
            raise
        return existing
    return profile


async def load_team_context(
    session: AsyncSession, user_id: uuid.UUID
) -> tuple[Team | None, TeamMember | None]:
    stmt = (
        select(TeamMember, Team)
        .join(Team, Team.id == TeamMember.team_id)
        .where(TeamMember.user_id == user_id)
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if not row:
        return None, None
    membership, team = row
    return team, membership


# ------------------------------------------------------------------ participant
async def get_principal_optional(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> Principal | None:
    cached = getattr(request.state, "principal", None)
    if cached is not None:
        return cached

    token = _bearer_token(request)
    if not token:
        return None

    if settings.auth_provider == "local":
        try:
            claims = decode_user_token(token)
        except TokenError as exc:
            raise Unauthorized("Your session expired. Please sign in again.", code=exc.reason) from exc
        identity = {
            "user_id": _parse_uuid(claims.get("sub")),
            "email": claims.get("email") or "",
            "verified": True,
            "full_name": claims.get("full_name") or "",
        }
        auth_method: Literal["supabase", "local"] = "local"
    else:
        try:
            supabase_identity = await verify_supabase_token(token)
        except TokenError as exc:
            raise Unauthorized(
                "Your session is no longer valid. Please sign in again.", code=exc.reason
            ) from exc
        except SupabaseAuthError as exc:
            raise Unauthorized(
                "Authentication is temporarily unavailable.", code="auth_unavailable"
            ) from exc
        identity = {
            "user_id": _parse_uuid(supabase_identity.user_id),
            "email": supabase_identity.email,
            "verified": supabase_identity.email_verified,
            "full_name": "",
        }
        auth_method = "supabase"

    profile = await ensure_profile(
        session,
        user_id=identity["user_id"],
        email=identity["email"] or f"{identity['user_id']}@wano.local",
        full_name=identity["full_name"],
        email_verified=bool(identity["verified"]),
    )

    team, membership = await load_team_context(session, profile.id)
    principal = Principal(
        user_id=profile.id,
        email=profile.email,
        role=profile.role,
        auth_method=auth_method,
        profile=profile,
        team=team,
        membership=membership,
    )
    request.state.principal = principal
    request.state.auth_method = auth_method
    return principal


async def get_current_principal(
    principal: Annotated[Principal | None, Depends(get_principal_optional)],
) -> Principal:
    if principal is None:
        raise Unauthorized()
    return principal


async def get_active_principal(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    profile = principal.profile
    if profile.is_banned:
        raise AccountDisabled(
            profile.ban_reason or None, code="account_banned", details={"banned": True}
        )
    if not profile.is_active:
        raise AccountDisabled(
            "This account is inactive. Contact WANO CTF support.", code="account_inactive"
        )
    return principal


async def get_team_principal(
    principal: Annotated[Principal, Depends(get_active_principal)],
) -> Principal:
    """Guarantees an active, non-disqualified team membership."""
    from app.errors import TeamRequired

    if principal.team is None:
        raise TeamRequired()
    if principal.team.status == TeamStatus.DISQUALIFIED:
        raise Forbidden("This team has been disqualified by the organisers.", code="team_disqualified")
    return principal


async def get_captain_principal(
    principal: Annotated[Principal, Depends(get_team_principal)],
) -> Principal:
    if not principal.is_captain:
        raise Forbidden("Only the team captain can perform this action.", code="captain_only")
    return principal


def require_user_roles(*roles: UserRole):
    async def _dep(principal: Annotated[Principal, Depends(get_active_principal)]) -> Principal:
        if roles and principal.role not in roles:
            raise Forbidden()
        return principal

    return _dep


# ------------------------------------------------------------------------ admin
async def get_current_admin(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> AdminPrincipal:
    cached = getattr(request.state, "admin", None)
    if cached is not None:
        return cached

    token = _bearer_token(request)
    if not token:
        raise Unauthorized("Admin authentication required.", code="admin_auth_required")

    # Path 1 — dedicated organiser token issued by /api/admin/auth/login.
    try:
        claims: dict[str, Any] | None = decode_admin_token(token)
    except TokenError:
        claims = None

    if claims:
        jti = str(claims.get("jti") or "")
        admin_id = _parse_uuid(claims.get("sub"))
        admin = await session.get(AdminUser, admin_id)
        if admin is None or not admin.is_active:
            raise Forbidden("This organiser account is disabled.", code="admin_disabled")
        if admin.locked_until and _aware(admin.locked_until) > datetime.now(UTC):
            raise Forbidden("This organiser account is temporarily locked.", code="admin_locked")
        session_row = (
            await session.execute(select(AdminSession).where(AdminSession.jti == jti))
        ).scalar_one_or_none()
        if session_row is None or session_row.revoked_at is not None:
            raise Unauthorized(
                "Admin session revoked. Please sign in again.", code="admin_session_revoked"
            )
        if session_row.expires_at and _aware(session_row.expires_at) <= datetime.now(UTC):
            raise Unauthorized("Admin session expired. Please sign in again.", code="admin_session_expired")

        principal = AdminPrincipal(
            admin_id=admin.id,
            email=admin.email,
            role=admin.role,
            display_name=admin.display_name,
            jti=jti,
        )
        request.state.admin = principal
        request.state.admin_session_id = session_row.id
        return principal

    # Path 2 — optional: a Supabase participant whose profile role is 'admin'.
    if settings.allow_admin_supabase_login:
        try:
            participant = await get_principal_optional(request, session)
        except Unauthorized:
            participant = None
        if (
            participant is not None
            and participant.role == UserRole.ADMIN
            and not participant.profile.is_banned
            and participant.profile.is_active
        ):
            principal = AdminPrincipal(
                admin_id=participant.user_id,
                email=participant.email,
                role=AdminRole.ADMIN,
                display_name=participant.profile.display_name,
                source="supabase",
            )
            request.state.admin = principal
            return principal

    raise Unauthorized("Admin authentication required.", code="admin_auth_required")


def require_admin_roles(*roles: AdminRole):
    """Dependency factory: superadmin always passes."""

    async def _dep(admin: Annotated[AdminPrincipal, Depends(get_current_admin)]) -> AdminPrincipal:
        if admin.is_superadmin:
            return admin
        if roles and admin.role not in roles:
            raise Forbidden(
                "Your organiser role cannot perform this action.", code="insufficient_admin_role"
            )
        return admin

    return _dep


# ------------------------------------------------------------------ typed aliases
SessionDep = Annotated[AsyncSession, Depends(get_session)]
OptionalPrincipalDep = Annotated[Principal | None, Depends(get_principal_optional)]
PrincipalDep = Annotated[Principal, Depends(get_current_principal)]
ActivePrincipalDep = Annotated[Principal, Depends(get_active_principal)]
TeamPrincipalDep = Annotated[Principal, Depends(get_team_principal)]
CaptainDep = Annotated[Principal, Depends(get_captain_principal)]
AdminDep = Annotated[AdminPrincipal, Depends(get_current_admin)]
RequestCtxDep = Annotated[RequestContext, Depends(get_request_context)]

