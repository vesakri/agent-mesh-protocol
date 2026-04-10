"""Tests for stream checkpoint types."""
import pytest
from pydantic import ValidationError


class TestStreamCheckpointEvent:
    def test_checkpoint_creation(self):
        from ampro import StreamCheckpointEvent
        cp = StreamCheckpointEvent(
            checkpoint_id="cp-001",
            seq=10,
            state_snapshot={"cursor": "abc123", "offset": 42},
            timestamp="2026-04-09T14:00:00Z",
        )
        assert cp.checkpoint_id == "cp-001"
        assert cp.seq == 10
        assert cp.state_snapshot == {"cursor": "abc123", "offset": 42}
        assert cp.timestamp == "2026-04-09T14:00:00Z"

    def test_checkpoint_seq_ge_zero(self):
        from ampro import StreamCheckpointEvent
        # seq=0 should be valid
        cp = StreamCheckpointEvent(
            checkpoint_id="cp-002",
            seq=0,
            timestamp="2026-04-09T14:00:00Z",
        )
        assert cp.seq == 0

        # seq=-1 should fail
        with pytest.raises(ValidationError):
            StreamCheckpointEvent(
                checkpoint_id="cp-bad",
                seq=-1,
                timestamp="2026-04-09T14:00:00Z",
            )

    def test_checkpoint_empty_snapshot(self):
        from ampro import StreamCheckpointEvent
        cp = StreamCheckpointEvent(
            checkpoint_id="cp-003",
            seq=5,
            timestamp="2026-04-09T14:00:00Z",
        )
        assert cp.state_snapshot == {}

    def test_checkpoint_nested_snapshot(self):
        from ampro import StreamCheckpointEvent
        nested = {
            "channels": {
                "ch-1": {"last_seq": 10},
                "ch-2": {"last_seq": 20, "meta": {"label": "audit"}},
            },
            "cursors": [1, 2, 3],
        }
        cp = StreamCheckpointEvent(
            checkpoint_id="cp-004",
            seq=100,
            state_snapshot=nested,
            timestamp="2026-04-09T14:00:00Z",
        )
        assert cp.state_snapshot["channels"]["ch-2"]["meta"]["label"] == "audit"

    def test_streaming_event_type_has_checkpoint(self):
        from ampro import StreamingEventType
        assert hasattr(StreamingEventType, "STREAM_CHECKPOINT")
        assert StreamingEventType.STREAM_CHECKPOINT == "stream.checkpoint"
