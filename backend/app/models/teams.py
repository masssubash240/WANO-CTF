"""Teams, membership and per-team aggregate scoring columns."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.enums import TeamRole, TeamStatus


class Team(Base, TimestampMixin):
    """The scoring unit for WANO CTF.

    ``score`` / ``solved_count`` are denormalised counters maintained
    transactionally by the scoring service so the public leaderboard never has
    to aggregate the whole ``submissions`` table.
    """

    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name_normalized: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    team_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(300))
    captain_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    college: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[TeamStatus] = mapped_column(
        SAEnum(TeamStatus, native_enum=False, length=24, validate_strings=True),
        default=TeamStatus.ACTIVE,
        nullable=False,
    )
    status_reason: Mapped[str | None] = mapped_column(String(400))

    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    hint_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    last_solve_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    members: Mapped[list[TeamMember]] = relationship(
        back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )
    captain: Mapped[Profile] = relationship(lazy="joined")  # noqa: F821

    __table_args__ = (
        CheckConstraint("score >= 0", name="score_non_negative"),
        CheckConstraint("solved_count >= 0", name="solved_count_non_negative"),
        Index("ix_teams_leaderboard", "score", "last_solve_at"),
        Index("ix_teams_status_score", "status", "score"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Team {self.name} score={self.score}>"


class TeamMember(Base, TimestampMixin):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = uuid_pk()
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[TeamRole] = mapped_column(
        SAEnum(TeamRole, native_enum=False, length=24, validate_strings=True),
        default=TeamRole.MEMBER,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    team: Mapped[Team] = relationship(back_populates="members")
    user: Mapped[Profile] = relationship(back_populates="memberships", lazy="joined")  # noqa: F821

    __table_args__ = (
        # A participant can only belong to one team.
        UniqueConstraint("user_id", name="uq_team_members_user_id"),
        UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
        Index("ix_team_members_team", "team_id"),
    )
