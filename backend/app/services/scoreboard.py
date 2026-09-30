"""Public scoreboard, freeze semantics and the post-event results breakdown."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import Forbidden, NotFound
from app.models.enums import TeamStatus
from app.models.submissions import Solve
from app.models.teams import Team, TeamMember
from app.schemas.challenge import SolveRecord
from app.services.competition import CompetitionState
from app.schemas.scoreboard import (
    ResultsResponse,
    ScoreboardEntry,
    ScoreboardMeta,
    ScoreboardResponse,
    TeamSolveDetail,
)

#: score DESC, then earliest last_solve_at, then name — standard CTF tiebreak.
_LEADERBOARD_ORDER = (
    Team.score.desc(),
    Team.last_solve_at.asc(),
    Team.name.asc(),
)


def _now() -> datetime:
    return datetime.now(UTC)


async def _member_counts(session: AsyncSession) -> dict[uuid.UUID, int]:
    rows = await session.execute(
        select(TeamMember.team_id, func.count()).group_by(TeamMember.team_id)
    )
    return {team_id: int(count) for team_id, count in rows.all()}


async def leaderboard_rows(
    session: AsyncSession, *, limit: int | None = None
) -> list[tuple[Team, int]]:
    """All non-disqualified teams in leaderboard order, paired with their rank.

    Ranking is computed in Python after ordering so ranks stay gapless and
    deterministic across SQLite (dev) and PostgreSQL (prod).
    """
    stmt = select(Team).where(Team.status != TeamStatus.DISQUALIFIED).order_by(*_LEADERBOARD_ORDER)
    if limit:
        stmt = stmt.limit(limit)
    teams = list((await session.execute(stmt)).scalars())
    return [(team, index) for index, team in enumerate(teams, start=1)]


def _to_solve_record(solve: Solve) -> SolveRecord:
    challenge = solve.challenge
    category = challenge.category if challenge else None
    return SolveRecord(
        challenge_id=solve.challenge_id,
        challenge_title=challenge.title if challenge else "Unknown",
        challenge_slug=challenge.slug if challenge else "",
        category_slug=category.slug if category else "",
        category_name=category.name if category else "Uncategorised",
        points=solve.points,
        hint_penalty=solve.hint_penalty,
        solved_at=solve.solved_at,
        first_blood=solve.is_first_blood,
    )


async def _solves_for(session: AsyncSession, team_id: uuid.UUID) -> list[Solve]:
    return list(
        (
            await session.execute(
                select(Solve).where(Solve.team_id == team_id).order_by(Solve.solved_at.asc())
            )
        ).scalars()
    )


def _to_detail(team: Team, rank: int, solves: list[Solve]) -> TeamSolveDetail:
    return TeamSolveDetail(
        rank=rank,
        team_id=team.id,
        team_name=team.name,
        college=team.college,
        score=team.score,
        solved_count=team.solved_count,
        hint_penalty=team.hint_penalty,
        last_solve_at=team.last_solve_at,
        first_bloods=sum(1 for s in solves if s.is_first_blood),
        solves=[_to_solve_record(s) for s in solves],
    )


async def build_scoreboard(
    session: AsyncSession,
    state: CompetitionState,
    *,
    settings_row,
    viewer_team_id: uuid.UUID | None = None,
    is_admin: bool = False,
) -> ScoreboardResponse:
    """Assemble the scoreboard, honouring ``scoreboard_public`` and the freeze.

    While frozen, scores are zeroed for everyone (including the caller's own
    team) so nobody can infer the final standings before the event ends.
    """
    if not settings_row.scoreboard_public and not is_admin:
        raise Forbidden(
            "The scoreboard is currently hidden by the organisers.", code="scoreboard_hidden"
        )

    frozen = state.scoreboard_frozen
    members = await _member_counts(session)
    entries: list[ScoreboardEntry] = []
    my_entry: ScoreboardEntry | None = None

    for team, rank in await leaderboard_rows(session):
        entry = ScoreboardEntry(
            rank=rank,
            team_id=team.id,
            team_name=team.name,
            college=team.college,
            score=0 if frozen else team.score,
            solved_count=0 if frozen else team.solved_count,
            last_solve_at=None if frozen else team.last_solve_at,
            member_count=members.get(team.id, 0),
            is_own_team=viewer_team_id is not None and team.id == viewer_team_id,
        )
        entries.append(entry)
        if entry.is_own_team:
            my_entry = entry

    return ScoreboardResponse(
        entries=entries,
        total_teams=len(entries),
        frozen=frozen,
        frozen_since=settings_row.end_at if frozen else None,
        public=settings_row.scoreboard_public,
        generated_at=_now(),
        meta=ScoreboardMeta(
            status=state.status,
            start_at=state.start_at,
            end_at=state.end_at,
            server_time=state.server_time,
            seconds_remaining=state.seconds_remaining,
        ),
        my_team=my_entry,
    )


async def build_results(
    session: AsyncSession,
    state: CompetitionState,
    *,
    settings_row,
    is_admin: bool = False,
) -> ResultsResponse:
    """Full post-event breakdown for every team, gated on ``results_published``."""
    if not (settings_row.results_published or is_admin):
        raise Forbidden("Results have not been published yet.", code="results_not_published")

    details: list[TeamSolveDetail] = []
    for team, rank in await leaderboard_rows(session):
        details.append(_to_detail(team, rank, await _solves_for(session, team.id)))

    return ResultsResponse(
        published=bool(settings_row.results_published),
        status=state.status,
        generated_at=_now(),
        entries=details,
    )


async def team_results(
    session: AsyncSession,
    *,
    team_id: uuid.UUID,
    state: CompetitionState,
    settings_row,
    is_admin: bool = False,
) -> ResultsResponse:
    """Results page for a single team."""
    team = await session.get(Team, team_id)
    if team is None:
        raise NotFound("That team could not be found.")
    if not (settings_row.results_published or is_admin):
        raise Forbidden("Results have not been published yet.", code="results_not_published")

    ranks = {t.id: r for t, r in await leaderboard_rows(session)}
    solves = await _solves_for(session, team.id)
    return ResultsResponse(
        published=bool(settings_row.results_published),
        status=state.status,
        generated_at=_now(),
        entries=[_to_detail(team, ranks.get(team.id, 0), solves)],
    )
