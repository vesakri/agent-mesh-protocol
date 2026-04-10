"""
Agent Protocol — Stream Checkpoints.

Periodic state snapshots for reconnection. Clients resume from the
last checkpoint instead of replaying all events from the beginning.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StreamCheckpointEvent(BaseModel):
    """Periodic state snapshot emitted on the SSE stream."""

    checkpoint_id: str = Field(description="Unique checkpoint identifier")
    seq: int = Field(ge=0, description="Sequence number at this checkpoint")
    state_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized state at this point",
    )
    timestamp: str = Field(description="ISO-8601 timestamp")

    model_config = {"extra": "ignore"}
