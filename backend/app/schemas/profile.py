"""Participant profile payloads.

Public projection deliberately omits email, phone and any internal flag
(``is_banned``, ``ban_reason``) unless the caller is the profile owner or an admin.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from app.schemas.common import ORMModel, TimestampedModel
from app.schemas.team import TeamMembershipSummary


class ProfileUpdate(ORMModel):
    """Self-service profile edit — role/status fields are intentionally absent."""

    full_name: Annotated[str | None, Field(min_length=2, max_length=160)] = None
    college: Annotated[str | None, Field(max_length=200)] = None
    department: Annotated[str | None, Field(max_length=160)] = None
    year: Annotated[str | None, Field(max_length=40)] = None
    phone: Annotated[str | None, Field(max_length=32)] = None

    @field_validator("full_name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Please provide your full name.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def _clean_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = "".join(ch for ch in value if ch.isdigit() or ch in "+- ()")
        return digits.strip()[:32] or None


class ProfilePublic(TimestampedModel):
    """Safe projection for public/team views — no email, phone or moderation data."""

    id: uuid.UUID
    full_name: str
    college: str | None = None
    department: str | None = None
    year: str | None = None


class ProfileSelf(TimestampedModel):
    """Full profile for the authenticated owner."""

    id: uuid.UUID
    email: str
    full_name: str
    college: str | None = None
    department: str | None = None
    year: str | None = None
    phone: str | None = None
    role: str
    email_verified: bool = False
    is_active: bool = True
    is_banned: bool = False
    ban_reason: str | None = None
    last_login_at: datetime | None = None


class SessionResponse(ORMModel):
    """``GET /api/users/me`` — everything the dashboard needs in one round trip."""

    profile: ProfileSelf
    team: TeamMembershipSummary | None = None
    is_captain: bool = False
    is_admin: bool = False
    auth_provider: str = "supabase"
    permissions: dict[str, bool] = Field(default_factory=dict)
