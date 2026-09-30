"""Challenge attachment storage.

Uploaded artefacts are treated as hostile: they are written to storage and
**never executed**. Downloads are only ever served through the API, which
authorises the caller and then redeems a short-lived, single-use token.
"""

from __future__ import annotations

import hashlib
import mimetypes
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import NotFound, StorageError
from app.models.files import ChallengeFile, ChallengeFileToken

TOKEN_TTL_MINUTES = 10


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def storage_root() -> Path:
    return Path(settings.local_storage_dir).resolve()


def safe_local_path(storage_path: str) -> Path:
    """Resolve a stored path and refuse anything that escapes the storage root."""
    root = storage_root()
    candidate = (root / storage_path).resolve()
    if not candidate.is_relative_to(root):
        raise NotFound("That file is no longer available.")
    return candidate


def validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extension_set:
        raise StorageError(
            f"Files of type '{suffix or 'unknown'}' are not allowed.",
            code="extension_not_allowed",
        )
    return suffix


def guess_mime(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


async def store_upload(
    session: AsyncSession,
    *,
    challenge_id: uuid.UUID,
    filename: str,
    data: bytes,
    uploaded_by: uuid.UUID | None,
    label: str | None = None,
) -> ChallengeFile:
    """Persist an upload locally and register its metadata."""
    validate_extension(filename)
    limit = settings.max_upload_mb * 1024 * 1024
    if len(data) > limit:
        raise StorageError(
            f"Files must be {settings.max_upload_mb} MB or smaller.", code="file_too_large"
        )
    if not data:
        raise StorageError("The uploaded file is empty.", code="empty_file")

    digest = hashlib.sha256(data).hexdigest()
    safe_name = Path(filename).name  # never trust a client-supplied path
    relative = f"challenges/{challenge_id}/{uuid.uuid4().hex}-{safe_name}"
    target = safe_local_path(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

    row = ChallengeFile(
        challenge_id=challenge_id,
        filename=safe_name,
        storage_path=relative,
        storage_backend="local",
        size_bytes=len(data),
        mime_type=guess_mime(safe_name),
        sha256=digest,
        label=label,
        uploaded_by=uploaded_by,
    )
    session.add(row)
    await session.flush()
    return row


async def issue_download_token(
    session: AsyncSession,
    *,
    file: ChallengeFile,
    user_id: uuid.UUID | None,
    team_id: uuid.UUID | None,
) -> ChallengeFileToken:
    row = ChallengeFileToken(
        token=secrets.token_urlsafe(36),
        file_id=file.id,
        user_id=user_id,
        team_id=team_id,
        expires_at=_now() + timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    session.add(row)
    await session.flush()
    return row


async def redeem_token(session: AsyncSession, token: str) -> ChallengeFileToken:
    """Single-use redemption: unknown, reused or expired tokens are all rejected."""
    row = (
        await session.execute(
            select(ChallengeFileToken).where(ChallengeFileToken.token == token).limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFound("That download link is invalid.")
    if row.used_at is not None:
        raise NotFound("That download link has already been used.")
    expires = _aware(row.expires_at)
    if expires is not None and expires <= _now():
        raise NotFound("That download link has expired.")
    return row


async def mark_token_used(session: AsyncSession, row: ChallengeFileToken) -> None:
    row.used_at = _now()
    await session.flush()


async def get_file_or_404(session: AsyncSession, file_id: uuid.UUID) -> ChallengeFile:
    row = await session.get(ChallengeFile, file_id)
    if row is None:
        raise NotFound("That file could not be found.")
    return row
