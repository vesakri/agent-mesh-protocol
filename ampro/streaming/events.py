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


# Maximum size of a single SSE event payload. SSE has no hard limit, but
# most infra (nginx, HTTP/2 proxies, Cloudflare) starts chunking or
# dropping above roughly 1 MB. 256 KiB leaves generous headroom.
MAX_SSE_EVENT_BYTES = 262_144  # 256 KiB


class StreamingEvent(BaseModel):
    """A single streaming event for SSE delivery."""

    type: StreamingEventType
    data: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None  # Optional event ID for reconnection
    seq: int = Field(
        default=0,
        ge=0,
        description=(
            "Server-assigned monotonic sequence number for ordering. "
            "Do not set manually — StreamBus.emit() assigns this atomically."
        ),
    )
    cross_channel_seq: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Optional monotonic counter scoped to the session, not the "
            "channel. Implementations MAY provide cross_channel_seq to "
            "enable causal ordering across channels; when present, "
            "receivers MUST honour it."
        ),
    )

    def to_sse(self) -> str:
        """Format as Server-Sent Events (SSE) text.

        Raises:
            ValueError: If the serialized event exceeds
                :data:`MAX_SSE_EVENT_BYTES` (256 KiB).
        """
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.type.value}")
        lines.append(f"data: {json.dumps(self.data, default=str)}")
        lines.append("")  # Empty line terminates the event
        sse = "\n".join(lines) + "\n"
        if len(sse.encode("utf-8")) > MAX_SSE_EVENT_BYTES:
            raise ValueError(
                f"SSE event exceeds {MAX_SSE_EVENT_BYTES}-byte limit"
            )
        return sse

    model_config = {"extra": "ignore"}
