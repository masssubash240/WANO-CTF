"""Public competition state (the countdown every client polls)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.competition import CompetitionPublic
from app.services.competition import get_public_state

router = APIRouter(prefix="/competition", tags=["competition"])


@router.get("", response_model=CompetitionPublic)
@router.get("/", response_model=CompetitionPublic, include_in_schema=False)
async def read_competition(session: SessionDep) -> CompetitionPublic:
    """Unauthenticated so the landing page can render before sign-in."""
    return await get_public_state(session)
