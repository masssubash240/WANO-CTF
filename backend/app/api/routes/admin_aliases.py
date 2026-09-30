"""Spec-compatibility endpoints for Admin operations:
- GET /api/admin/export/csv
- POST /api/admin/round/start
- POST /api/admin/round/stop
- POST /api/admin/reset-scores
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import delete, select, update

from app.api.deps import SessionDep
from app.models.competition import CompetitionSettings, CompetitionStatus
from app.models.submissions import ScoringEvent, Solve, Submission
from app.models.teams import Team
from app.security.deps import AdminPrincipal, get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])
AdminDep = Annotated[AdminPrincipal, Depends(get_current_admin)]


class ActionStatusResponse(BaseModel):
    status: str
    message: str


@router.get("/export/csv")
async def export_scoreboard_csv(
    _admin: AdminDep,
    session: SessionDep,
) -> Response:
    """Export current leaderboard standings to CSV."""
    stmt = (
        select(Team)
        .order_by(Team.score.desc(), Team.last_solve_at.asc().nulls_last())
    )
    teams = list((await session.execute(stmt)).scalars())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Team Name", "College", "Points", "Solve Count", "Last Solve Time"])

    for rank, t in enumerate(teams, start=1):
        writer.writerow([
            rank,
            t.name,
            t.college or "",
            t.score,
            t.solved_count,
            t.last_solve_at.isoformat() if t.last_solve_at else "",
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wano_ctf_round1_standings.csv"},
    )


@router.post("/round/start", response_model=ActionStatusResponse)
async def start_round(
    _admin: AdminDep,
    session: SessionDep,
) -> ActionStatusResponse:
    """Start or resume Round 1 competition."""
    stmt = select(CompetitionSettings).limit(1)
    row = (await session.execute(stmt)).scalar_one_or_none()
    now = datetime.now(UTC)

    if row is None:
        row = CompetitionSettings(
            name="WANO CTF — Round 1",
            status=CompetitionStatus.LIVE,
            start_at=now,
            submissions_enabled=True,
        )
        session.add(row)
    else:
        row.status = CompetitionStatus.LIVE
        if not row.start_at:
            row.start_at = now
        row.submissions_enabled = True

    await session.commit()
    return ActionStatusResponse(status="success", message="Round 1 started successfully.")


@router.post("/round/stop", response_model=ActionStatusResponse)
async def stop_round(
    _admin: AdminDep,
    session: SessionDep,
) -> ActionStatusResponse:
    """Stop or pause Round 1 competition."""
    stmt = select(CompetitionSettings).limit(1)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is not None:
        row.status = CompetitionStatus.PAUSED
        row.submissions_enabled = False
        await session.commit()

    return ActionStatusResponse(status="success", message="Round 1 stopped/paused.")


@router.post("/reset-scores", response_model=ActionStatusResponse)
async def reset_scores(
    _admin: AdminDep,
    session: SessionDep,
) -> ActionStatusResponse:
    """Reset all team scores, solves, and submissions."""
    await session.execute(delete(Submission))
    await session.execute(delete(Solve))
    await session.execute(delete(ScoringEvent))
    await session.execute(
        update(Team).values(
            score=0,
            hint_penalty=0,
            solved_count=0,
            last_solve_at=None,
        )
    )
    await session.commit()
    return ActionStatusResponse(status="success", message="All team scores and submissions reset.")
