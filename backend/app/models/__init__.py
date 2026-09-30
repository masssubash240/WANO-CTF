"""SQLAlchemy model registry.

Importing this package registers every mapper, which is required before
``Base.metadata.create_all`` or any relationship string resolution runs.
"""

from app.models.accounts import (
    ActivityEvent,
    AdminSession,
    AdminUser,
    AnnouncementRead,
    AuditLog,
    LoginEvent,
    Profile,
    RateLimitCounter,
)
from app.models.announcements import Announcement
from app.models.base import Base, JSONType, TimestampMixin, uuid_pk
from app.models.challenges import Category, Challenge, ChallengeHint, HintUnlock
from app.models.competition import CompetitionSettings
from app.models.enums import (
    CATEGORY_SEED,
    ActorType,
    AdminRole,
    AnnouncementPriority,
    CompetitionStatus,
    Difficulty,
    TeamRole,
    TeamStatus,
    UserRole,
)
from app.models.files import ChallengeFile, ChallengeFileToken
from app.models.submissions import ScoringEvent, Solve, Submission
from app.models.teams import Team, TeamMember

__all__ = [
    # base
    "Base",
    "JSONType",
    "TimestampMixin",
    "uuid_pk",
    # enums
    "ActorType",
    "AdminRole",
    "AnnouncementPriority",
    "CATEGORY_SEED",
    "CompetitionStatus",
    "Difficulty",
    "TeamRole",
    "TeamStatus",
    "UserRole",
    # accounts / security
    "ActivityEvent",
    "AdminSession",
    "AdminUser",
    "AnnouncementRead",
    "AuditLog",
    "LoginEvent",
    "Profile",
    "RateLimitCounter",
    # announcements
    "Announcement",
    # challenges
    "Category",
    "Challenge",
    "ChallengeHint",
    "HintUnlock",
    # competition
    "CompetitionSettings",
    # files
    "ChallengeFile",
    "ChallengeFileToken",
    # submissions / scoring
    "ScoringEvent",
    "Solve",
    "Submission",
    # teams
    "Team",
    "TeamMember",
]
