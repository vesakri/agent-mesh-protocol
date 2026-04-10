"""
Agent Protocol — Streaming Backpressure.

Flow control events for SSE streams. Prevents a fast producer from
overwhelming a slow consumer.

  stream.ack    — client tells server what it has processed
  stream.pause  — server tells client it is pausing the stream
  stream.resume — client tells server it is ready for more events

The protocol defines the event types. Implementation strategies
(ACK frequency, buffer sizing) are guidance, not protocol.

NOTE: Backpressure events are protocol primitives. Enforcement (pausing
producers, dropping events) is the responsibility of the runtime
implementation, not this library.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StreamAckEvent(BaseModel):
    """stream.ack — client tells server what it has processed."""

    last_seq: int = Field(description="Last sequence number the client has processed")
    timestamp: str = Field(description="ISO-8601 timestamp of the acknowledgment")

    model_config = {"extra": "ignore"}


class StreamPauseEvent(BaseModel):
    """stream.pause — server tells client it is pausing the stream."""

    reason: str = Field(
        description="Why the stream is paused (e.g. 'client_behind', 'buffer_full')",
    )
    resume_after_ack: int = Field(
        description="Resume when client ACKs this sequence number",
    )

    model_config = {"extra": "ignore"}


class StreamResumeEvent(BaseModel):
    """stream.resume — client tells server it is ready for more events."""

    from_seq: int = Field(description="Resume streaming from this sequence number")
    buffer_capacity: int | None = Field(
        default=None,
        description="How many events the client can buffer",
    )

    model_config = {"extra": "ignore"}
