"""Announcement broadcast + per-participant read tracking."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import NotFound
from app.models.accounts import AnnouncementRead
from app.models.announcements import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementPublic, AnnouncementUpdate


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def to_public(row: Announcement, *, is_read: bool = False) -> AnnouncementPublic:
    return AnnouncementPublic(
        id=row.id,
        title=row.title,
        message=row.message,
        priority=row.priority,
        is_pinned=row.is_pinned,
        published_at=_aware(row.published_at),
        author_name=row.author_name,
        is_read=is_read,
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
    )


async def list_published(
    session: AsyncSession, *, user_id: uuid.UUID | None = None, limit: int = 50
) -> list[AnnouncementPublic]:
    """Pinned first, then newest. Expired announcements drop out automatically."""
    now = _now()
    stmt = (
        select(Announcement)
        .where(
            Announcement.is_published.is_(True),
            (Announcement.expires_at.is_(None)) | (Announcement.expires_at > now),
        )
        .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).scalars())

    read_ids: set[uuid.UUID] = set()
    if user_id is not None and rows:
        read_ids = set(
            (
                await session.execute(
                    select(AnnouncementRead.announcement_id).where(
                        AnnouncementRead.user_id == user_id
                    )
                )
            ).scalars()
        )
    return [to_public(row, is_read=row.id in read_ids) for row in rows]


async def mark_read(
    session: AsyncSession, *, announcement_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    existing = (
        await session.execute(
            select(AnnouncementRead).where(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(AnnouncementRead(announcement_id=announcement_id, user_id=user_id))
    await session.flush()


async def create_announcement(
    session: AsyncSession, payload: AnnouncementCreate, *, admin_id: uuid.UUID | None
) -> Announcement:
    row = Announcement(
        title=payload.title,
        message=payload.message,
        priority=payload.priority,
        is_published=payload.is_published,
        is_pinned=payload.is_pinned,
        expires_at=payload.expires_at,
        author_name=payload.author_name,
        created_by=admin_id,
        published_at=_now() if payload.is_published else None,
    )
    session.add(row)
    await session.flush()
    return row


async def update_announcement(
    session: AsyncSession, announcement_id: uuid.UUID, payload: AnnouncementUpdate
) -> Announcement:
    row = await session.get(Announcement, announcement_id)
    if row is None:
        raise NotFound("That announcement could not be found.")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(row, field, value)
    # Re-publishing re-stamps the broadcast time so it resurfaces on clients.
    if data.get("is_published") and row.published_at is None:
        row.published_at = _now()
    await session.flush()
    return row


async def delete_announcement(session: AsyncSession, announcement_id: uuid.UUID) -> None:
    row = await session.get(Announcement, announcement_id)
    if row is None:
        raise NotFound("That announcement could not be found.")
    await session.delete(row)
    await session.flush()
