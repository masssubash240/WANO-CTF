"""Append-only audit trail, login telemetry and anti-cheat signal helpers.

Every privileged action and authentication outcome funnels through here so the
audit tables stay authoritative. These helpers deliberately never raise: losing
telemetry must never take down a request.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.accounts import ActivityEvent, AuditLog, LoginEvent
from app.models.enums import ActorType

logger = logging.getLogger("wano.audit")


async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = ActorType.SYSTEM,
    actor_email: str | None = None,
    target_type: str | None = None,
    target_id: str | uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog | None:
    """Write one audit row. No-ops (and never fails) when auditing is disabled."""
    if not settings.audit_log_enabled:
        return None
    row = AuditLog(
        actor_id=actor_id,
        actor_type=actor_type,
        actor_email=actor_email,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(row)
    try:
        await session.flush()
    except Exception:  # pragma: no cover - telemetry must not break the request
        logger.warning("Failed to write audit entry for action=%s", action, exc_info=True)
        return None
    return row


async def record_login_event(
    session: AsyncSession,
    *,
    success: bool,
    email: str | None = None,
    user_id: uuid.UUID | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Record a sign-in attempt — persisted even for failures (anti-brute-force)."""
    session.add(
        LoginEvent(
            user_id=user_id,
            email=email.lower() if email else None,
            success=success,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )
    try:
        await session.flush()
    except Exception:  # pragma: no cover
        logger.warning("Failed to record login event", exc_info=True)


async def record_activity(
    session: AsyncSession,
    *,
    event_type: str,
    team_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    challenge_id: uuid.UUID | None = None,
    severity: str = "info",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> ActivityEvent:
    """Append an anti-cheat signal for later *human* review (never auto-ban)."""
    row = ActivityEvent(
        team_id=team_id,
        user_id=user_id,
        challenge_id=challenge_id,
        event_type=event_type,
        severity=severity,
        details=details or {},
        ip_address=ip_address,
    )
    session.add(row)
    await session.flush()
    return row
