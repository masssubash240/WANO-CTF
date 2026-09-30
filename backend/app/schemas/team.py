"""Team payloads.

``team_code`` is the invite secret used to join a team. It is only ever returned
to members of that team (never in public listings) so teams cannot be hijacked.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from app.models.enums import TeamRole, TeamStatus
from app.schemas.common import ORMModel, TimestampedModel

TEAM_CODE_PATTERN = r"^[A-Z0-9]{4,16}$"


class TeamMemberPublic(TimestampedModel):
    """Member view — no email or phone (privacy by default)."""

    id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole
    joined_at: datetime | None = None
    display_name: str = ""
    college: str | None = None


class TeamPublic(TimestampedModel):
    id: uuid.UUID
    name: str
    college: str | None = None
    status: TeamStatus
    score: int = 0
    solved_count: int = 0
    member_count: int = 0
    last_solve_at: datetime | None = None


class TeamMembershipSummary(ORMModel):
    """Compact team block embedded in the session/dashboard response."""

    id: uuid.UUID
    name: str
    team_code: str | None = None
    status: TeamStatus
    score: int = 0
    rank: int | None = None
    solved_count: int = 0
    hint_penalty: int = 0
    member_count: int = 0
    max_team_size: int = 4
    role: TeamRole = TeamRole.MEMBER
    is_captain: bool = False
    members_locked: bool = False
    members: list[TeamMemberPublic] = Field(default_factory=list)


class TeamDetail(TeamPublic):
    team_code: str | None = None
    captain_id: uuid.UUID
    captain_name: str | None = None
    members: list[TeamMemberPublic] = Field(default_factory=list)
    is_captain: bool = False
    members_locked: bool = False


class TeamCreateRequest(ORMModel):
    name: Annotated[str, Field(min_length=3, max_length=40)]
    description: Annotated[str | None, Field(max_length=300)] = None
    college: Annotated[str | None, Field(max_length=200)] = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("Team name must be at least 3 characters long.")
        if not any(ch.isalnum() for ch in cleaned):
            raise ValueError("Team name must contain letters or numbers.")
        if cleaned.lower() in {"admin", "organizer", "organiser", "wano", "ctf", "system"}:
            raise ValueError("That team name is reserved.")
        return cleaned


class TeamJoinRequest(ORMModel):
    team_code: Annotated[str, Field(min_length=4, max_length=16, pattern=TEAM_CODE_PATTERN)]

    @field_validator("team_code")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.strip().upper()


class TeamUpdateRequest(ORMModel):
    description: Annotated[str | None, Field(max_length=300)] = None
    college: Annotated[str | None, Field(max_length=200)] = None
