"""Admin panel payloads.

Admin schemas are the only place where a *flag* value may appear in a request
body, and it is write-only: ``AdminChallengeRow.has_flag`` is a boolean, and no
endpoint ever returns a flag in any form.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from app.models.enums import AdminRole, Difficulty, TeamStatus, UserRole
from app.schemas.common import ORMModel, TimestampedModel


# ------------------------------------------------------------------ statistics
class AdminStats(ORMModel):
    total_participants: int = 0
    total_teams: int = 0
    total_challenges: int = 0
    published_challenges: int = 0
    total_submissions: int = 0
    correct_submissions: int = 0
    incorrect_submissions: int = 0
    active_users_15m: int = 0
    active_teams_15m: int = 0
    solves_last_hour: int = 0
    teams_with_solves: int = 0
    average_solve_seconds: int | None = None
    server_time: datetime


class AdminLeaderboardRow(ORMModel):
    rank: int
    team_name: str
    score: int
    solved_count: int
    last_solve_at: datetime | None = None


# ------------------------------------------------------------------------ users
class AdminUserRow(TimestampedModel):
    id: uuid.UUID
    email: str
    full_name: str = ""
    college: str | None = None
    department: str | None = None
    year: str | None = None
    phone: str | None = None
    role: UserRole = UserRole.PARTICIPANT
    is_active: bool = True
    is_banned: bool = False
    ban_reason: str | None = None
    email_verified: bool = False
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    team_id: uuid.UUID | None = None
    team_name: str | None = None


class AdminUserUpdate(ORMModel):
    full_name: Annotated[str | None, Field(min_length=2, max_length=160)] = None
    college: Annotated[str | None, Field(max_length=200)] = None
    department: Annotated[str | None, Field(max_length=160)] = None
    year: Annotated[str | None, Field(max_length=40)] = None
    phone: Annotated[str | None, Field(max_length=32)] = None
    role: UserRole | None = None
    is_active: bool | None = None
    is_banned: bool | None = None
    ban_reason: Annotated[str | None, Field(max_length=400)] = None


class AdminAdminCreate(ORMModel):
    email: Annotated[str, Field(min_length=5, max_length=255)]
    display_name: Annotated[str, Field(min_length=2, max_length=160)]
    password: Annotated[str, Field(min_length=12, max_length=256)]
    role: AdminRole = AdminRole.ADMIN


class AdminAdminRow(TimestampedModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: AdminRole
    is_active: bool = True
    last_login_at: datetime | None = None
    last_login_ip: str | None = None


# ------------------------------------------------------------------------ teams
class AdminTeamMemberRow(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str = ""
    email: str | None = None
    role: str
    joined_at: datetime | None = None


class AdminTeamRow(TimestampedModel):
    id: uuid.UUID
    name: str
    team_code: str
    status: TeamStatus
    status_reason: str | None = None
    score: int = 0
    solved_count: int = 0
    hint_penalty: int = 0
    college: str | None = None
    member_count: int = 0
    captain_id: uuid.UUID | None = None
    captain_email: str | None = None
    last_solve_at: datetime | None = None


class AdminTeamDetail(AdminTeamRow):
    members: list[AdminTeamMemberRow] = Field(default_factory=list)


class AdminTeamUpdate(ORMModel):
    name: Annotated[str | None, Field(min_length=3, max_length=40)] = None
    college: Annotated[str | None, Field(max_length=200)] = None
    status: TeamStatus | None = None
    status_reason: Annotated[str | None, Field(max_length=400)] = None


class ScoringAdjustment(ORMModel):
    """Manual score change (bonus / penalty) with a mandatory reason."""

    delta: Annotated[int, Field(ge=-100_000, le=100_000)]
    reason: Annotated[str, Field(min_length=3, max_length=400)]


# ------------------------------------------------------------------- challenges
class AdminChallengeRow(TimestampedModel):
    """Admin projection — reveals only whether a flag exists, never its value."""

    id: uuid.UUID
    title: str
    slug: str
    category_id: uuid.UUID
    category_slug: str = ""
    category_name: str = ""
    difficulty: Difficulty
    points: int
    description: str = ""
    visible: bool = False
    is_demo: bool = False
    author: str | None = None
    connection_info: str | None = None
    flag_format_hint: str | None = None
    requires_team: bool = True
    max_attempts_per_minute: int | None = None
    solved_count: int = 0
    hint_count: int = 0
    file_count: int = 0
    has_flag: bool = True
    released_at: datetime | None = None


class AdminHintInput(ORMModel):
    text: Annotated[str, Field(min_length=3, max_length=2000)]
    cost: Annotated[int, Field(ge=0, le=10_000)] = 0
    display_order: Annotated[int, Field(ge=0, le=1000)] = 0
    is_visible: bool = True


class AdminHintUpdate(ORMModel):
    text: Annotated[str | None, Field(min_length=3, max_length=2000)] = None
    cost: Annotated[int | None, Field(ge=0, le=10_000)] = None
    display_order: Annotated[int | None, Field(ge=0, le=1000)] = None
    is_visible: bool | None = None


class AdminHintRow(ORMModel):
    id: uuid.UUID
    challenge_id: uuid.UUID
    text: str
    cost: int = 0
    display_order: int = 0
    is_visible: bool = True
    unlocks: int = 0


class AdminChallengeCreate(ORMModel):
    title: Annotated[str, Field(min_length=3, max_length=160)]
    slug: Annotated[str | None, Field(max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")] = None
    category_id: uuid.UUID | None = None
    category_slug: Annotated[str | None, Field(max_length=60)] = None
    description: Annotated[str, Field(min_length=3, max_length=20_000)]
    difficulty: Difficulty = Difficulty.EASY
    points: Annotated[int, Field(ge=0, le=100_000)] = 100
    #: Write-only. Stored as HMAC-SHA256(flag, FLAG_PEPPER) — never returned.
    flag: Annotated[str, Field(min_length=3, max_length=512)]
    flag_format_hint: Annotated[str | None, Field(max_length=80)] = "WANO{...}"
    connection_info: Annotated[str | None, Field(max_length=300)] = None
    author: Annotated[str | None, Field(max_length=120)] = None
    visible: bool = False
    requires_team: bool = True
    max_attempts_per_minute: Annotated[int | None, Field(ge=1, le=120)] = None
    released_at: datetime | None = None
    is_demo: bool = False
    hints: list[AdminHintInput] = Field(default_factory=list)

    @field_validator("description", "title")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip()


class AdminChallengeUpdate(ORMModel):
    title: Annotated[str | None, Field(min_length=3, max_length=160)] = None
    slug: Annotated[str | None, Field(max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")] = None
    category_id: uuid.UUID | None = None
    category_slug: Annotated[str | None, Field(max_length=60)] = None
    description: Annotated[str | None, Field(min_length=3, max_length=20_000)] = None
    difficulty: Difficulty | None = None
    points: Annotated[int | None, Field(ge=0, le=100_000)] = None
    #: Provide to rotate the flag; omit to keep the existing digest.
    flag: Annotated[str | None, Field(min_length=3, max_length=512)] = None
    flag_format_hint: Annotated[str | None, Field(max_length=80)] = None
    connection_info: Annotated[str | None, Field(max_length=300)] = None
    author: Annotated[str | None, Field(max_length=120)] = None
    visible: bool | None = None
    requires_team: bool | None = None
    max_attempts_per_minute: Annotated[int | None, Field(ge=1, le=120)] = None
    released_at: datetime | None = None


class AdminCategoryInput(ORMModel):
    slug: Annotated[str, Field(min_length=2, max_length=60, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
    name: Annotated[str, Field(min_length=2, max_length=80)]
    description: Annotated[str | None, Field(max_length=1000)] = None
    icon: Annotated[str, Field(max_length=60)] = "Puzzle"
    accent: Annotated[str, Field(max_length=20)] = "cyan"
    display_order: Annotated[int, Field(ge=0, le=999)] = 0
    is_visible: bool = True


class AdminCategoryUpdate(ORMModel):
    name: Annotated[str | None, Field(min_length=2, max_length=80)] = None
    description: Annotated[str | None, Field(max_length=1000)] = None
    icon: Annotated[str | None, Field(max_length=60)] = None
    accent: Annotated[str | None, Field(max_length=20)] = None
    display_order: Annotated[int | None, Field(ge=0, le=999)] = None
    is_visible: bool | None = None


# ------------------------------------------------------------------ submissions
class AdminSubmissionRow(ORMModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str = ""
    challenge_id: uuid.UUID
    challenge_title: str = ""
    challenge_slug: str = ""
    submitted_by: uuid.UUID | None = None
    submitted_by_name: str | None = None
    submitted_flag_masked: str | None = None
    is_correct: bool = False
    points_awarded: int = 0
    attempt_number: int = 1
    ip_address: str | None = None
    submitted_at: datetime


class AdminSolveRow(ORMModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str = ""
    challenge_id: uuid.UUID
    challenge_title: str = ""
    points: int = 0
    first_blood: bool = False
    solved_at: datetime


class AuditLogRow(ORMModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None = None
    actor_type: str = "system"
    actor_email: str | None = None
    action: str
    target_type: str | None = None
    target_id: str | None = None
    details: dict = Field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime


class ActivityEventRow(ORMModel):
    """Anti-cheat signal row surfaced for *human* review (never auto-bans)."""

    id: uuid.UUID
    team_id: uuid.UUID | None = None
    team_name: str | None = None
    user_id: uuid.UUID | None = None
    challenge_id: uuid.UUID | None = None
    event_type: str
    severity: str = "info"
    details: dict = Field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime


