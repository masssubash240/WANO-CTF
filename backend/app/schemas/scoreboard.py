"""Scoreboard / results payloads.

The public scoreboard is deliberately lean (no emails, no phone numbers, no
per-member data) and served from denormalised counters instead of aggregating
the submissions table.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CompetitionStatus
from app.schemas.challenge import SolveRecord
from app.schemas.common import ORMModel


class ScoreboardEntry(ORMModel):
    rank: int
    team_id: uuid.UUID | None = None
    team_name: str
    college: str | None = None
    score: int = 0
    solved_count: int = 0
    last_solve_at: datetime | None = None
    member_count: int = 0
    #: True only for scoreboard entries the caller's team owns.
    is_own_team: bool = False


class ScoreboardMeta(BaseModel):
    status: CompetitionStatus
    start_at: datetime | None = None
    end_at: datetime | None = None
    server_time: datetime
    seconds_remaining: int | None = None


class ScoreboardResponse(BaseModel):
    entries: list[ScoreboardEntry] = Field(default_factory=list)
    total_teams: int = 0
    frozen: bool = False
    frozen_since: datetime | None = None
    public: bool = True
    generated_at: datetime
    meta: ScoreboardMeta
    my_team: ScoreboardEntry | None = None


class TeamSolveDetail(BaseModel):
    """Results page breakdown for one team."""

    rank: int
    team_id: uuid.UUID
    team_name: str
    college: str | None = None
    score: int
    solved_count: int
    hint_penalty: int = 0
    last_solve_at: datetime | None = None
    first_bloods: int = 0
    solves: list[SolveRecord] = Field(default_factory=list)


class ResultsResponse(BaseModel):
    published: bool
    status: CompetitionStatus
    generated_at: datetime
    entries: list[TeamSolveDetail] = Field(default_factory=list)


class ScoreboardPoint(BaseModel):
    """Single point of the score-progression chart."""

    t: datetime
    score: int
