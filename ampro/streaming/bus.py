"""
Agent Protocol — StreamBus.

Per-task event bus backed by asyncio.Queue with ring-buffer replay
for SSE reconnection support.  Each task_id gets its own StreamBus
registered in a global ``_active_streams`` dict.

Public API
----------
- ``get_or_create_stream(task_id)`` → ``StreamBus``
- ``cleanup_stream(task_id)``
- ``StreamBus.subscribe(subscriber_id)``
- ``StreamBus.emit(event)``
- ``StreamBus.events(subscriber_id)``  (async iterator, auth-gated)
- ``StreamBus.replay_from(last_event_id, subscriber_id=...)``  (auth-gated)
- ``StreamBus.close()``
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator

from ampro.streaming.events import StreamingEvent, StreamingEventType

# ---------------------------------------------------------------------------
# Ring buffer capacity — keeps the latest N events for replay
# ---------------------------------------------------------------------------
_RING_BUFFER_CAPACITY = 100

# Maximum number of active streams in the global registry.
# Prevents unbounded memory growth from leaked or abandoned streams.
MAX_ACTIVE_STREAMS = 10_000

# Sentinel used to signal the consumer that the stream is finished.
_SENTINEL = object()


class StreamBus:
    """Per-task event bus with async queue + ring-buffer replay."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self._queue: asyncio.Queue[StreamingEvent | object] = asyncio.Queue(maxsize=1000)
        self._ring: deque[StreamingEvent] = deque(maxlen=_RING_BUFFER_CAPACITY)
        self._seq: int = 0  # monotonically increasing event id
        self._closed: bool = False
        self._dropped_count: int = 0
        self._authorized_subscribers: set[str] = set()

    # ----- subscription -----

    def subscribe(self, subscriber_id: str) -> None:
        """Authorize *subscriber_id* to consume events from this bus.

        Must be called before ``events()`` or ``replay_from()`` to
        grant read access.
        """
        if not subscriber_id:
            raise ValueError("subscriber_id must be a non-empty string")
        self._authorized_subscribers.add(subscriber_id)

    def _check_authorized(self, subscriber_id: str) -> None:
        """Raise ``PermissionError`` if *subscriber_id* is not subscribed."""
        if subscriber_id not in self._authorized_subscribers:
            raise PermissionError(
                f"subscriber '{subscriber_id}' is not authorized on stream "
                f"'{self.task_id}'"
            )

    # ----- writing side -----

    def emit(self, event: StreamingEvent) -> None:
        """Assign a sequential ID, store in ring buffer, and enqueue."""
        if self._closed:
            return
        self._seq += 1
        # Stamp the event with an integer id (as string for SSE spec)
        event = event.model_copy(update={"id": str(self._seq), "seq": self._seq})
        self._ring.append(event)
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._dropped_count += 1  # Track drops so consumers can detect gaps

    def close(self) -> None:
        """Emit a DONE event (if not already closed) and signal end of stream."""
        if self._closed:
            return
        self._closed = True
        # Emit a terminal DONE event
        done_event = StreamingEvent(
            type=StreamingEventType.DONE,
            data={"finish_reason": "stream_closed"},
        )
        self._seq += 1
        done_event = done_event.model_copy(update={"id": str(self._seq), "seq": self._seq})
        self._ring.append(done_event)
        self._queue.put_nowait(done_event)
        # Put sentinel so the async iterator exits
        self._queue.put_nowait(_SENTINEL)

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def last_event_id(self) -> int:
        return self._seq

    @property
    def dropped_count(self) -> int:
        """Number of events dropped because the consumer queue was full."""
        return self._dropped_count

    # ----- reading side -----

    async def events(self, subscriber_id: str) -> AsyncIterator[StreamingEvent]:
        """Yield events as they arrive.  Stops when the bus is closed.

        Raises ``PermissionError`` if *subscriber_id* has not been
        registered via ``subscribe()``.
        """
        self._check_authorized(subscriber_id)
        while True:
            item = await self._queue.get()
            if item is _SENTINEL:
                return
            # item is a StreamingEvent at this point
            yield item  # type: ignore[misc]

    def replay_from(
        self, last_event_id: int, *, subscriber_id: str
    ) -> list[StreamingEvent]:
        """Return buffered events with id > ``last_event_id``.

        Used for SSE reconnection: the client sends ``Last-Event-ID``
        and the server replays everything that was emitted after that id.

        Raises ``PermissionError`` if *subscriber_id* has not been
        registered via ``subscribe()``.
        """
        self._check_authorized(subscriber_id)
        result: list[StreamingEvent] = []
        for ev in self._ring:
            ev_id = int(ev.id) if ev.id else 0
            if ev_id > last_event_id:
                result.append(ev)
        return result


# ---------------------------------------------------------------------------
# Global stream registry
# ---------------------------------------------------------------------------
_active_streams: dict[str, StreamBus] = {}


def get_or_create_stream(task_id: str) -> StreamBus:
    """Return the existing StreamBus for *task_id*, or create a new one.

    Raises RuntimeError if the global stream registry has reached
    MAX_ACTIVE_STREAMS to prevent unbounded memory growth.
    """
    if task_id not in _active_streams:
        if len(_active_streams) >= MAX_ACTIVE_STREAMS:
            raise RuntimeError(
                f"Maximum active streams ({MAX_ACTIVE_STREAMS}) reached. "
                "Clean up completed streams before creating new ones."
            )
        _active_streams[task_id] = StreamBus(task_id)
    return _active_streams[task_id]


def cleanup_stream(task_id: str) -> None:
    """Remove the StreamBus for *task_id* from the global registry."""
    bus = _active_streams.pop(task_id, None)
    if bus and not bus.closed:
        bus.close()
