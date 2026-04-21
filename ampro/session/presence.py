"""
Agent Protocol — Presence Types.

Pure protocol types for agent presence and availability.
Declares the possible states an agent can be in and the
data model for presence updates (heartbeats).

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from datetime import UTC, datetime
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

    agent_id: str = Field(description="Unique identifier of the agent reporting presence")
    state: PresenceState = Field(description="Current presence state of the agent")
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), description="UTC timestamp of the last heartbeat")
    active_tasks: int = Field(default=0, description="Number of tasks the agent is currently processing")
    current_task_id: str | None = Field(default=None, description="ID of the task the agent is actively working on, if any")
    metadata: dict = Field(default_factory=dict, description="Arbitrary key-value metadata for the presence update")

    model_config = {"extra": "ignore"}
