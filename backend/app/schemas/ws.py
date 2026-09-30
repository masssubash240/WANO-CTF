"""WebSocket message contract for real-time scoreboard/announcements.

Envelope::

    { "type": "scoreboard.update", "ts": "2026-03-14T09:31:17Z", "payload": {...} }

The frontend applies these patches without reloading the page and falls back to
REST polling if the socket cannot be established (venue Wi-Fi is not reliable).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

WsEventType = Literal[
    "connection.ack",
    "ping",
    "pong",
    "scoreboard.update",
    "scoreboard.freeze",
    "scoreboard.unfreeze",
    "announcement.created",
    "announcement.updated",
    "announcement.deleted",
    "competition.status",
    "challenge.solved",
    "challenge.hint",
    "error",
]


class WsEnvelope(BaseModel):
    type: WsEventType
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def build(cls, event_type: WsEventType, payload: dict[str, Any] | None = None) -> WsEnvelope:
        return cls(type=event_type, payload=payload or {})


class WsSubscribeMessage(BaseModel):
    action: Literal["subscribe", "unsubscribe", "ping"]
    channels: list[str] = Field(default_factory=list)


class WsSolvePayload(BaseModel):
    team_id: uuid.UUID
    team_name: str
    challenge_id: uuid.UUID
    challenge_title: str
    points: int
    first_blood: bool = False
    team_score: int
    solved_count: int
