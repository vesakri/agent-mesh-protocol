"""
Agent Protocol — Stream Channels.

Multiplexing multiple logical streams on a single SSE connection.
Each channel is identified by a channel_id and can be independently
opened, used, and closed.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StreamChannel(BaseModel):
    """A single logical stream multiplexed on one SSE connection."""

    channel_id: str = Field(description="Unique channel identifier")
    task_id: str | None = Field(
        default=None,
        description="Task this channel is associated with",
    )
    created_at: str = Field(description="ISO-8601 timestamp when channel was opened")

    model_config = {"extra": "ignore"}


class StreamChannelOpenEvent(BaseModel):
    """Event emitted when a new stream channel is opened."""

    channel_id: str = Field(description="Channel being opened")
    task_id: str | None = Field(
        default=None,
        description="Task this channel serves",
    )
    created_at: str = Field(description="ISO-8601 timestamp")

    model_config = {"extra": "ignore"}


class StreamChannelCloseEvent(BaseModel):
    """Event emitted when a stream channel is closed."""

    channel_id: str = Field(description="Channel being closed")
    reason: str = Field(
        default="complete",
        description="Reason for closing (complete, error, timeout)",
    )

    model_config = {"extra": "ignore"}
