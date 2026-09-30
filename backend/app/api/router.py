"""Aggregated API router.

Participant routes are mounted first; the admin panel lives under a separate
``/admin`` prefix and is guarded by its own organiser identity (see
``app.security.deps.get_current_admin``) so a participant token can never reach
it.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    admin_aliases,
    announcements,
    auth,
    auth_aliases,
    challenges,
    challenges_aliases,
    competition,
    files,
    leaderboard_aliases,
    scoreboard,
    submissions,
    teams,
    users,
    users_aliases,
)
from app.api.routes.admin import router as admin_router
from app.config import settings

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(auth.router)
api_router.include_router(auth_aliases.router)
api_router.include_router(competition.router)
api_router.include_router(users.router)
api_router.include_router(users_aliases.router)
api_router.include_router(teams.router)
api_router.include_router(challenges.router)
api_router.include_router(challenges_aliases.router)
api_router.include_router(submissions.router)
api_router.include_router(scoreboard.router)
api_router.include_router(leaderboard_aliases.router)
api_router.include_router(announcements.router)
api_router.include_router(files.router)
api_router.include_router(admin_aliases.router)

api_router.include_router(admin_router)

__all__ = ["api_router"]

