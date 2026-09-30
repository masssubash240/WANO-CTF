"""Domain enums shared by models, schemas and services."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.value


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class TeamStatus(StrEnum):
    ACTIVE = "active"
    LOCKED = "locked"
    DISQUALIFIED = "disqualified"


class TeamRole(StrEnum):
    CAPTAIN = "captain"
    MEMBER = "member"


class CompetitionStatus(StrEnum):
    UPCOMING = "upcoming"
    LIVE = "live"
    PAUSED = "paused"
    ENDED = "ended"


class AnnouncementPriority(StrEnum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"


class UserRole(StrEnum):
    PARTICIPANT = "participant"
    ADMIN = "admin"


class AdminRole(StrEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"


class ActorType(StrEnum):
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


#: Display order + labels used by the public landing page and challenge filters.
CATEGORY_SEED: list[dict[str, str]] = [
    {
        "slug": "web",
        "name": "Web Security",
        "icon": "Globe",
        "description": "Break into web applications: injection, auth flaws, SSRF and more.",
    },
    {
        "slug": "crypto",
        "name": "Cryptography",
        "icon": "KeyRound",
        "description": "Classical ciphers, weak key exchange, broken implementations.",
    },
    {
        "slug": "forensics",
        "name": "Digital Forensics",
        "icon": "Search",
        "description": "Disk images, memory dumps, file carving and metadata analysis.",
    },
    {
        "slug": "osint",
        "name": "OSINT",
        "icon": "Radar",
        "description": "Open-source intelligence: trace digital footprints across the web.",
    },
    {
        "slug": "linux",
        "name": "Linux",
        "icon": "Terminal",
        "description": "Privilege escalation, restricted shells, permissions and services.",
    },
    {
        "slug": "reverse",
        "name": "Reverse Engineering",
        "icon": "Binary",
        "description": "Disassemble binaries, defeat obfuscation, recover hidden logic.",
    },
    {
        "slug": "networking",
        "name": "Networking",
        "icon": "Network",
        "description": "Packet captures, protocol abuse, tunnelling and traffic analysis.",
    },
    {
        "slug": "misc",
        "name": "Miscellaneous",
        "icon": "Puzzle",
        "description": "Steganography, esoteric languages and everything in between.",
    },
]
