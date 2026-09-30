"""Announcement payloads (info / warning / urgent broadcasts)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from app.models.enums import AnnouncementPriority
from app.schemas.common import ORMModel, TimestampedModel


class AnnouncementPublic(TimestampedModel):
    id: uuid.UUID
    title: str
    message: str
    priority: AnnouncementPriority
    is_pinned: bool = False
    published_at: datetime | None = None
    author_name: str | None = None
    is_read: bool = False


class AnnouncementCreate(ORMModel):
    title: Annotated[str, Field(min_length=3, max_length=200)]
    message: Annotated[str, Field(min_length=3, max_length=5000)]
    priority: AnnouncementPriority = AnnouncementPriority.INFO
    is_pinned: bool = False
    is_published: bool = True
    expires_at: datetime | None = None
    author_name: Annotated[str | None, Field(max_length=120)] = None

    @field_validator("title", "message")
    @classmethod
    def _clean(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned


class AnnouncementUpdate(ORMModel):
    title: Annotated[str | None, Field(min_length=3, max_length=200)] = None
    message: Annotated[str | None, Field(min_length=3, max_length=5000)] = None
    priority: AnnouncementPriority | None = None
    is_pinned: bool | None = None
    is_published: bool | None = None
    expires_at: datetime | None = None
