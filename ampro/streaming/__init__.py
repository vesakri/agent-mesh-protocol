"""SSE streaming events, backpressure, and channels."""

from ampro.streaming.auth import StreamAuthRefreshEvent
from ampro.streaming.backpressure import (
    StreamAckEvent,
    StreamPauseEvent,
    StreamResumeEvent,
)
from ampro.streaming.bus import StreamBus, cleanup_stream, get_or_create_stream
from ampro.streaming.channel import (
    StreamChannel,
    StreamChannelCloseEvent,
    StreamChannelOpenEvent,
)
from ampro.streaming.checkpoint import StreamCheckpointEvent
from ampro.streaming.events import StreamingEvent, StreamingEventType

__all__ = [
    # Events
    "StreamingEventType", "StreamingEvent",
    # Backpressure
    "StreamAckEvent", "StreamPauseEvent", "StreamResumeEvent",
    # Channels
    "StreamChannel", "StreamChannelOpenEvent", "StreamChannelCloseEvent",
    # Checkpoints
    "StreamCheckpointEvent",
    # Auth
    "StreamAuthRefreshEvent",
    # Bus
    "StreamBus", "get_or_create_stream", "cleanup_stream",
]
