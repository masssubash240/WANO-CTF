"""Flag submissions and immutable solve records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JSONType, uuid_pk


class Submission(Base):
    """Every flag attempt (correct *and* incorrect) for anti-abuse monitoring.

    The submitted value is truncated + masked before storage: we keep just
    enough for forensics (prefix/length) without persisting a usable flag dump.
    """

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = uuid_pk()
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL")
    )
    submitted_flag_masked: Mapped[str | None] = mapped_column(String(80))
    submitted_flag_sha256: Mapped[str | None] = mapped_column(String(64))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(400))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    challenge: Mapped[Challenge] = relationship(lazy="joined")  # noqa: F821
    team: Mapped[Team] = relationship(lazy="joined")  # noqa: F821

    __table_args__ = (
        Index("ix_submissions_team_challenge", "team_id", "challenge_id"),
        Index("ix_submissions_challenge_correct", "challenge_id", "is_correct"),
        Index("ix_submissions_submitted_at", "submitted_at"),
        Index("ix_submissions_team_time", "team_id", "submitted_at"),
    )


class Solve(Base):
    """One row per solved challenge per team — the authoritative score source."""

    __tablename__ = "solves"

    id: Mapped[uuid.UUID] = uuid_pk()
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    solved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL")
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hint_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submission_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    solved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    is_first_blood: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    challenge: Mapped[Challenge] = relationship(lazy="joined")  # noqa: F821
    team: Mapped[Team] = relationship(lazy="joined")  # noqa: F821

    __table_args__ = (
        # Hard guarantee: one score per team per challenge (also enforced in SQL).
        UniqueConstraint("team_id", "challenge_id", name="uq_solves_team_challenge"),
        Index("ix_solves_team", "team_id"),
        Index("ix_solves_challenge_time", "challenge_id", "solved_at"),
        Index("ix_solves_solved_at", "solved_at"),
    )


class ScoringEvent(Base):
    """Manual score adjustments by admins (bonuses / penalties) + audit trail."""

    __tablename__ = "scoring_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    details: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
