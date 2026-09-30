"""Singleton competition configuration / state machine row.

Server-side UTC timestamps are authoritative: the frontend countdown is purely
cosmetic and every write path re-reads this table through
``CompetitionService`` before accepting a submission.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONType, TimestampMixin
from app.models.enums import CompetitionStatus


class CompetitionSettings(Base, TimestampMixin):
    __tablename__ = "competition_settings"

    #: Always 1 — enforced by a check constraint so exactly one row exists.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    name: Mapped[str] = mapped_column(String(160), default="WANO CTF", nullable=False)
    tagline: Mapped[str] = mapped_column(String(240), default="Think. Hack. Capture. Defend.", nullable=False)
    venue: Mapped[str | None] = mapped_column(String(240))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(160))
    contact_phone: Mapped[str | None] = mapped_column(String(40))

    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registration_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    team_lock_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[CompetitionStatus] = mapped_column(
        SAEnum(CompetitionStatus, native_enum=False, length=16, validate_strings=True),
        default=CompetitionStatus.UPCOMING,
        nullable=False,
    )
    submissions_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scoreboard_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scoreboard_freeze_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    scoreboard_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    results_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    #: Rate limit: max submissions per minute per team per challenge (0 = disabled).
    submission_rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    #: Max total submissions a team may send to one challenge (0 = unlimited).
    max_attempts_per_challenge: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    default_hint_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_team_size: Mapped[int] = mapped_column(Integer, default=4, nullable=False)

    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_paused_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    banner_message: Mapped[str | None] = mapped_column(Text)
    status_reason: Mapped[str | None] = mapped_column(String(400))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    extra: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    __table_args__ = (
        CheckConstraint("id = 1", name="singleton_row"),
        CheckConstraint("end_at IS NULL OR start_at IS NULL OR end_at > start_at", name="valid_window"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CompetitionSettings status={self.status} start={self.start_at} end={self.end_at}>"
