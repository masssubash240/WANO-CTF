"""Challenge read projections and the hint-unlock economy.

Hints belong to the *team*, not the individual, and their cost is attached to
the eventual ``Solve`` so the awarded points already reflect what was spent.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import BadRequest, Forbidden, NotFound
from app.models.challenges import Challenge, ChallengeHint, HintUnlock
from app.models.enums import TeamStatus
from app.models.submissions import Solve, Submission
from app.schemas.challenge import (
    ChallengeDetail,
    ChallengeFilePublic,
    ChallengeHintPublic,
    ChallengeSummary,
    HintUnlockResponse,
)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def get_visible_challenge_or_404(session: AsyncSession, slug: str) -> Challenge:
    challenge = (
        await session.execute(select(Challenge).where(Challenge.slug == slug).limit(1))
    ).scalar_one_or_none()
    if challenge is None or not challenge.visible:
        raise NotFound("That challenge is not available.")
    return challenge


@dataclass(slots=True)
class TeamProgress:
    """Everything needed to personalise challenges for one team."""

    team_id: uuid.UUID | None = None
    solves: dict[uuid.UUID, Solve] = field(default_factory=dict)
    attempts: dict[uuid.UUID, int] = field(default_factory=dict)
    unlocked_hints: dict[uuid.UUID, set[uuid.UUID]] = field(default_factory=dict)
    hint_cost: dict[uuid.UUID, int] = field(default_factory=dict)

    def is_solved(self, challenge_id: uuid.UUID) -> bool:
        return challenge_id in self.solves

    def attempts_used(self, challenge_id: uuid.UUID) -> int:
        return self.attempts.get(challenge_id, 0)

    def cost_for(self, challenge_id: uuid.UUID) -> int:
        return self.hint_cost.get(challenge_id, 0)


async def load_team_progress(session: AsyncSession, team_id: uuid.UUID | None) -> TeamProgress:
    """Batch a team's solves, attempt counts and hint unlocks in three queries."""
    progress = TeamProgress(team_id=team_id)
    if team_id is None:
        return progress

    for solve in (await session.execute(select(Solve).where(Solve.team_id == team_id))).scalars():
        progress.solves[solve.challenge_id] = solve

    rows = await session.execute(
        select(Submission.challenge_id, func.count())
        .where(Submission.team_id == team_id)
        .group_by(Submission.challenge_id)
    )
    progress.attempts = {challenge_id: int(count) for challenge_id, count in rows.all()}

    for unlock in (await session.execute(select(HintUnlock).where(HintUnlock.team_id == team_id))).scalars():
        progress.unlocked_hints.setdefault(unlock.challenge_id, set()).add(unlock.hint_id)
        progress.hint_cost[unlock.challenge_id] = (
            progress.hint_cost.get(unlock.challenge_id, 0) + unlock.cost_paid
        )
    return progress


# ------------------------------------------------------------------ projections
def to_summary(challenge: Challenge, progress: TeamProgress) -> ChallengeSummary:
    category = challenge.category
    return ChallengeSummary(
        id=challenge.id,
        title=challenge.title,
        slug=challenge.slug,
        category_slug=category.slug if category else "",
        category_name=category.name if category else "Uncategorised",
        category_icon=category.icon if category else "Puzzle",
        difficulty=challenge.difficulty,
        points=challenge.points,
        solved_count=challenge.solved_count,
        is_solved=progress.is_solved(challenge.id),
        hint_count=sum(1 for h in challenge.hints if h.is_visible),
        file_count=len(challenge.files),
        author=challenge.author,
    )


def _to_file(challenge_slug: str, file) -> ChallengeFilePublic:
    return ChallengeFilePublic(
        id=file.id,
        filename=file.filename,
        label=file.label,
        size_bytes=file.size_bytes,
        mime_type=file.mime_type,
        sha256=file.sha256,
        download_url=f"{settings.api_prefix}/challenges/{challenge_slug}/files/{file.id}/download",
    )


def _to_hint(hint: ChallengeHint, progress: TeamProgress, challenge_id: uuid.UUID) -> ChallengeHintPublic:
    """An un-unlocked hint exposes only its cost â€” never its text."""
    unlocked = hint.id in progress.unlocked_hints.get(challenge_id, set())
    return ChallengeHintPublic(
        id=hint.id,
        display_order=hint.display_order,
        cost=hint.cost,
        is_unlocked=unlocked,
        text=hint.text if unlocked else None,
    )


def to_detail(
    challenge: Challenge,
    progress: TeamProgress,
    *,
    max_attempts: int = 0,
) -> ChallengeDetail:
    solve = progress.solves.get(challenge.id)
    used = progress.attempts_used(challenge.id)
    remaining = None if max_attempts <= 0 else max(0, max_attempts - used)
    summary = to_summary(challenge, progress)

    return ChallengeDetail(
        **summary.model_dump(),
        description=challenge.description,
        connection_info=challenge.connection_info,
        flag_format_hint=challenge.flag_format_hint,
        hints=[_to_hint(h, progress, challenge.id) for h in challenge.hints if h.is_visible],
        files=[_to_file(challenge.slug, f) for f in challenge.files],
        attempts_used=used,
        max_attempts=max_attempts or None,
        attempts_remaining=remaining,
        solved_at=_aware(solve.solved_at) if solve else None,
        points_awarded=solve.points if solve else None,
        first_blood=bool(solve and solve.is_first_blood),
    )


async def unlock_hint(
    session: AsyncSession,
    *,
    challenge: Challenge,
    hint_id: uuid.UUID,
    team: Team,
    user_id: uuid.UUID,
) -> HintUnlockResponse:
    """Spend team points to release one hint. Idempotent per (hint, team)."""
    if team.status != TeamStatus.ACTIVE:
        raise Forbidden("Your team can no longer unlock hints.", code="team_inactive")

    hint = next((h for h in challenge.hints if h.id == hint_id), None)
    if hint is None or not hint.is_visible:
        raise NotFound("That hint is not available.")

    existing = (
        await session.execute(
            select(HintUnlock).where(
                HintUnlock.hint_id == hint_id, HintUnlock.team_id == team.id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return HintUnlockResponse(
            hint_id=hint.id,
            text=hint.text,
            cost_paid=0,
            team_score=team.score,
            total_hint_penalty=team.hint_penalty,
        )

    if team.score < hint.cost:
        raise BadRequest(
            "Your team does not have enough points for that hint.", code="insufficient_points"
        )

    session.add(
        HintUnlock(
            hint_id=hint.id,
            challenge_id=challenge.id,
            team_id=team.id,
            user_id=user_id,
            cost_paid=hint.cost,
        )
    )
    # Hints are tracked separately from `team.score`, which stays equal to the
    # sum of awarded solve points (see scoring.submit_flag).
    team.hint_penalty += hint.cost
    await session.flush()

    return HintUnlockResponse(
        hint_id=hint.id,
        text=hint.text,
        cost_paid=hint.cost,
        team_score=team.score,
        total_hint_penalty=team.hint_penalty,
    )
