"""Competition configuration/state payloads (public + admin)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.models.enums import CompetitionStatus
from app.schemas.common import ORMModel


class CompetitionPublic(ORMModel):
    """Everything a participant (or the landing page) needs to know about state."""

    name: str
    tagline: str = "Think. Hack. Capture. Defend."
    venue: str | None = None
    timezone: str = "Asia/Kolkata"
    contact_email: str | None = None
    contact_phone: str | None = None

    status: CompetitionStatus
    start_at: datetime | None = None
    end_at: datetime | None = None
    server_time: datetime
    seconds_remaining: int | None = None
    seconds_until_start: int | None = None
    elapsed_seconds: int | None = None

    registration_open: bool = True
    submissions_enabled: bool = True
    team_lock_at: datetime | None = None
    teams_locked: bool = False
    scoreboard_public: bool = True
    scoreboard_frozen: bool = False
    scoreboard_freeze_minutes: int = 15
    results_published: bool = False
    banner_message: str | None = None

    submission_rate_limit_per_minute: int = 5
    max_attempts_per_challenge: int = 0
    default_hint_penalty: int = 0
    max_team_size: int = 4
    revision: int = 1


class CompetitionAdminUpdate(ORMModel):
    """Admin-editable competition configuration (all fields optional)."""

    name: Annotated[str | None, Field(min_length=3, max_length=160)] = None
    tagline: Annotated[str | None, Field(max_length=240)] = None
    venue: Annotated[str | None, Field(max_length=240)] = None
    timezone: Annotated[str | None, Field(max_length=64)] = None
    contact_email: Annotated[str | None, Field(max_length=160)] = None
    contact_phone: Annotated[str | None, Field(max_length=40)] = None

    start_at: datetime | None = None
    end_at: datetime | None = None
    team_lock_at: datetime | None = None

    registration_open: bool | None = None
    submissions_enabled: bool | None = None
    scoreboard_public: bool | None = None
    scoreboard_freeze_minutes: Annotated[int | None, Field(ge=0, le=240)] = None
    results_published: bool | None = None
    banner_message: Annotated[str | None, Field(max_length=2000)] = None

    submission_rate_limit_per_minute: Annotated[int | None, Field(ge=0, le=120)] = None
    max_attempts_per_challenge: Annotated[int | None, Field(ge=0, le=10_000)] = None
    default_hint_penalty: Annotated[int | None, Field(ge=0, le=1000)] = None
    max_team_size: Annotated[int | None, Field(ge=1, le=20)] = None

    @model_validator(mode="after")
    def _validate_window(self) -> CompetitionAdminUpdate:
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValueError("The end time must be after the start time.")
        return self


CompetitionAction = Literal["start", "pause", "resume", "end", "freeze", "unfreeze", "publish_results"]


class CompetitionStateChange(ORMModel):
    """Admin competition control (START / PAUSE / END / FREEZE / UNFREEZE)."""

    action: CompetitionAction
    reason: Annotated[str | None, Field(max_length=400)] = None
    disable_submissions: bool = True
