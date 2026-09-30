"""Authentication payloads.

Sensitive note: ``AuthConfigResponse`` intentionally exposes only the public
Supabase URL + anon key (which are public by design) so the browser can talk to
Supabase Auth directly. The service-role key, flag pepper and JWT secrets never
leave the server.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORMModel, normalize_email
from app.security.passwords import password_strength_errors


class AuthConfigResponse(BaseModel):
    """Tells the frontend which auth provider is active."""

    provider: Literal["supabase", "local"]
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    email_verification_required: bool = True
    google_oauth_enabled: bool = False
    password_reset_enabled: bool = True


class LocalRegisterRequest(BaseModel):
    """Only accepted when ``DEV_AUTH_ENABLED=true`` (never in production)."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=256)]
    full_name: Annotated[str, Field(min_length=2, max_length=160)]
    college: Annotated[str | None, Field(max_length=200)] = None
    department: Annotated[str | None, Field(max_length=160)] = None
    year: Annotated[str | None, Field(max_length=40)] = None
    phone: Annotated[str | None, Field(max_length=32)] = None
    team_name: Annotated[str | None, Field(max_length=100)] = None
    is_team_leader: bool = False

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("full_name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Please provide your full name.")
        return cleaned

    @field_validator("password")
    @classmethod
    def _strong(cls, value: str) -> str:
        problems = password_strength_errors(value)
        if problems:
            raise ValueError(problems[0])
        return value


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=256)]

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime
    refresh_token: str | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return normalize_email(value)


class PasswordResetConfirm(BaseModel):
    token: str | None = None
    email: EmailStr | None = None
    new_password: Annotated[str, Field(min_length=8, max_length=256)]

    @field_validator("new_password")
    @classmethod
    def _strong(cls, value: str) -> str:
        problems = password_strength_errors(value)
        if problems:
            raise ValueError(problems[0])
        return value


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=256)]
    totp: Annotated[str | None, Field(max_length=12)] = None

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return normalize_email(value)


class AdminIdentity(ORMModel):
    id: str
    email: str
    display_name: str
    role: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime
    admin: AdminIdentity
