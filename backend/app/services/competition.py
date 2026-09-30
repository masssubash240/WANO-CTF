"""Competition state machine.

The server clock and UTC timestamps in ``competition_settings`` are the single
source of truth. The frontend countdown is cosmetic only — every submission
re-checks state here, so changing a laptop clock cannot un-end a CTF.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_settings
from app.errors import (
    BadRequest,
    CompetitionEnded,
    CompetitionNotStarted,
    CompetitionPaused,
)
from app.models.competition import CompetitionSettings
from app.models.enums import CompetitionStatus
from app.schemas.competition import CompetitionAdminUpdate, CompetitionPublic

SINGLETON_ID = 1


@dataclass(slots=True)
class CompetitionState:
    status: CompetitionStatus
    server_time: datetime
    start_at: datetime | None
    end_at: datetime | None
    seconds_remaining: int | None
    seconds_until_start: int | None
    elapsed_seconds: int | None
    submissions_open: bool
    teams_locked: bool
    scoreboard_frozen: bool
    registration_open: bool
    results_published: bool


def utcnow() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def get_settings_row(session: AsyncSession, *, create: bool = True) -> CompetitionSettings:
    """Load the singleton row, creating a sane default on first boot."""
    row = await session.get(CompetitionSettings, SINGLETON_ID)
    if row is None and create:
        row = CompetitionSettings(id=SINGLETON_ID, timezone=app_settings.ctf_timezone)
        session.add(row)
        await session.flush()
    if row is None:  # pragma: no cover - defensive
        raise BadRequest("Competition settings are not initialised.")
    return row


def compute_state(row: CompetitionSettings, *, now: datetime | None = None) -> CompetitionState:
    """Derive the effective state (handles clock-driven auto start/end)."""
    current = now or utcnow()
    start_at = _aware(row.start_at)
    end_at = _aware(row.end_at)

    seconds_until_start: int | None = None
    if start_at:
        seconds_until_start = int((start_at - current).total_seconds())

    seconds_remaining: int | None = None
    if end_at:
        seconds_remaining = int((end_at - current).total_seconds())

    elapsed: int | None = None
    if start_at and current >= start_at:
        upper = min(current, end_at) if end_at else current
        elapsed = int((upper - start_at).total_seconds())

    # ---- effective status -------------------------------------------------
    if row.status == CompetitionStatus.ENDED or end_at and current >= end_at:
        status = CompetitionStatus.ENDED
    elif row.status == CompetitionStatus.PAUSED:
        status = CompetitionStatus.PAUSED
    elif start_at and current < start_at or row.status == CompetitionStatus.UPCOMING and start_at is None:
        status = CompetitionStatus.UPCOMING
    else:
        status = CompetitionStatus.LIVE

    submissions_open = bool(
        status == CompetitionStatus.LIVE and row.submissions_enabled and not (end_at and current >= end_at)
    )

    teams_locked = bool(
        (row.team_lock_at and current >= _aware(row.team_lock_at))
        or status in (CompetitionStatus.LIVE, CompetitionStatus.PAUSED, CompetitionStatus.ENDED)
        or (start_at is not None and current >= start_at)
    )

    freeze_at = (
        end_at - timedelta(minutes=row.scoreboard_freeze_minutes)
        if end_at and row.scoreboard_freeze_minutes
        else None
    )
    scoreboard_frozen = bool(
        row.scoreboard_frozen
        or (freeze_at is not None and status == CompetitionStatus.LIVE and current >= freeze_at)
    )

    return CompetitionState(
        status=status,
        server_time=current,
        start_at=start_at,
        end_at=end_at,
        seconds_remaining=seconds_remaining,
        seconds_until_start=seconds_until_start,
        elapsed_seconds=elapsed,
        submissions_open=submissions_open,
        teams_locked=teams_locked,
        scoreboard_frozen=scoreboard_frozen,
        registration_open=bool(row.registration_open and status == CompetitionStatus.UPCOMING),
        results_published=bool(row.results_published or status == CompetitionStatus.ENDED),
    )


def to_public(row: CompetitionSettings, state: CompetitionState) -> CompetitionPublic:
    return CompetitionPublic(
        name=row.name,
        tagline=row.tagline,
        venue=row.venue,
        timezone=row.timezone,
        contact_email=row.contact_email,
        contact_phone=row.contact_phone,
        status=state.status,
        start_at=state.start_at,
        end_at=state.end_at,
        server_time=state.server_time,
        seconds_remaining=state.seconds_remaining,
        seconds_until_start=state.seconds_until_start,
        elapsed_seconds=state.elapsed_seconds,
        registration_open=state.registration_open,
        submissions_enabled=state.submissions_open,
        team_lock_at=_aware(row.team_lock_at),
        teams_locked=state.teams_locked,
        scoreboard_public=row.scoreboard_public,
        scoreboard_frozen=state.scoreboard_frozen,
        scoreboard_freeze_minutes=row.scoreboard_freeze_minutes,
        results_published=state.results_published,
        banner_message=row.banner_message,
        submission_rate_limit_per_minute=row.submission_rate_limit_per_minute,
        max_attempts_per_challenge=row.max_attempts_per_challenge,
        default_hint_penalty=row.default_hint_penalty,
        max_team_size=row.max_team_size,
        revision=row.revision,
    )


async def get_public_state(session: AsyncSession) -> CompetitionPublic:
    row = await get_settings_row(session)
    return to_public(row, compute_state(row))


# ------------------------------------------------------------ gate assertions
async def require_submissions_open(
    session: AsyncSession,
) -> tuple[CompetitionSettings, CompetitionState]:
    """Raise the right, user-friendly error when flags cannot be submitted."""
    row = await get_settings_row(session)
    state = compute_state(row)
    if state.status == CompetitionStatus.UPCOMING:
        raise CompetitionNotStarted(details={"start_at": _iso(state.start_at)})
    if state.status == CompetitionStatus.PAUSED:
        raise CompetitionPaused()
    if state.status == CompetitionStatus.ENDED:
        raise CompetitionEnded()
    if not row.submissions_enabled:
        raise CompetitionPaused("Submissions are currently disabled by the organisers.")
    return row, state


async def require_registration_open(session: AsyncSession) -> CompetitionSettings:
    row = await get_settings_row(session)
    state = compute_state(row)
    if not row.registration_open:
        raise BadRequest("Registration for WANO CTF is closed.", code="registration_closed", status_code=409)
    if state.status == CompetitionStatus.ENDED:
        raise CompetitionEnded("The competition has ended; registration is closed.")
    return row


async def require_team_changes_allowed(session: AsyncSession) -> CompetitionSettings:
    from app.errors import TeamLocked

    row = await get_settings_row(session)
    if compute_state(row).teams_locked:
        raise TeamLocked()
    return row


# ------------------------------------------------------------------ mutations
async def apply_update(
    session: AsyncSession, payload: CompetitionAdminUpdate, *, actor_id=None
) -> CompetitionSettings:
    row = await get_settings_row(session)
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        if field in {"start_at", "end_at", "team_lock_at"} and value is not None:
            value = _aware(value)
        setattr(row, field, value)

    if row.start_at and row.end_at and _aware(row.end_at) <= _aware(row.start_at):
        raise BadRequest("The end time must be after the start time.", code="invalid_window")
    if row.status == CompetitionStatus.LIVE and row.start_at is None:
        raise BadRequest("A start time is required before the competition goes live.", code="missing_start")

    # Recompute the status against the new window so an admin editing times
    # mid-event cannot leave the state machine inconsistent.
    state = compute_state(row)
    if row.status in (
        CompetitionStatus.UPCOMING,
        CompetitionStatus.LIVE,
        CompetitionStatus.ENDED,
    ):
        row.status = state.status
    row.updated_by = actor_id
    row.revision += 1
    await session.flush()
    return row


async def change_state(
    session: AsyncSession,
    action: str,
    *,
    reason: str | None = None,
    disable_submissions: bool = True,
    actor_id=None,
) -> CompetitionSettings:
    """START / PAUSE / RESUME / END / FREEZE / UNFREEZE / PUBLISH_RESULTS."""
    row = await get_settings_row(session)
    now = utcnow()

    if action == "start":
        if row.start_at is None:
            row.start_at = now
        if row.end_at is None:
            row.end_at = _aware(row.start_at) + timedelta(hours=8)
        elif _aware(row.end_at) <= now:
            raise BadRequest(
                "The configured end time is in the past. Update the schedule first.",
                code="invalid_window",
            )
        row.status = CompetitionStatus.LIVE
        row.submissions_enabled = True
        row.started_at = row.started_at or now
        row.paused_at = None
        if row.team_lock_at is None:
            row.team_lock_at = row.start_at

    elif action == "pause":
        if row.status != CompetitionStatus.LIVE:
            raise BadRequest("Only a live competition can be paused.", code="invalid_transition")
        row.status = CompetitionStatus.PAUSED
        row.paused_at = now

    elif action == "resume":
        if row.status != CompetitionStatus.PAUSED:
            raise BadRequest("The competition is not paused.", code="invalid_transition")
        if row.paused_at:
            paused_seconds = max(0, int((now - _aware(row.paused_at)).total_seconds()))
            row.total_paused_seconds += paused_seconds
            # Extend the window so participants are not robbed of solving time.
            if row.end_at:
                row.end_at = _aware(row.end_at) + timedelta(seconds=paused_seconds)
        row.paused_at = None
        row.status = CompetitionStatus.LIVE
        row.submissions_enabled = True

    elif action == "end":
        row.status = CompetitionStatus.ENDED
        row.ended_at = now
        row.paused_at = None
        if disable_submissions:
            row.submissions_enabled = False

    elif action == "freeze":
        row.scoreboard_frozen = True

    elif action == "unfreeze":
        row.scoreboard_frozen = False

    elif action == "publish_results":
        row.results_published = True

    else:  # pragma: no cover - guarded by the schema Literal
        raise BadRequest("Unknown competition action.", code="unknown_action")

    row.status_reason = reason
    row.updated_by = actor_id
    row.revision += 1
    await session.flush()
    return row


async def count_visible_teams(session: AsyncSession) -> int:
    from sqlalchemy import func

    from app.models.enums import TeamStatus
    from app.models.teams import Team

    stmt = select(func.count()).select_from(Team).where(Team.status != TeamStatus.DISQUALIFIED)
    return int((await session.execute(stmt)).scalar_one() or 0)


def _iso(value: datetime | None) -> str | None:
    aware = _aware(value)
    return aware.isoformat() if aware else None
