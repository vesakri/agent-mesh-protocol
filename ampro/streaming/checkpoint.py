"""
Agent Protocol — Stream Checkpoints.

Periodic state snapshots for reconnection. Clients resume from the
last checkpoint instead of replaying all events from the beginning.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


# Maximum serialized size of a checkpoint state_snapshot. Larger snapshots
# are rejected to prevent memory exhaustion and protect proxies/infra that
# buffer SSE events.
MAX_STATE_SNAPSHOT_BYTES = 1_048_576  # 1 MiB


class StreamCheckpointEvent(BaseModel):
    """Periodic state snapshot emitted on the SSE stream."""

    checkpoint_id: str = Field(description="Unique checkpoint identifier")
    seq: int = Field(ge=0, description="Sequence number at this checkpoint")
    state_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized state at this point (<= 1 MiB when JSON-encoded)",
    )
    timestamp: str = Field(description="ISO-8601 timestamp")

    model_config = {"extra": "ignore"}

    @field_validator("state_snapshot")
    @classmethod
    def _validate_state_snapshot_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            serialized = json.dumps(value, default=str)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"state_snapshot must be JSON-serializable: {exc}") from exc
        if len(serialized.encode("utf-8")) > MAX_STATE_SNAPSHOT_BYTES:
            raise ValueError("state_snapshot exceeds 1 MiB size limit")
        return value
