"""
Agent Protocol — Heartbeat Emitter.

Emits periodic heartbeat events on SSE streams to keep connections
alive through proxies and detect dead clients.

Spec ref: Section 5.1 — heartbeat every 15 seconds.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from ampro.streaming.events import StreamingEvent, StreamingEventType


class HeartbeatEmitter:
    """Emits heartbeat events at a fixed interval."""

    def __init__(self, interval_seconds: float = 15.0):
        self._interval = interval_seconds
        self._running = False
        self._seq_counter = 0

    async def emit(self, session_id: str = "") -> AsyncIterator[StreamingEvent]:
        """Yield heartbeat events at the configured interval."""
        self._running = True
        try:
            while self._running:
                await asyncio.sleep(self._interval)
                if not self._running:
                    break
                self._seq_counter += 1
                yield StreamingEvent(
                    type=StreamingEventType.HEARTBEAT,
                    seq=self._seq_counter,
                    id=f"{session_id}:{self._seq_counter}" if session_id else "",
                )
        finally:
            self._running = False

    def stop(self) -> None:
        """Stop the heartbeat emitter."""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
