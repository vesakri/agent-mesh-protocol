"""
Agent Protocol — Presence Types.

Pure protocol types for agent presence and availability.
Declares the possible states an agent can be in and the
data model for presence updates (heartbeats).

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class PresenceState(str, Enum):
    """Possible presence states for an agent."""

    ONLINE = "online"
    BUSY = "busy"
    SLEEPING = "sleeping"
    PAUSED = "paused"
    OFFLINE = "offline"


class PresenceUpdate(BaseModel):
    """A presence heartbeat from an agent."""

    agent_id: str
    state: PresenceState
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_tasks: int = 0
    current_task_id: str | None = None
    metadata: dict = Field(default_factory=dict)

    model_config = {"extra": "ignore"}
