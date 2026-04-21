"""Tests for P0.D HIGH findings: Task 5.5, 5.6, 5.8.

Task 5.5 — StreamingEvent seq is server-assigned (via StreamBus.emit).
Task 5.6 — validate_body rejects empty/whitespace/None body_type.
Task 5.8 — AgentMessage id defaults to UUID, but accepts any string.
"""

from __future__ import annotations

import uuid

import pytest

from ampro.core.body_schemas import validate_body
from ampro.core.envelope import AgentMessage
from ampro.streaming.bus import StreamBus
from ampro.streaming.events import StreamingEvent, StreamingEventType


# ---------------------------------------------------------------------------
# Task 5.5 — Stream Seq Server-Assigned
# ---------------------------------------------------------------------------


class TestStreamSeqServerAssigned:
    """seq field defaults to 0 and is overridden by StreamBus.emit()."""

    def test_seq_defaults_to_zero(self):
        """A freshly created StreamingEvent has seq=0."""
        ev = StreamingEvent(
            type=StreamingEventType.TEXT_DELTA,
            data={"text": "hello"},
        )
        assert ev.seq == 0

    def test_seq_overridden_via_model_copy(self):
        """Server can override seq using model_copy (simulating bus.emit)."""
        ev = StreamingEvent(
            type=StreamingEventType.TEXT_DELTA,
            data={"text": "hello"},
        )
        updated = ev.model_copy(update={"seq": 42})
        assert updated.seq == 42
        # Original is unchanged
        assert ev.seq == 0

    def test_bus_emit_assigns_sequential_ids(self):
        """StreamBus.emit() assigns monotonically increasing seq values."""
        bus = StreamBus("task-seq-test")
        bus.subscribe("sub-1")

        for _ in range(5):
            bus.emit(
                StreamingEvent(
                    type=StreamingEventType.TEXT_DELTA,
                    data={"text": "chunk"},
                )
            )

        replayed = bus.replay_from(0, subscriber_id="sub-1")
        seqs = [ev.seq for ev in replayed]
        assert seqs == [1, 2, 3, 4, 5]

    def test_bus_emit_overwrites_caller_seq(self):
        """Even if the caller sets seq, StreamBus.emit() overwrites it."""
        bus = StreamBus("task-overwrite-test")
        bus.subscribe("sub-1")

        ev = StreamingEvent(
            type=StreamingEventType.TEXT_DELTA,
            data={"text": "sneaky"},
            seq=999,
        )
        bus.emit(ev)

        replayed = bus.replay_from(0, subscriber_id="sub-1")
        assert len(replayed) == 1
        assert replayed[0].seq == 1  # Server-assigned, not 999

    def test_seq_negative_rejected(self):
        """seq field has ge=0 constraint — negative values are rejected."""
        with pytest.raises(Exception):
            StreamingEvent(
                type=StreamingEventType.TEXT_DELTA,
                data={"text": "bad"},
                seq=-1,
            )


# ---------------------------------------------------------------------------
# Task 5.6 — Body Type Empty String Validation
# ---------------------------------------------------------------------------


class TestBodyTypeEmptyStringValidation:
    """validate_body rejects None, empty, and whitespace body_type."""

    def test_body_type_none_raises(self):
        """validate_body(None, ...) raises ValueError."""
        with pytest.raises(ValueError, match="body_type is required"):
            validate_body(None, {"text": "hello"})  # type: ignore[arg-type]

    def test_body_type_empty_string_raises(self):
        """validate_body('', ...) raises ValueError."""
        with pytest.raises(ValueError, match="body_type cannot be empty"):
            validate_body("", {"text": "hello"})

    def test_body_type_whitespace_raises(self):
        """validate_body('   ', ...) raises ValueError."""
        with pytest.raises(ValueError, match="body_type cannot be empty"):
            validate_body("   ", {"text": "hello"})

    def test_body_type_tabs_and_newlines_raises(self):
        """validate_body with tabs/newlines raises ValueError."""
        with pytest.raises(ValueError, match="body_type cannot be empty"):
            validate_body("\t\n", {"text": "hello"})

    def test_known_body_type_validates(self):
        """validate_body('task.create', ...) returns validated model."""
        result = validate_body("task.create", {
            "description": "Find me a hotel",
        })
        assert hasattr(result, "description")
        assert result.description == "Find me a hotel"  # type: ignore[union-attr]

    def test_unknown_body_type_passthrough(self):
        """validate_body('x-custom.type', ...) returns raw dict."""
        body = {"foo": "bar", "baz": 42}
        result = validate_body("x-custom.type", body)
        assert result == body
        assert isinstance(result, dict)

    def test_message_body_type_validates(self):
        """validate_body('message', ...) returns MessageBody."""
        result = validate_body("message", {"text": "hello world"})
        assert hasattr(result, "text")
        assert result.text == "hello world"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Task 5.8 — Message ID: auto-UUID default, accepts any string
# ---------------------------------------------------------------------------


class TestMessageIdFormat:
    """AgentMessage id defaults to UUID but accepts any explicit string.

    ID format enforcement belongs at the dedup layer, not the model layer,
    because protocol consumers may use different ID formats.
    """

    def test_auto_generated_id_is_valid_uuid(self):
        """Default id (from uuid4 factory) is a valid UUID."""
        msg = AgentMessage(
            sender="@alice",
            recipient="@bob",
            body="hello",
        )
        # Should parse as a valid UUID
        parsed = uuid.UUID(msg.id)
        assert str(parsed) == msg.id.lower()

    def test_valid_uuid_accepted(self):
        """Explicitly providing a valid UUID is accepted."""
        valid_id = str(uuid.uuid4())
        msg = AgentMessage(
            sender="@alice",
            recipient="@bob",
            id=valid_id,
            body="hello",
        )
        assert msg.id == valid_id

    def test_custom_string_id_accepted(self):
        """Custom non-UUID string IDs are accepted."""
        msg = AgentMessage(
            sender="@alice",
            recipient="@bob",
            id="my-custom-id",
            body="hello",
        )
        assert msg.id == "my-custom-id"

    def test_empty_string_id_accepted(self):
        """Empty string id is accepted (format is not enforced at model layer)."""
        msg = AgentMessage(
            sender="@alice",
            recipient="@bob",
            id="",
            body="hello",
        )
        assert msg.id == ""

    def test_numeric_id_accepted(self):
        """Numeric-only id is accepted."""
        msg = AgentMessage(
            sender="@alice",
            recipient="@bob",
            id="12345",
            body="hello",
        )
        assert msg.id == "12345"

    def test_two_messages_have_unique_ids(self):
        """Two auto-created messages get different IDs."""
        msg1 = AgentMessage(sender="@alice", recipient="@bob", body="hi")
        msg2 = AgentMessage(sender="@alice", recipient="@bob", body="there")
        assert msg1.id != msg2.id
