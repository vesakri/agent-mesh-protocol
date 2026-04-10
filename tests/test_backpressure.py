"""Tests for streaming backpressure event types."""
import pytest
from pydantic import ValidationError


class TestStreamAckEvent:
    def test_all_fields(self):
        from ampro import StreamAckEvent
        event = StreamAckEvent(
            last_seq=42,
            timestamp="2026-04-09T12:00:00Z",
        )
        assert event.last_seq == 42
        assert event.timestamp == "2026-04-09T12:00:00Z"

    def test_missing_required_raises(self):
        from ampro import StreamAckEvent
        with pytest.raises(ValidationError):
            StreamAckEvent(last_seq=10)  # missing timestamp


class TestStreamPauseEvent:
    def test_all_fields(self):
        from ampro import StreamPauseEvent
        event = StreamPauseEvent(
            reason="client_behind",
            resume_after_ack=40,
        )
        assert event.reason == "client_behind"
        assert event.resume_after_ack == 40

    def test_missing_required_raises(self):
        from ampro import StreamPauseEvent
        with pytest.raises(ValidationError):
            StreamPauseEvent(reason="buffer_full")  # missing resume_after_ack


class TestStreamResumeEvent:
    def test_all_fields(self):
        from ampro import StreamResumeEvent
        event = StreamResumeEvent(
            from_seq=41,
            buffer_capacity=100,
        )
        assert event.from_seq == 41
        assert event.buffer_capacity == 100

    def test_buffer_capacity_optional(self):
        from ampro import StreamResumeEvent
        event = StreamResumeEvent(from_seq=41)
        assert event.buffer_capacity is None

    def test_missing_from_seq_raises(self):
        from ampro import StreamResumeEvent
        with pytest.raises(ValidationError):
            StreamResumeEvent()  # missing from_seq


class TestStreamingEventTypeBackpressure:
    def test_stream_ack_value(self):
        from ampro import StreamingEventType
        assert StreamingEventType.STREAM_ACK == "stream.ack"

    def test_stream_pause_value(self):
        from ampro import StreamingEventType
        assert StreamingEventType.STREAM_PAUSE == "stream.pause"

    def test_stream_resume_value(self):
        from ampro import StreamingEventType
        assert StreamingEventType.STREAM_RESUME == "stream.resume"

    def test_seventeen_total_events(self):
        from ampro import StreamingEventType
        assert len(StreamingEventType) == 17
