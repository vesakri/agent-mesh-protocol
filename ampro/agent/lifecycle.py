"""
Agent Protocol — Agent Lifecycle.

Status management and orderly shutdown for agents in the mesh.

Agents declare their lifecycle status in agent.json:
  - active: operational, accepting new sessions
  - deactivating: shutting down, no new sessions, draining existing work
  - decommissioned: permanently offline, registry returns 410 Gone
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentLifecycleStatus(str, Enum):
    """Possible lifecycle statuses for an agent in the mesh."""

    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    DECOMMISSIONED = "decommissioned"


class AgentDeactivationNoticeBody(BaseModel):
    """body.type = 'agent.deactivation_notice' — Notify peers of orderly shutdown."""

    agent_id: str = Field(
        description="agent:// URI of the agent being deactivated",
    )
    reason: str = Field(
        description="Human-readable reason for deactivation",
    )
    deactivation_time: str = Field(
        description="ISO-8601 timestamp when deactivation started",
    )
    active_sessions: int = Field(
        description="Number of sessions still open",
    )
    migration_endpoint: str | None = Field(
        default=None,
        description="Endpoint of a replacement agent, if available",
    )
    final_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when agent will go fully offline",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional context",
    )

    model_config = {"extra": "ignore"}
