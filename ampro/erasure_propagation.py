"""
Agent Protocol — Erasure Propagation Status.

Tracks GDPR erasure requests as they propagate across the agent mesh.
When Agent A requests erasure from Agent B, and B had shared data with
Agent C, B reports back to A via erasure.propagation_status for each
downstream agent.

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ErasurePropagationStatus(str, Enum):
    """Possible states for an erasure propagation report."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ErasurePropagationStatusBody(BaseModel):
    """body.type = 'erasure.propagation_status' — downstream erasure report."""

    erasure_id: str = Field(description="ID of the original erasure request")
    agent_id: str = Field(description="Agent reporting its erasure status")
    status: str = Field(
        description="Propagation status: pending, completed, or failed",
    )
    records_affected: int = Field(
        description="Number of records erased or attempted",
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp of this status report",
    )
    detail: str | None = Field(
        default=None,
        description="Human-readable detail, especially on failure",
    )
    downstream_agents: list[str] = Field(
        default_factory=list,
        description="Agents this node propagated the erasure to",
    )

    model_config = {"extra": "ignore"}
