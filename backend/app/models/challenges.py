"""Categories, challenges, hints and challenge attachments."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
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
from typing import TYPE_CHECKING

from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.enums import Difficulty

if TYPE_CHECKING:  # avoids a circular import at module load
    from app.models.files import ChallengeFile


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(60), default="Puzzle", nullable=False)
    accent: Mapped[str] = mapped_column(String(20), default="cyan", nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    challenges: Mapped[list[Challenge]] = relationship(back_populates="category")


class Challenge(Base, TimestampMixin):
    """A single CTF task.

    SECURITY: the plaintext flag is **never** stored. Only
    ``flag_hash = HMAC-SHA256(normalize(flag), FLAG_PEPPER)`` is persisted and it
    is never serialised by any schema (see ``ChallengePublic``).
    """

    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[Difficulty] = mapped_column(
        SAEnum(Difficulty, native_enum=False, length=16, validate_strings=True),
        default=Difficulty.EASY,
        nullable=False,
    )
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    flag_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    flag_format_hint: Mapped[str | None] = mapped_column(String(80), default="WANO{...}")
    connection_info: Mapped[str | None] = mapped_column(String(300))
    author: Mapped[str | None] = mapped_column(String(120))
    visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    requires_team: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_attempts_per_minute: Mapped[int | None] = mapped_column(Integer)
    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))

    category: Mapped[Category] = relationship(back_populates="challenges", lazy="joined")
    hints: Mapped[list[ChallengeHint]] = relationship(
        back_populates="challenge",
        cascade="all, delete-orphan",
        order_by="ChallengeHint.display_order",
        lazy="selectin",
    )
    files: Mapped[list[ChallengeFile]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("points >= 0", name="points_non_negative"),
        Index("ix_challenges_category_visible", "category_id", "visible"),
        Index("ix_challenges_visible_points", "visible", "points"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Challenge {self.slug} ({self.points}p)>"


class ChallengeHint(Base, TimestampMixin):
    __tablename__ = "challenge_hints"

    id: Mapped[uuid.UUID] = uuid_pk()
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    challenge: Mapped[Challenge] = relationship(back_populates="hints")

    __table_args__ = (CheckConstraint("cost >= 0", name="cost_non_negative"),)


class HintUnlock(Base):
    """Records a team spending points on a hint (append-only audit)."""

    __tablename__ = "hint_unlocks"

    id: Mapped[uuid.UUID] = uuid_pk()
    hint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenge_hints.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    cost_paid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("hint_id", "team_id", name="uq_hint_unlocks_hint_team"),)
