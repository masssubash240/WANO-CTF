"""Public file download route for challenge attachments."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import SessionDep
from app.config import settings
from app.errors import NotFound
from app.models.files import ChallengeFile

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("/{challenge_slug}/files/{file_id}/download")
async def download_challenge_file(
    challenge_slug: str,
    file_id: uuid.UUID,
    session: SessionDep,
):
    stmt = select(ChallengeFile).where(ChallengeFile.id == file_id).limit(1)
    file_record = (await session.execute(stmt)).scalar_one_or_none()
    if file_record is None:
        raise NotFound("Requested file does not exist.", code="file_not_found")

    disk_path = Path(file_record.storage_path)
    if not disk_path.is_absolute():
        from app.services.files import storage_root
        disk_path = storage_root() / disk_path

    if not disk_path.exists():
        raise NotFound("The file attachment is not available on disk.", code="file_missing")

    return FileResponse(
        path=disk_path,
        filename=file_record.filename,
        media_type=file_record.mime_type or "application/octet-stream",
    )
