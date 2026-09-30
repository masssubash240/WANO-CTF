"""Supabase Auth integration (token verification + Admin API).

Production flow
---------------
1. The browser authenticates with ``supabase-js`` (GoTrue) and receives an
   access token. Supabase stores/hashes the password — we never see it.
2. The browser sends ``Authorization: Bearer <access_token>`` to this API.
3. We verify the token locally: asymmetric keys via the project JWKS endpoint
   (current Supabase default) or HS256 with the legacy JWT secret.
4. Service-role calls (create/disable users) are proxied through the Admin API
   so the service key never reaches the client.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from app.config import settings
from app.security.tokens import TokenError


class SupabaseAuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(slots=True)
class SupabaseIdentity:
    user_id: str
    email: str
    role: str = "authenticated"
    email_verified: bool = False


_JWKS_CACHE_TTL = 600
_jwks_client: PyJWKClient | None = None
_jwks_created_at = 0.0


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client, _jwks_created_at
    now = time.monotonic()
    if _jwks_client is None or (now - _jwks_created_at) > _JWKS_CACHE_TTL:
        _jwks_client = PyJWKClient(settings.jwks_url, cache_keys=True, lifespan=_JWKS_CACHE_TTL)
        _jwks_created_at = now
    return _jwks_client


def _verify_sync(token: str) -> SupabaseIdentity:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise TokenError("malformed_token") from exc

    algorithm = header.get("alg", "")
    # aud is "authenticated"; verified explicitly for HS256 below.
    options = {"verify_aud": False}

    try:
        if algorithm in {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA"}:
            if not settings.jwks_url:
                raise TokenError("jwks_not_configured")
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
            payload = jwt.decode(token, signing_key, algorithms=[algorithm], options=options)
        elif algorithm in {"HS256", "HS384", "HS512"}:
            if not settings.supabase_jwt_secret:
                raise TokenError("legacy_secret_not_configured")
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=[algorithm],
                audience="authenticated",
                options={"verify_aud": True},
            )
        else:
            raise TokenError("unsupported_algorithm")
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token_expired") from exc
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
        raise TokenError("invalid_token") from exc

    # Issuer pinning prevents tokens minted for another Supabase project.
    if settings.supabase_url:
        expected_iss = f"{settings.supabase_url.rstrip('/')}/auth/v1"
        if payload.get("iss") not in (None, expected_iss):
            raise TokenError("invalid_issuer")

    user_id = payload.get("sub")
    if not user_id:
        raise TokenError("missing_subject")

    metadata = payload.get("user_metadata") or {}
    return SupabaseIdentity(
        user_id=str(user_id),
        email=(payload.get("email") or "").lower(),
        role=payload.get("role") or "authenticated",
        email_verified=bool(payload.get("email_confirmed_at") or metadata.get("email_verified")),
    )


async def verify_supabase_token(token: str) -> SupabaseIdentity:
    """Verify a Supabase access token without trusting any client claim."""
    if not settings.supabase_configured:
        raise TokenError("supabase_not_configured")
    return await asyncio.to_thread(_verify_sync, token)


class SupabaseAdminClient:
    """Thin async wrapper over the GoTrue Admin API (service-role only)."""

    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    @property
    def _base(self) -> str:
        return f"{settings.supabase_url.rstrip('/')}/auth/v1"

    @property
    def _headers(self) -> dict[str, str]:
        key = settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _ensure_configured(self) -> None:
        if not settings.supabase_admin_configured:
            raise SupabaseAuthError("Supabase admin credentials are not configured.", status_code=503)

    async def create_user(
        self, *, email: str, password: str, full_name: str = "", email_confirm: bool = False
    ) -> dict[str, Any]:
        self._ensure_configured()
        payload = {
            "email": email,
            "password": password,
            "email_confirm": email_confirm,
            "user_metadata": {"full_name": full_name},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base}/admin/users", headers=self._headers, json=payload
            )
        if response.status_code >= 400:
            raise SupabaseAuthError(
                _extract_error(response, "Unable to create the account."),
                status_code=response.status_code,
            )
        return response.json()

    async def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base}/admin/users", headers=self._headers, params={"email": email}
            )
        if response.status_code >= 400:
            raise SupabaseAuthError(
                _extract_error(response, "Unable to look up the account."),
                status_code=response.status_code,
            )
        users = (response.json() or {}).get("users") or []
        for user in users:
            if (user.get("email") or "").lower() == email.lower():
                return user
        return users[0] if users else None

    async def set_password(self, user_id: str, password: str) -> None:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.put(
                f"{self._base}/admin/users/{user_id}",
                headers=self._headers,
                json={"password": password},
            )
        if response.status_code >= 400:
            raise SupabaseAuthError(
                _extract_error(response, "Unable to update the password."),
                status_code=response.status_code,
            )

    async def ban_user(self, user_id: str, *, banned: bool) -> None:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.put(
                f"{self._base}/admin/users/{user_id}",
                headers=self._headers,
                json={"ban_duration": "876000h" if banned else "none"},
            )
        if response.status_code >= 400:
            raise SupabaseAuthError(
                _extract_error(response, "Unable to update the account state."),
                status_code=response.status_code,
            )

    async def send_recovery(self, email: str, redirect_to: str) -> None:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base}/recover",
                headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
                json={"email": email, "redirect_to": redirect_to},
            )
        # Always succeed for the caller to avoid account enumeration.
        if response.status_code >= 500:  # pragma: no cover - upstream outage
            raise SupabaseAuthError("Unable to send the reset email.", status_code=503)


def _extract_error(response: httpx.Response, fallback: str) -> str:
    try:
        data = response.json()
    except Exception:
        return fallback
    if isinstance(data, dict):
        return str(
            data.get("msg") or data.get("message") or data.get("error_description") or fallback
        )
    return fallback


supabase_admin = SupabaseAdminClient()

