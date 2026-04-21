"""Tests for C13 — StreamBus replay/events authorization.

Validates that ``replay_from()`` and ``events()`` require the caller
to be in ``authorized_subscribers`` (registered via ``subscribe()``).
"""

from __future__ import annotations

import pytest

from ampro.streaming.bus import StreamBus
from ampro.streaming.events import StreamingEvent, StreamingEventType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bus(task_id: str = "task-1") -> StreamBus:
    return StreamBus(task_id)


def _emit_n(bus: StreamBus, n: int = 3) -> None:
    """Emit *n* TEXT_DELTA events into *bus*."""
    for i in range(n):
        bus.emit(
            StreamingEvent(
                type=StreamingEventType.TEXT_DELTA,
                data={"text": f"chunk-{i}"},
            )
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStreamReplayAuth:
    """C13: replay_from and events require authorized subscriber."""

    def test_subscribe_then_replay(self):
        """Subscribed caller can replay buffered events."""
        bus = _make_bus()
        _emit_n(bus, 3)

        bus.subscribe("agent-a")
        replayed = bus.replay_from(0, subscriber_id="agent-a")

        assert len(replayed) == 3
        assert replayed[0].data["text"] == "chunk-0"
        assert replayed[2].data["text"] == "chunk-2"

    def test_replay_without_subscribing_raises(self):
        """Unsubscribed caller gets PermissionError on replay_from."""
        bus = _make_bus()
        _emit_n(bus, 2)

        with pytest.raises(PermissionError, match="not authorized"):
            bus.replay_from(0, subscriber_id="intruder")

    @pytest.mark.asyncio
    async def test_subscribe_then_events(self):
        """Subscribed caller can iterate events via async generator."""
        bus = _make_bus()
        bus.subscribe("agent-b")

        # Emit events, then close so the iterator terminates.
        _emit_n(bus, 2)
        bus.close()

        collected: list[StreamingEvent] = []
        async for ev in bus.events(subscriber_id="agent-b"):
            collected.append(ev)

        # 2 data events + 1 DONE from close()
        assert len(collected) == 3
        assert collected[0].data["text"] == "chunk-0"
        assert collected[-1].type == StreamingEventType.DONE

    @pytest.mark.asyncio
    async def test_events_without_subscribing_raises(self):
        """Unsubscribed caller gets PermissionError on events()."""
        bus = _make_bus()
        _emit_n(bus, 1)
        bus.close()

        with pytest.raises(PermissionError, match="not authorized"):
            async for _ in bus.events(subscriber_id="intruder"):
                pass  # pragma: no cover — should never reach here

    def test_two_subscribers_independent_replay_windows(self):
        """Two subscribers each see only events after their own last_event_id."""
        bus = _make_bus()

        bus.subscribe("alpha")
        bus.subscribe("beta")

        # Emit 5 events (ids 1..5)
        _emit_n(bus, 5)

        # alpha replays from id 2 → should get events 3, 4, 5
        alpha_replay = bus.replay_from(2, subscriber_id="alpha")
        assert len(alpha_replay) == 3
        assert [int(e.id) for e in alpha_replay] == [3, 4, 5]

        # beta replays from id 4 → should get event 5
        beta_replay = bus.replay_from(4, subscriber_id="beta")
        assert len(beta_replay) == 1
        assert int(beta_replay[0].id) == 5

        # Confirm that an unsubscribed third party cannot replay
        with pytest.raises(PermissionError):
            bus.replay_from(0, subscriber_id="gamma")
