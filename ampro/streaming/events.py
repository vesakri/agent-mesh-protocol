"""
Agent Protocol — Streaming Events.

17 event types for real-time agent processing updates via SSE.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StreamingEventType(str, Enum):
    """The 17 protocol streaming event types."""

    THINKING = "thinking"          # Agent is reasoning
    TOOL_CALL = "tool_call"        # Agent is invoking a tool
    TOOL_RESULT = "tool_result"    # Tool returned a result
    TEXT_DELTA = "text_delta"      # Partial text response
    STATE_CHANGE = "state_change"  # Task status changed
    AGENT_CALL = "agent_call"      # Agent is delegating to another agent
    AGENT_RESULT = "agent_result"  # Delegated agent returned
    ERROR = "error"                # Something went wrong
    HEARTBEAT = "heartbeat"        # Keepalive ping (no payload)
    DONE = "done"                  # Final event — stream complete

    # Backpressure flow control (see ampro.backpressure)
    STREAM_ACK = "stream.ack"         # Client ACKs processed events
    STREAM_PAUSE = "stream.pause"     # Server pauses the stream
    STREAM_RESUME = "stream.resume"   # Client signals ready for more

    # Stream multiplexing and lifecycle (see ampro.stream_channel, stream_checkpoint, stream_auth)
    STREAM_CHANNEL_OPEN = "stream.channel_open"    # Open a logical channel
    STREAM_CHANNEL_CLOSE = "stream.channel_close"  # Close a logical channel
    STREAM_CHECKPOINT = "stream.checkpoint"         # Periodic state snapshot
    STREAM_AUTH_REFRESH = "stream.auth_refresh"     # Mid-stream token renewal


class StreamingEvent(BaseModel):
    """A single streaming event for SSE delivery."""

    type: StreamingEventType
    data: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None  # Optional event ID for reconnection
    seq: int = Field(
        default=0,
        ge=0,
        description="Monotonic sequence number for ordering, starts at 1",
    )

    def to_sse(self) -> str:
        """Format as Server-Sent Events (SSE) text."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.type.value}")
        lines.append(f"data: {json.dumps(self.data, default=str)}")
        lines.append("")  # Empty line terminates the event
        return "\n".join(lines) + "\n"

    model_config = {"extra": "ignore"}
