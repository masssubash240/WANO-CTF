"""JWT issuing/verification for the two independent authentication domains.

* ``wano-user``  – participants (issued by the local dev provider; in production
  Supabase Auth issues the token and this module only *verifies* it).
* ``wano-admin`` – organisers, always issued here, always revocable through the
  ``admin_sessions`` table (a stolen admin token can be killed instantly).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import settings

AUDIENCE_USER = "wano-user"
AUDIENCE_ADMIN = "wano-admin"
ISSUER = "wano-ctf"


class TokenError(Exception):
    """Raised for any invalid/expired token; ``reason`` is safe to log."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(slots=True)
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime
    claims: dict[str, Any] = field(default_factory=dict)


def _now() -> datetime:
    return datetime.now(UTC)


def create_token(
    subject: str,
    *,
    audience: str,
    secret: str,
    ttl_minutes: int | None = None,
    claims: dict[str, Any] | None = None,
    algorithm: str = "HS256",
) -> IssuedToken:
    issued_at = _now()
    ttl = ttl_minutes if ttl_minutes is not None else settings.access_token_ttl_minutes
    expires_at = issued_at + timedelta(minutes=ttl)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(subject),
        "aud": audience,
        "iss": ISSUER,
        "iat": int(issued_at.timestamp()),
        "nbf": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": jti,
    }
    if claims:
        payload.update(claims)
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return IssuedToken(token=token, jti=jti, expires_at=expires_at, claims=payload)


def create_user_token(subject: str, *, email: str, role: str = "participant") -> IssuedToken:
    """Local-provider access token (dev/test only)."""
    return create_token(
        subject,
        audience=AUDIENCE_USER,
        secret=settings.jwt_secret,
        claims={"email": email, "role": role, "typ": "access", "provider": "local"},
    )


def create_admin_token(
    subject: str, *, email: str, role: str, ttl_minutes: int = 480
) -> IssuedToken:
    return create_token(
        subject,
        audience=AUDIENCE_ADMIN,
        secret=settings.admin_jwt_secret,
        ttl_minutes=ttl_minutes,
        claims={"email": email, "amd_role": role, "typ": "admin"},
    )


def decode_token(
    token: str,
    *,
    audience: str,
    secret: str,
    leeway_seconds: int = 10,
) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience,
            issuer=ISSUER,
            leeway=leeway_seconds,
            options={"require": ["exp", "iat", "sub", "aud"]},
        )
    except jwt.ExpiredSignatureError as exc:  # pragma: no cover - depends on clock
        raise TokenError("token_expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise TokenError("invalid_audience") from exc
    except jwt.InvalidIssuerError as exc:
        raise TokenError("invalid_issuer") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid_token") from exc


def decode_user_token(token: str) -> dict[str, Any]:
    return decode_token(token, audience=AUDIENCE_USER, secret=settings.jwt_secret)


def decode_admin_token(token: str) -> dict[str, Any]:
    return decode_token(token, audience=AUDIENCE_ADMIN, secret=settings.admin_jwt_secret)


def decode_unverified(token: str) -> dict[str, Any]:
    """Header/payload peek for routing decisions only — never for authz."""
    try:
        return jwt.decode(token, options={"verify_signature": False, "verify_aud": False})
    except jwt.InvalidTokenError:
        return {}
