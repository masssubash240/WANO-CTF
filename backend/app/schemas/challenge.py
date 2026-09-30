"""Challenge payloads.

FLAG CONTRACT: no schema in this module (or anywhere else) exposes
``flag``/``flag_hash``. ``FlagSubmitRequest`` is write-only, and
``FlagSubmitResponse`` returns only booleans/points — the flag itself is never
echoed, even on success.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from app.models.enums import Difficulty
from app.schemas.common import ORMModel, TimestampedModel
from app.security.flags import normalize_flag


class CategoryPublic(TimestampedModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    icon: str = "Puzzle"
    accent: str = "cyan"
    display_order: int = 0
    challenge_count: int = 0
    solved_count: int = 0
    total_points: int = 0


class ChallengeFilePublic(ORMModel):
    id: uuid.UUID
    filename: str
    label: str | None = None
    size_bytes: int = 0
    mime_type: str = "application/octet-stream"
    sha256: str | None = None
    download_url: str


class ChallengeHintPublic(ORMModel):
    id: uuid.UUID
    display_order: int = 0
    cost: int = 0
    is_unlocked: bool = False
    #: ``None`` while locked — the hint text is only released after unlocking.
    text: str | None = None


class ChallengeSummary(ORMModel):
    """List/card projection (never contains description or flags)."""

    id: uuid.UUID
    title: str
    slug: str
    category_slug: str
    category_name: str
    category_icon: str = "Puzzle"
    difficulty: Difficulty
    points: int
    solved_count: int = 0
    is_solved: bool = False
    hint_count: int = 0
    file_count: int = 0
    author: str | None = None


class ChallengeDetail(ChallengeSummary):
    description: str = ""
    connection_info: str | None = None
    flag_format_hint: str | None = "WANO{...}"
    hints: list[ChallengeHintPublic] = Field(default_factory=list)
    files: list[ChallengeFilePublic] = Field(default_factory=list)
    attempts_used: int = 0
    max_attempts: int | None = None
    attempts_remaining: int | None = None
    solved_at: datetime | None = None
    points_awarded: int | None = None
    first_blood: bool = False


class SolveRecord(ORMModel):
    challenge_id: uuid.UUID
    challenge_title: str
    challenge_slug: str
    category_slug: str
    category_name: str
    points: int
    hint_penalty: int = 0
    solved_at: datetime
    first_blood: bool = False


class FlagSubmitRequest(ORMModel):
    flag: Annotated[str, Field(min_length=1, max_length=512)]

    @field_validator("flag")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = normalize_flag(value)
        if not normalized:
            raise ValueError("Please enter a flag before submitting.")
        return normalized


class FlagSubmitResponse(ORMModel):
    """Never includes the expected flag — only the verdict and score deltas."""

    correct: bool
    message: str
    points_awarded: int = 0
    already_solved: bool = False
    challenge_slug: str | None = None
    team_score: int | None = None
    team_rank: int | None = None
    solved_count: int | None = None
    attempts_remaining: int | None = None
    retry_after: int | None = None


class HintUnlockResponse(ORMModel):
    hint_id: uuid.UUID
    text: str
    cost_paid: int = 0
    team_score: int = 0
    total_hint_penalty: int = 0
