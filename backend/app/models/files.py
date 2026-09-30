"""Challenge attachment metadata + short-lived download tokens.

Uploaded artefacts are treated as hostile: they are stored (Supabase Storage or
local disk) and **never executed**; downloads always go through the API which
validates authorisation, extension, size and MIME type.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class ChallengeFile(Base, TimestampMixin):
    __tablename__ = "challenge_files"

    id: Mapped[uuid.UUID] = uuid_pk()
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream", nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64))
    label: Mapped[str | None] = mapped_column(String(160))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    download_count: Mapped[int] = mapped_column(default=0, nullable=False)

    challenge: Mapped[Challenge] = relationship(back_populates="files")  # noqa: F821

    __table_args__ = (Index("ix_challenge_files_challenge", "challenge_id"),)


class ChallengeFileToken(Base):
    """Single-use signed download token bound to a user/team."""

    __tablename__ = "challenge_file_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    token: Mapped[str] = mapped_column(String(96), unique=True, nullable=False, index=True)
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("challenge_files.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
