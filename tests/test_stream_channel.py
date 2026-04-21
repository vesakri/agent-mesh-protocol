"""Tests for stream channel multiplexing types."""


class TestStreamChannel:
    def test_stream_channel_creation(self):
        from ampro import StreamChannel
        ch = StreamChannel(
            channel_id="ch-001",
            task_id="t-42",
            created_at="2026-04-09T12:00:00Z",
        )
        assert ch.channel_id == "ch-001"
        assert ch.task_id == "t-42"
        assert ch.created_at == "2026-04-09T12:00:00Z"

    def test_stream_channel_optional_task_id(self):
        from ampro import StreamChannel
        ch = StreamChannel(
            channel_id="ch-002",
            created_at="2026-04-09T12:00:00Z",
        )
        assert ch.task_id is None


class TestStreamChannelOpenEvent:
    def test_channel_open_event(self):
        from ampro import StreamChannelOpenEvent
        event = StreamChannelOpenEvent(
            channel_id="ch-010",
            task_id="t-99",
            created_at="2026-04-09T13:00:00Z",
        )
        assert event.channel_id == "ch-010"
        assert event.task_id == "t-99"
        assert event.created_at == "2026-04-09T13:00:00Z"


class TestStreamChannelCloseEvent:
    def test_channel_close_event_default_reason(self):
        from ampro import StreamChannelCloseEvent
        event = StreamChannelCloseEvent(channel_id="ch-010")
        assert event.channel_id == "ch-010"
        assert event.reason == "complete"

    def test_channel_close_event_custom_reason(self):
        from ampro import StreamChannelCloseEvent
        event = StreamChannelCloseEvent(
            channel_id="ch-010",
            reason="error",
        )
        assert event.reason == "error"


class TestStreamingEventTypeChannelMembers:
    def test_streaming_event_type_has_channel_open(self):
        from ampro import StreamingEventType
        assert hasattr(StreamingEventType, "STREAM_CHANNEL_OPEN")
        assert StreamingEventType.STREAM_CHANNEL_OPEN == "stream.channel_open"

    def test_streaming_event_type_has_channel_close(self):
        from ampro import StreamingEventType
        assert hasattr(StreamingEventType, "STREAM_CHANNEL_CLOSE")
        assert StreamingEventType.STREAM_CHANNEL_CLOSE == "stream.channel_close"
