"""Flag submission, solve recording and score accounting.

Security invariants enforced here:

* The submitted flag is hashed (``submission_fingerprint``) and masked
  (``mask_flag``) before it reaches the database — plaintext is never persisted.
* Verification is a constant-time HMAC compare against the stored digest.
* A *failed* attempt is committed before the error is raised, otherwise the
  request-scoped session would roll the anti-abuse record back.
* ``team.score`` only ever changes through an awarded solve or an explicit,
  audited admin adjustment.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import AttemptsExhausted, BadRequest, IncorrectFlag
from app.models.challenges import Challenge
from app.models.submissions import ScoringEvent, Solve, Submission
from app.models.teams import Team
from app.schemas.challenge import FlagSubmitResponse
from app.security.flags import flag_matches, mask_flag, normalize_flag, submission_fingerprint
from app.security.rate_limit import enforce_persistent


def _now() -> datetime:
    return datetime.now(UTC)


async def attempts_used(session: AsyncSession, team_id: uuid.UUID, challenge_id: uuid.UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count())
                .select_from(Submission)
                .where(Submission.team_id == team_id, Submission.challenge_id == challenge_id)
            )
        ).scalar_one()
        or 0
    )


async def existing_solve(
    session: AsyncSession, team_id: uuid.UUID, challenge_id: uuid.UUID
) -> Solve | None:
    return (
        await session.execute(
            select(Solve).where(Solve.team_id == team_id, Solve.challenge_id == challenge_id)
        )
    ).scalar_one_or_none()


async def _challenge_already_solved(session: AsyncSession, challenge_id: uuid.UUID) -> bool:
    solve_id = await session.scalar(select(Solve.id).where(Solve.challenge_id == challenge_id).limit(1))
    return solve_id is not None


async def _rank(session: AsyncSession, team: Team) -> int | None:
    from app.services.teams import team_rank

    return await team_rank(session, team.id)


async def _record_submission(
    session: AsyncSession,
    *,
    team: Team,
    challenge: Challenge,
    user_id: uuid.UUID | None,
    submitted_flag: str,
    correct: bool,
    attempt_number: int,
    ip_address: str | None,
    user_agent: str | None,
) -> Submission:
    row = Submission(
        team_id=team.id,
        challenge_id=challenge.id,
        submitted_by=user_id,
        submitted_flag_masked=mask_flag(submitted_flag),
        submitted_flag_sha256=submission_fingerprint(submitted_flag),
        is_correct=correct,
        attempt_number=attempt_number,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(row)
    await session.flush()
    return row


async def submit_flag(
    session: AsyncSession,
    *,
    challenge: Challenge,
    team: Team,
    user_id: uuid.UUID | None,
    submitted_flag: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    max_attempts: int = 0,
    rate_limit_per_minute: int = 5,
    hint_cost: int = 0,
    started_at: datetime | None = None,
) -> FlagSubmitResponse:
    """Verify one flag attempt, record it, and award points when correct."""
    normalized = normalize_flag(submitted_flag)
    if not normalized:
        raise BadRequest("Please enter a flag before submitting.", code="empty_flag")

    # 1. Re-solves are idempotent: no double points, no error toast.
    solved = await existing_solve(session, team.id, challenge.id)
    if solved is not None:
        return FlagSubmitResponse(
            correct=True,
            already_solved=True,
            message="Your team has already solved this challenge.",
            points_awarded=0,
            challenge_slug=challenge.slug,
            team_score=team.score,
            team_rank=await _rank(session, team),
            solved_count=team.solved_count,
        )

    # 2. Throttle before any write so a scripted brute force is cheap to reject.
    if rate_limit_per_minute > 0:
        await enforce_persistent(
            session,
            f"submit:{team.id}:{challenge.id}",
            limit=rate_limit_per_minute,
            window_seconds=60,
            message="Slow down — too many submissions for this challenge.",
        )

    # 3. Total-attempt ceiling (0 = unlimited).
    used = await attempts_used(session, team.id, challenge.id)
    if max_attempts > 0 and used >= max_attempts:
        raise AttemptsExhausted(details={"attempts_used": used, "max_attempts": max_attempts})

    correct = flag_matches(normalized, challenge.flag_hash)
    submission = await _record_submission(
        session,
        team=team,
        challenge=challenge,
        user_id=user_id,
        submitted_flag=normalized,
        correct=correct,
        attempt_number=used + 1,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not correct:
        # Commit the attempt *before* raising, otherwise the request-scoped
        # session rollback would erase the anti-abuse trail.
        await session.commit()
        raise IncorrectFlag(
            details={
                "challenge_slug": challenge.slug,
                "attempts_used": used + 1,
                "attempts_remaining": (
                    None if max_attempts <= 0 else max(0, max_attempts - (used + 1))
                ),
            }
        )

    # 4. Award: points already spent on hints reduce the value of this solve.
    awarded = max(0, challenge.points - hint_cost)
    now = _now()
    solve = Solve(
        team_id=team.id,
        challenge_id=challenge.id,
        solved_by=user_id,
        points=awarded,
        hint_penalty=hint_cost,
        submission_id=submission.id,
        solved_at=now,
        elapsed_seconds=int((now - started_at).total_seconds()) if started_at else None,
        is_first_blood=not await _challenge_already_solved(session, challenge.id),
    )
    session.add(solve)
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - concurrent solve
        await session.rollback()
        raise IncorrectFlag("That challenge was just solved by your team.") from exc

    team.score += awarded
    team.solved_count += 1
    team.last_solve_at = now
    challenge.solved_count += 1
    submission.points_awarded = awarded
    await session.commit()

    return FlagSubmitResponse(
        correct=True,
        message="Flag accepted. Points added to your team.",
        points_awarded=awarded,
        challenge_slug=challenge.slug,
        team_score=team.score,
        team_rank=await _rank(session, team),
        solved_count=team.solved_count,
    )


async def apply_adjustment(
    session: AsyncSession, *, team: Team, delta: int, reason: str, admin_id: uuid.UUID | None
) -> Team:
    """Manual bonus/penalty, recorded in ``scoring_events`` for the audit trail."""
    if team.score + delta < 0:
        raise BadRequest(
            f"That penalty would take {team.name} below zero.", code="negative_score"
        )
    session.add(ScoringEvent(team_id=team.id, delta=delta, reason=reason, created_by=admin_id))
    team.score += delta
    await session.flush()
    return team
