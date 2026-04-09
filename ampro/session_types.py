"""
Agent Protocol - Session Types.

Pure session types for the SESSION capability group.
Handles session lifecycle: start, resume, end, inject context.

This module contains NO platform-specific imports.
It is designed for extraction as part of pip install agent-protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionState(str, Enum):
    """Session lifecycle states.

    v0.1.1 expands from 4 to 8 states to cover the full handshake lifecycle.
    """

    IDLE = "idle"
    INIT_SENT = "init_sent"
    INIT_RECEIVED = "init_received"
    ESTABLISHED = "established"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CLOSED = "closed"


class SessionConfig(BaseModel):
    """Configuration for a new session."""

    ttl_seconds: int = Field(
        default=3600,
        ge=1,
        description="Time-to-live in seconds before the session expires",
    )
    max_messages: int = Field(
        default=100,
        ge=1,
        description="Maximum number of messages allowed in this session",
    )
    context_window: int = Field(
        default=10,
        ge=1,
        description="Number of recent messages to include in context",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata attached to the session",
    )

    model_config = {"extra": "ignore"}


class SessionContext(BaseModel):
    """Full session state."""

    session_id: str = Field(
        description="Unique session identifier (UUID)",
    )
    agent_id: str = Field(
        default="",
        description="Agent that owns this session",
    )
    org_id: str = Field(
        default="",
        description="Organization this session belongs to (optional)",
    )
    state: SessionState = Field(
        default=SessionState.ACTIVE,
        description="Current session lifecycle state",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the session was created",
    )
    last_activity: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last message activity timestamp",
    )
    message_count: int = Field(
        default=0,
        ge=0,
        description="Number of messages sent in this session",
    )
    config: SessionConfig = Field(
        default_factory=SessionConfig,
        description="Session configuration (TTL, limits, etc.)",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Session context - injected key/value pairs persisted across messages",
    )

    model_config = {"extra": "ignore"}
