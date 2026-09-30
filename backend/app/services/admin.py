"""Organiser-facing queries: dashboard statistics and paginated listings.

Every function here is read-only; mutations live in the admin routers so that
authorisation and audit logging stay in one place. Flag plaintext never leaves
this layer — challenges are projected through ``has_flag: bool`` only.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts import Profile
from app.models.challenges import Challenge
from app.models.enums import CompetitionStatus, TeamStatus
from app.models.submissions import Solve, Submission
from app.models.teams import Team, TeamMember
from app.schemas.admin import (
    AdminLeaderboardRow,
    AdminStats,
    AdminTeamRow,
    AdminUserRow,
)
from app.schemas.common import Page

ACTIVE_WINDOW = timedelta(minutes=15)
SOLVE_WINDOW = timedelta(hours=1)


def _now() -> datetime:
    return datetime.now(UTC)


def _cut(**kwargs) -> datetime:
    return _now() - timedelta(**kwargs)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def _count(session: AsyncSession, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one() or 0)


async def build_stats(session: AsyncSession, *, status: CompetitionStatus) -> AdminStats:
    """Dashboard counters. One round trip per metric, all index-backed."""
    now = _now()
    total_participants = await _count(
        session, select(func.count()).select_from(Profile).where(Profile.role != "admin")
    )
    total_teams = await _count(
        session,
        select(func.count())
        .select_from(Team)
        .where(Team.status != TeamStatus.DISQUALIFIED),
    )
    total_challenges = await _count(session, select(func.count()).select_from(Challenge))
    published_challenges = await _count(
        session, select(func.count()).select_from(Challenge).where(Challenge.visible.is_(True))
    )
    total_submissions = await _count(session, select(func.count()).select_from(Submission))
    correct_submissions = await _count(
        session, select(func.count()).select_from(Submission).where(Submission.is_correct.is_(True))
    )

    active_users_15m = await _count(
        session,
        select(func.count(func.distinct(Submission.submitted_by))).where(
            Submission.submitted_at >= now - ACTIVE_WINDOW
        ),
    )
    active_teams_15m = await _count(
        session,
        select(func.count(func.distinct(Submission.team_id))).where(
            Submission.submitted_at >= now - ACTIVE_WINDOW
        ),
    )
    solves_last_hour = await _count(
        session, select(func.count()).select_from(Solve).where(Solve.solved_at >= now - SOLVE_WINDOW)
    )
    teams_with_solves = await _count(
        session,
        select(func.count(func.distinct(Solve.team_id))).where(Solve.solved_at >= now - SOLVE_WINDOW),
    )

    # Mean time-to-solve over recorded solves, as whole seconds.
    avg_seconds = (
        await session.execute(select(func.avg(Solve.elapsed_seconds)).where(Solve.elapsed_seconds.isnot(None)))
    ).scalar_one()

    return AdminStats(
        total_participants=total_participants,
        total_teams=total_teams,
        total_challenges=total_challenges,
        published_challenges=published_challenges,
        total_submissions=total_submissions,
        correct_submissions=correct_submissions,
        incorrect_submissions=total_submissions - correct_submissions,
        active_users_15m=active_users_15m,
        active_teams_15m=active_teams_15m,
        solves_last_hour=solves_last_hour,
        teams_with_solves=teams_with_solves,
        average_solve_seconds=int(avg_seconds) if avg_seconds is not None else None,
        server_time=now,
    )


async def leaderboard(session: AsyncSession, *, limit: int = 25) -> list[AdminLeaderboardRow]:
    """Organiser leaderboard — always unfrozen, disqualifications excluded."""
    rows = await session.execute(
        select(Team)
        .where(Team.status != TeamStatus.DISQUALIFIED)
        .order_by(Team.score.desc(), Team.last_solve_at.asc().nulls_last(), Team.name.asc())
        .limit(limit)
    )
    return [
        AdminLeaderboardRow(
            rank=index,
            team_name=team.name,
            score=team.score,
            solved_count=team.solved_count,
            last_solve_at=_aware(team.last_solve_at),
        )
        for index, team in enumerate(rows.scalars(), start=1)
    ]


# ------------------------------------------------------------------------ users
def _to_user_row(profile: Profile, team: Team | None) -> AdminUserRow:
    return AdminUserRow(
        id=profile.id,
        email=profile.email,
        full_name=profile.display_name,
        college=profile.college,
        department=profile.department,
        year=profile.year,
        phone=profile.phone,
        role=profile.role,
        is_active=profile.is_active,
        is_banned=profile.is_banned,
        ban_reason=profile.ban_reason,
        email_verified=profile.email_verified,
        last_login_at=_aware(profile.last_login_at),
        last_login_ip=profile.last_login_ip,
        team_id=team.id if team else None,
        team_name=team.name if team else None,
        created_at=_aware(profile.created_at),
        updated_at=_aware(profile.updated_at),
    )


async def list_users(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    role: str | None = None,
) -> Page[AdminUserRow]:
    """Participants with their team attached, paginated and searchable."""
    filters = []
    if search:
        needle = f"%{search.strip().lower()}%"
        filters.append(
            or_(func.lower(Profile.display_name).like(needle), func.lower(Profile.email).like(needle))
        )
    if role:
        filters.append(Profile.role == role)

    count_stmt = select(func.count()).select_from(Profile).where(*filters)
    total = await _count(session, count_stmt)

    rows = await session.execute(
        select(Profile, Team)
        .outerjoin(TeamMember, TeamMember.user_id == Profile.id)
        .outerjoin(Team, Team.id == TeamMember.team_id)
        .where(*filters)
        .order_by(Profile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page[AdminUserRow](
        items=[_to_user_row(profile, team) for profile, team in rows.all()],
        total=total,
        page=page,
        page_size=page_size,
    )


# ------------------------------------------------------------------------ teams
def _to_team_row(team: Team, member_count: int, captain_email: str | None) -> AdminTeamRow:
    return AdminTeamRow(
        id=team.id,
        name=team.name,
        team_code=team.team_code,
        status=team.status,
        status_reason=team.status_reason,
        score=team.score,
        solved_count=team.solved_count,
        hint_penalty=team.hint_penalty,
        member_count=member_count,
        captain_id=team.captain_id,
        captain_email=captain_email,
        college=team.college,
        last_solve_at=_aware(team.last_solve_at),
        created_at=_aware(team.created_at),
        updated_at=_aware(team.updated_at),
    )


async def _team_captain_emails(session: AsyncSession, team_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not team_ids:
        return {}
    rows = await session.execute(
        select(Team.id, Profile.email)
        .join(Profile, Profile.id == Team.captain_id)
        .where(Team.id.in_(team_ids))
    )
    return {team_id: email for team_id, email in rows.all()}


async def list_teams(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    status: TeamStatus | None = None,
) -> Page[AdminTeamRow]:
    filters = []
    if search:
        needle = f"%{search.strip().lower()}%"
        filters.append(
            or_(func.lower(Team.name).like(needle), func.lower(Team.team_code).like(needle))
        )
    if status:
        filters.append(Team.status == status)

    total = await _count(session, select(func.count()).select_from(Team).where(*filters))

    rows = await session.execute(
        select(Team, func.count(TeamMember.id))
        .outerjoin(TeamMember, TeamMember.team_id == Team.id)
        .where(*filters)
        .group_by(Team.id)
        .order_by(Team.score.desc(), Team.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    loaded = rows.all()
    captains = await _team_captain_emails(session, [team.id for team, _ in loaded])
    return Page[AdminTeamRow](
        items=[
            _to_team_row(team, int(count or 0), captains.get(team.id))
            for team, count in loaded
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
