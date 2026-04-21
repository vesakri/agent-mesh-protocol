"""Tests for field length limits on body schema models (Task 5.7).

Validates that all Body models in ampro.core.body_schemas enforce
max_length on string fields, numeric bounds on int/float fields,
and max_length on list fields to prevent DoS via oversized payloads.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ampro.core.body_schemas import (
    DataConsentRequestBody,
    DataConsentResponseBody,
    MessageBody,
    NotificationBody,
    TaskAcknowledgeBody,
    TaskAssignBody,
    TaskCompleteBody,
    TaskCreateBody,
    TaskDelegateBody,
    TaskErrorBody,
    TaskEscalateBody,
    TaskInputRequiredBody,
    TaskProgressBody,
    TaskQuoteBody,
    TaskRejectBody,
    TaskRerouteBody,
    TaskResponseBody,
    TaskSpawnBody,
    TaskTransferBody,
)

# ---------------------------------------------------------------------------
# String max_length enforcement
# ---------------------------------------------------------------------------


class TestStringMaxLength:
    """String fields exceeding max_length must raise ValidationError."""

    def test_message_text_too_long(self):
        with pytest.raises(ValidationError):
            MessageBody(text="x" * 65537)

    def test_message_text_at_limit(self):
        body = MessageBody(text="x" * 65536)
        assert len(body.text) == 65536

    def test_task_create_description_too_long(self):
        with pytest.raises(ValidationError):
            TaskCreateBody(description="x" * 8193)

    def test_task_create_description_at_limit(self):
        body = TaskCreateBody(description="x" * 8192)
        assert len(body.description) == 8192

    def test_task_create_task_id_too_long(self):
        with pytest.raises(ValidationError):
            TaskCreateBody(description="ok", task_id="x" * 257)

    def test_task_assign_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskAssignBody(task_id="x" * 257, assignee="@bob")
        with pytest.raises(ValidationError):
            TaskAssignBody(task_id="t-1", assignee="x" * 257)
        with pytest.raises(ValidationError):
            TaskAssignBody(task_id="t-1", assignee="@bob", reason="x" * 8193)

    def test_task_delegate_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskDelegateBody(
                task_id="x" * 257,
                description="ok",
                delegation_chain=[],
            )
        with pytest.raises(ValidationError):
            TaskDelegateBody(
                task_id="t-1",
                description="x" * 8193,
                delegation_chain=[],
            )

    def test_task_spawn_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskSpawnBody(
                parent_task_id="x" * 257,
                description="ok",
            )
        with pytest.raises(ValidationError):
            TaskSpawnBody(
                parent_task_id="t-1",
                description="x" * 8193,
            )

    def test_task_quote_task_id_too_long(self):
        with pytest.raises(ValidationError):
            TaskQuoteBody(
                task_id="x" * 257,
                expires_at="2026-01-01T00:00:00Z",
            )

    def test_notification_fields_too_long(self):
        with pytest.raises(ValidationError):
            NotificationBody(topic="x" * 257, message="ok")
        with pytest.raises(ValidationError):
            NotificationBody(topic="test", message="x" * 8193)

    def test_task_progress_message_too_long(self):
        with pytest.raises(ValidationError):
            TaskProgressBody(task_id="t-1", message="x" * 8193)

    def test_task_input_required_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskInputRequiredBody(
                task_id="x" * 257,
                reason="ok",
                prompt="ok",
            )
        with pytest.raises(ValidationError):
            TaskInputRequiredBody(
                task_id="t-1",
                reason="x" * 8193,
                prompt="ok",
            )
        with pytest.raises(ValidationError):
            TaskInputRequiredBody(
                task_id="t-1",
                reason="ok",
                prompt="x" * 8193,
            )

    def test_task_input_required_consent_url_too_long(self):
        """consent_url is capped at 2048 chars."""
        with pytest.raises(ValidationError):
            TaskInputRequiredBody(
                task_id="t-1",
                reason="ok",
                prompt="ok",
                consent_url="https://example.com/" + "x" * 2048,
            )

    def test_task_escalate_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskEscalateBody(
                task_id="x" * 257,
                escalate_to="sender_human",
                reason="ok",
            )
        with pytest.raises(ValidationError):
            TaskEscalateBody(
                task_id="t-1",
                escalate_to="sender_human",
                reason="x" * 8193,
            )

    def test_task_reroute_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskRerouteBody(
                task_id="t-1",
                action="cancel",
                reason="x" * 8193,
            )

    def test_task_transfer_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskTransferBody(
                task_id="t-1",
                transfer_to="x" * 257,
                reason="ok",
            )

    def test_task_acknowledge_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskAcknowledgeBody(task_id="x" * 257)

    def test_task_reject_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskRejectBody(task_id="x" * 257, reason="ok")
        with pytest.raises(ValidationError):
            TaskRejectBody(task_id="t-1", reason="x" * 8193)

    def test_task_complete_task_id_too_long(self):
        with pytest.raises(ValidationError):
            TaskCompleteBody(task_id="x" * 257, result="ok")

    def test_task_error_fields_too_long(self):
        with pytest.raises(ValidationError):
            TaskErrorBody(
                task_id="x" * 257,
                reason="ok",
                retry_eligible=False,
            )
        with pytest.raises(ValidationError):
            TaskErrorBody(
                task_id="t-1",
                reason="x" * 8193,
                retry_eligible=False,
            )

    def test_task_response_text_too_long(self):
        with pytest.raises(ValidationError):
            TaskResponseBody(text="x" * 65537)

    def test_data_consent_request_fields_too_long(self):
        with pytest.raises(ValidationError):
            DataConsentRequestBody(
                requester="x" * 257,
                target="@bob",
                scopes=["read"],
                reason="ok",
            )

    def test_data_consent_response_fields_too_long(self):
        with pytest.raises(ValidationError):
            DataConsentResponseBody(
                requester="x" * 257,
                target="@bob",
                approved=True,
            )


# ---------------------------------------------------------------------------
# Numeric bounds enforcement
# ---------------------------------------------------------------------------


class TestNumericBounds:
    """Numeric fields must enforce ge/le constraints."""

    def test_timeout_negative(self):
        with pytest.raises(ValidationError):
            TaskCreateBody(description="test", timeout_seconds=-1)

    def test_timeout_exceeds_max(self):
        with pytest.raises(ValidationError):
            TaskCreateBody(description="test", timeout_seconds=86401)

    def test_timeout_at_zero(self):
        body = TaskCreateBody(description="test", timeout_seconds=0)
        assert body.timeout_seconds == 0

    def test_timeout_at_max(self):
        body = TaskCreateBody(description="test", timeout_seconds=86400)
        assert body.timeout_seconds == 86400

    def test_estimated_cost_negative(self):
        with pytest.raises(ValidationError):
            TaskQuoteBody(
                task_id="t-1",
                expires_at="2026-01-01T00:00:00Z",
                estimated_cost_usd=-1.0,
            )

    def test_estimated_tokens_negative(self):
        with pytest.raises(ValidationError):
            TaskQuoteBody(
                task_id="t-1",
                expires_at="2026-01-01T00:00:00Z",
                estimated_tokens=-1,
            )

    def test_estimated_duration_negative(self):
        with pytest.raises(ValidationError):
            TaskQuoteBody(
                task_id="t-1",
                expires_at="2026-01-01T00:00:00Z",
                estimated_duration_seconds=-1,
            )

    def test_estimated_duration_exceeds_max(self):
        with pytest.raises(ValidationError):
            TaskQuoteBody(
                task_id="t-1",
                expires_at="2026-01-01T00:00:00Z",
                estimated_duration_seconds=86401,
            )

    def test_progress_estimated_remaining_negative(self):
        with pytest.raises(ValidationError):
            TaskProgressBody(task_id="t-1", estimated_remaining_seconds=-1)

    def test_progress_estimated_remaining_exceeds_max(self):
        with pytest.raises(ValidationError):
            TaskProgressBody(task_id="t-1", estimated_remaining_seconds=86401)

    def test_input_required_timeout_negative(self):
        with pytest.raises(ValidationError):
            TaskInputRequiredBody(
                task_id="t-1",
                reason="ok",
                prompt="ok",
                timeout_seconds=-1,
            )

    def test_acknowledge_duration_negative(self):
        with pytest.raises(ValidationError):
            TaskAcknowledgeBody(task_id="t-1", estimated_duration_seconds=-1)

    def test_acknowledge_duration_exceeds_max(self):
        with pytest.raises(ValidationError):
            TaskAcknowledgeBody(task_id="t-1", estimated_duration_seconds=86401)

    def test_reject_retry_after_negative(self):
        with pytest.raises(ValidationError):
            TaskRejectBody(
                task_id="t-1",
                reason="no",
                retry_after_seconds=-1,
            )

    def test_reject_retry_after_exceeds_max(self):
        with pytest.raises(ValidationError):
            TaskRejectBody(
                task_id="t-1",
                reason="no",
                retry_after_seconds=86401,
            )

    def test_error_retry_after_negative(self):
        with pytest.raises(ValidationError):
            TaskErrorBody(
                reason="err",
                retry_eligible=True,
                retry_after_seconds=-1,
            )

    def test_complete_cost_usd_negative(self):
        with pytest.raises(ValidationError):
            TaskCompleteBody(task_id="t-1", result="ok", cost_usd=-0.01)

    def test_complete_duration_negative(self):
        with pytest.raises(ValidationError):
            TaskCompleteBody(task_id="t-1", result="ok", duration_seconds=-1.0)

    def test_consent_request_ttl_negative(self):
        with pytest.raises(ValidationError):
            DataConsentRequestBody(
                requester="@alice",
                target="@bob",
                scopes=["read"],
                reason="ok",
                ttl_seconds=-1,
            )

    def test_consent_request_ttl_exceeds_max(self):
        with pytest.raises(ValidationError):
            DataConsentRequestBody(
                requester="@alice",
                target="@bob",
                scopes=["read"],
                reason="ok",
                ttl_seconds=604801,
            )


# ---------------------------------------------------------------------------
# List max_length enforcement
# ---------------------------------------------------------------------------


class TestListMaxLength:
    """List fields must enforce max_length constraints."""

    def test_message_attachments_too_many(self):
        with pytest.raises(ValidationError):
            MessageBody(text="hi", attachments=[{"f": i} for i in range(51)])

    def test_task_create_tools_required_too_many(self):
        with pytest.raises(ValidationError):
            TaskCreateBody(
                description="test",
                tools_required=["t"] * 51,
            )

    def test_task_delegate_chain_too_long(self):
        with pytest.raises(ValidationError):
            TaskDelegateBody(
                task_id="t-1",
                description="ok",
                delegation_chain=[{"a": i} for i in range(51)],
            )

    def test_task_input_required_options_too_many(self):
        with pytest.raises(ValidationError):
            TaskInputRequiredBody(
                task_id="t-1",
                reason="ok",
                prompt="ok",
                options=["o"] * 51,
            )

    def test_consent_request_scopes_too_many(self):
        with pytest.raises(ValidationError):
            DataConsentRequestBody(
                requester="@alice",
                target="@bob",
                scopes=["s"] * 51,
                reason="ok",
            )

    def test_consent_response_scopes_too_many(self):
        with pytest.raises(ValidationError):
            DataConsentResponseBody(
                requester="@alice",
                target="@bob",
                scopes=["s"] * 51,
                approved=True,
            )


# ---------------------------------------------------------------------------
# Valid values must be accepted
# ---------------------------------------------------------------------------


class TestValidValues:
    """Confirm that valid values within bounds are accepted."""

    def test_task_create_valid(self):
        body = TaskCreateBody(
            description="Find me a hotel in London",
            task_id="task-abc-123",
            timeout_seconds=3600,
        )
        assert body.description == "Find me a hotel in London"
        assert body.timeout_seconds == 3600

    def test_task_quote_valid(self):
        body = TaskQuoteBody(
            task_id="t-1",
            expires_at="2026-01-01T00:00:00Z",
            estimated_cost_usd=1.50,
            estimated_tokens=100,
            estimated_duration_seconds=60,
        )
        assert body.estimated_cost_usd == 1.50

    def test_consent_request_valid(self):
        body = DataConsentRequestBody(
            requester="@alice",
            target="@bob",
            scopes=["read", "write"],
            reason="Need access to documents",
            ttl_seconds=86400,
        )
        assert body.ttl_seconds == 86400

    def test_message_with_attachments(self):
        body = MessageBody(
            text="hello",
            attachments=[{"type": "file", "url": "https://example.com/f.pdf"}],
        )
        assert len(body.attachments) == 1

    def test_task_progress_valid(self):
        body = TaskProgressBody(
            task_id="t-1",
            percentage=50,
            message="Half done",
            estimated_remaining_seconds=300,
        )
        assert body.percentage == 50
