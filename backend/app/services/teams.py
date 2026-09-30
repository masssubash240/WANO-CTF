"""Team lifecycle: creation, invite-code joins and read projections.

``team_code`` is the only join secret. It is generated server-side, checked for
collisions, and never returned in public listings (see ``TeamPublic``).
"""

from __future__ import annotations

import re
import secrets
import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import BadRequest, Conflict, Forbidden, NotFound
from app.models.enums import TeamRole, TeamStatus
from app.models.teams import Team, TeamMember
from app.schemas.team import (
    TeamCreateRequest,
    TeamDetail,
    TeamMemberPublic,
    TeamMembershipSummary,
    TeamPublic,
)

_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I ambiguity
_CODE_LENGTH = 6
_CODE_ATTEMPTS = 12

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_team_name(name: str) -> str:
    """Case/punctuation-insensitive form backing the uniqueness constraint."""
    return _NON_ALNUM.sub("", name.strip().lower())


async def _generate_team_code(session: AsyncSession) -> str:
    for _ in range(_CODE_ATTEMPTS):
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        exists = await session.scalar(select(Team.id).where(Team.team_code == code).limit(1))
        if exists is None:
            return code
    raise Conflict("Could not allocate a unique team code. Please try again.")


async def _existing_team(session: AsyncSession, user_id: uuid.UUID) -> Team | None:
    stmt = select(Team).join(TeamMember, TeamMember.team_id == Team.id).where(TeamMember.user_id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def member_count(session: AsyncSession, team_id: uuid.UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)
            )
        ).scalar_one()
        or 0
    )


async def get_team_or_404(session: AsyncSession, team_id: uuid.UUID) -> Team:
    team = await session.get(Team, team_id)
    if team is None:
        raise NotFound("That team could not be found.")
    return team


async def create_team(session: AsyncSession, *, user: uuid.UUID, payload: TeamCreateRequest) -> Team:
    """Create a team and enrol the caller as captain."""
    if await _existing_team(session, user) is not None:
        raise Conflict("You already belong to a team. Leave it before creating a new one.")

    normalized = normalize_team_name(payload.name)
    if not normalized:
        raise BadRequest("Please choose a team name with letters or numbers.")

    clash = await session.scalar(select(Team.id).where(Team.name_normalized == normalized).limit(1))
    if clash is not None:
        raise Conflict("That team name is already taken.", code="team_name_taken")

    team = Team(
        name=payload.name,
        name_normalized=normalized,
        team_code=await _generate_team_code(session),
        description=payload.description,
        college=payload.college,
        captain_id=user,
        status=TeamStatus.ACTIVE,
    )
    session.add(team)
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - concurrent create
        await session.rollback()
        raise Conflict("That team name is already taken.", code="team_name_taken") from exc

    session.add(TeamMember(team_id=team.id, user_id=user, role=TeamRole.CAPTAIN))
    await session.flush()
    return team


async def join_team(session: AsyncSession, *, user: uuid.UUID, code: str, max_team_size: int = 4) -> Team:
    """Join an existing team using its invite code."""
    if await _existing_team(session, user) is not None:
        raise Conflict("You already belong to a team. Leave it before joining another.")

    team = (
        await session.execute(select(Team).where(Team.team_code == code.strip().upper()).limit(1))
    ).scalar_one_or_none()
    if team is None:
        raise NotFound("No team matches that invite code.", code="invalid_team_code")
    if team.status == TeamStatus.DISQUALIFIED:
        raise Forbidden("That team has been disqualified by the organisers.", code="team_disqualified")

    if max_team_size > 0 and await member_count(session, team.id) >= max_team_size:
        raise BadRequest("That team is already full.", code="team_full")

    session.add(TeamMember(team_id=team.id, user_id=user, role=TeamRole.MEMBER))
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - concurrent join
        await session.rollback()
        raise Conflict("You already belong to a team.") from exc
    return team


async def leave_team(session: AsyncSession, *, user: uuid.UUID) -> None:
    """Remove the caller from their team, promoting a successor if they are captain."""
    membership = (
        await session.execute(select(TeamMember).where(TeamMember.user_id == user).limit(1))
    ).scalar_one_or_none()
    if membership is None:
        raise NotFound("You are not part of a team.")

    if membership.role == TeamRole.CAPTAIN:
        successor = (
            await session.execute(
                select(TeamMember)
                .where(TeamMember.team_id == membership.team_id, TeamMember.id != membership.id)
                .order_by(TeamMember.joined_at)
                .limit(1)
            )
        ).scalar_one_or_none()
        if successor is None:
            raise BadRequest(
                "A team captain cannot leave while the team has no other members.",
                code="captain_cannot_leave",
            )
        successor.role = TeamRole.CAPTAIN
        team = await session.get(Team, membership.team_id)
        if team is not None:
            team.captain_id = successor.user_id
        await session.flush()

    await session.delete(membership)
    await session.flush()


async def team_rank(session: AsyncSession, team_id: uuid.UUID) -> int | None:
    """1-based leaderboard position (score desc, earliest last solve breaks ties).

    Delegates to the scoreboard's own ordering so the rank shown on a team's
    dashboard can never disagree with the public leaderboard (both backends,
    SQLite and PostgreSQL). ``None`` means the team does not exist or is
    disqualified and therefore excluded from the leaderboard.
    """
    from app.services.scoreboard import leaderboard_rows

    for ranked_team, rank in await leaderboard_rows(session):
        if ranked_team.id == team_id:
            return rank
    return None


# ------------------------------------------------------------------ projections
def to_member_public(membership: TeamMember) -> TeamMemberPublic:
    profile = membership.user
    return TeamMemberPublic(
        id=membership.id,
        user_id=membership.user_id,
        role=membership.role,
        joined_at=membership.joined_at,
        display_name=profile.display_name if profile else "",
        college=profile.college if profile else None,
    )


async def to_public(session: AsyncSession, team: Team) -> TeamPublic:
    return TeamPublic(
        id=team.id,
        name=team.name,
        college=team.college,
        status=team.status,
        score=team.score,
        solved_count=team.solved_count,
        member_count=await member_count(session, team.id),
        last_solve_at=team.last_solve_at,
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


async def to_detail(session: AsyncSession, team: Team, *, viewer_id: uuid.UUID | None = None) -> TeamDetail:
    """``team_code`` is only ever revealed to an actual member of the team."""
    members = sorted(team.members, key=lambda m: (m.role != TeamRole.CAPTAIN, m.joined_at))
    is_member = any(m.user_id == viewer_id for m in members)
    return TeamDetail(
        id=team.id,
        name=team.name,
        college=team.college,
        status=team.status,
        score=team.score,
        solved_count=team.solved_count,
        member_count=len(members),
        last_solve_at=team.last_solve_at,
        created_at=team.created_at,
        updated_at=team.updated_at,
        team_code=team.team_code if is_member else None,
        captain_id=team.captain_id,
        captain_name=team.captain.display_name if team.captain else None,
        members=[to_member_public(m) for m in members],
        is_captain=is_member and team.captain_id == viewer_id,
        members_locked=team.status != TeamStatus.ACTIVE,
    )


async def to_membership_summary(
    session: AsyncSession,
    team: Team,
    membership: TeamMember,
    *,
    max_team_size: int = 4,
    with_rank: bool = True,
) -> TeamMembershipSummary:
    return TeamMembershipSummary(
        id=team.id,
        name=team.name,
        team_code=team.team_code,
        status=team.status,
        score=team.score,
        solved_count=team.solved_count,
        hint_penalty=team.hint_penalty,
        member_count=len(team.members),
        max_team_size=max_team_size,
        role=membership.role,
        is_captain=membership.role == TeamRole.CAPTAIN,
        members_locked=team.status != TeamStatus.ACTIVE,
        members=[to_member_public(m) for m in team.members],
        rank=await team_rank(session, team.id) if with_rank else None,
    )
