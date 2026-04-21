"""
Agent Protocol — Event Types for Pub/Sub.

Defines the event model for agent-to-agent pub/sub communication.
EventType enumerates the standard topics. EventSubscription and
EventNotification are the wire-format models exchanged between
subscribers and the events manager.

This module is PURE — no platform-specific imports allowed.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Standard event topic types for the agent protocol."""

    TASK_CREATED = "task.create"
    TASK_COMPLETED = "task.complete"
    TASK_FAILED = "task.error"
    MESSAGE_RECEIVED = "message.receive"
    TOOL_INVOKED = "tool.invoke"
    AGENT_JOINED = "agent.join"
    AGENT_LEFT = "agent.leave"
    CUSTOM = "custom"


class EventSubscription(BaseModel):
    """
    A subscription binding a subscriber agent to one or more topic patterns.

    Topics support glob patterns (e.g. ``task.*`` matches ``task.create``
    and ``task.complete``).
    """

    subscription_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique subscription identifier",
    )
    subscriber: str = Field(
        description="Agent ID of the subscriber",
    )
    topics: list[str] = Field(
        description="Glob patterns for topics to subscribe to (e.g. ['task.*'])",
    )
    filters: dict = Field(
        default_factory=dict,
        description="Optional key-value filters to narrow matching events",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the subscription was created",
    )

    model_config = {"extra": "ignore"}


class EventNotification(BaseModel):
    """
    A published event notification delivered to matching subscribers.

    The ``_depth`` field tracks cascade depth to prevent infinite fan-out
    loops (capped at 3).
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier for dedup",
    )
    topic: str = Field(
        description="The event topic (e.g. 'task.create')",
    )
    source: str = Field(
        description="Agent ID that published the event",
    )
    data: dict = Field(
        default_factory=dict,
        description="Event payload",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the event was created",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Optional correlation ID for tracing related events",
    )
    _depth: int = 0  # Private: cascade depth counter (not serialized by default)

    model_config = {"extra": "ignore"}

    def with_depth(self, depth: int) -> EventNotification:
        """Return a copy with the given cascade depth."""
        clone = self.model_copy()
        clone._depth = depth
        return clone
