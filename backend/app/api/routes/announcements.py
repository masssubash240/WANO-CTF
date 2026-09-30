"""Public announcement feed + per-user read tracking."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep
from app.schemas.announcement import AnnouncementPublic
from app.schemas.common import Message
from app.security.deps import Principal, get_active_principal, get_principal_optional
from app.services.announcements import list_published, mark_read

router = APIRouter(prefix="/announcements", tags=["announcements"])

OptionalPrincipal = Annotated[Principal | None, Depends(get_principal_optional)]
ActivePrincipal = Annotated[Principal, Depends(get_active_principal)]


@router.get("", response_model=list[AnnouncementPublic])
async def read_announcements(
    principal: OptionalPrincipal,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AnnouncementPublic]:
    user_id = principal.user_id if principal else None
    return await list_published(session, user_id=user_id, limit=limit)


@router.post("/{announcement_id}/read", response_model=Message)
async def post_mark_read(
    announcement_id: UUID,
    principal: ActivePrincipal,
    session: SessionDep,
) -> Message:
    await mark_read(session, announcement_id=announcement_id, user_id=principal.user_id)
    await session.commit()
    return Message(message="Marked as read.")


@router.get("/unread-count", response_model=dict)
async def read_unread_count(
    principal: ActivePrincipal,
    session: SessionDep,
) -> dict:
    items = await list_published(session, user_id=principal.user_id, limit=100)
    return {"unread": sum(1 for item in items if not item.is_read), "total": len(items)}
