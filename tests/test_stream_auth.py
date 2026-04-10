"""Tests for stream auth refresh types."""
import pytest
from pydantic import ValidationError


class TestStreamAuthRefreshEvent:
    def test_auth_refresh_creation(self):
        from ampro import StreamAuthRefreshEvent
        event = StreamAuthRefreshEvent(
            method="jwt",
            token="eyJhbGciOiJSUzI1NiJ9.new-token",
            expires_at="2026-04-09T15:00:00Z",
        )
        assert event.method == "jwt"
        assert event.token == "eyJhbGciOiJSUzI1NiJ9.new-token"
        assert event.expires_at == "2026-04-09T15:00:00Z"

    def test_auth_refresh_all_fields_required(self):
        from ampro import StreamAuthRefreshEvent
        # Missing method
        with pytest.raises(ValidationError):
            StreamAuthRefreshEvent(
                token="tok",
                expires_at="2026-04-09T15:00:00Z",
            )
        # Missing token
        with pytest.raises(ValidationError):
            StreamAuthRefreshEvent(
                method="jwt",
                expires_at="2026-04-09T15:00:00Z",
            )
        # Missing expires_at
        with pytest.raises(ValidationError):
            StreamAuthRefreshEvent(
                method="jwt",
                token="tok",
            )

    def test_auth_refresh_jwt_method(self):
        from ampro import StreamAuthRefreshEvent
        event = StreamAuthRefreshEvent(
            method="jwt",
            token="refreshed-jwt-token",
            expires_at="2026-04-09T16:00:00Z",
        )
        assert event.method == "jwt"

    def test_streaming_event_type_has_auth_refresh(self):
        from ampro import StreamingEventType
        assert hasattr(StreamingEventType, "STREAM_AUTH_REFRESH")
        assert StreamingEventType.STREAM_AUTH_REFRESH == "stream.auth_refresh"
