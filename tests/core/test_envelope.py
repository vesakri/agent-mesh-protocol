"""Tests for ampro.core.envelope — sender/recipient/header/body validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ampro.core.envelope import AgentMessage


class TestSenderRecipientLimits:
    """Issue #16 — sender/recipient hard max_length=512."""

    def test_sender_length_limit(self):
        oversize = "agent://" + ("a" * 600) + ".example.com"
        with pytest.raises(ValidationError):
            AgentMessage(
                sender=oversize,
                recipient="agent://b.example.com",
            )

    def test_recipient_length_limit(self):
        oversize = "agent://" + ("a" * 600) + ".example.com"
        with pytest.raises(ValidationError):
            AgentMessage(
                sender="agent://a.example.com",
                recipient=oversize,
            )

    def test_sender_at_limit_accepted(self):
        # 512-char sender is accepted.
        at_limit = "a" * 512
        msg = AgentMessage(
            sender=at_limit,
            recipient="agent://b.example.com",
        )
        assert len(msg.sender) == 512


class TestHeaderStringValues:
    """Issue #17 — header values MUST be strings (RFC 7230 §3.2)."""

    def test_headers_reject_non_string_values(self):
        with pytest.raises(ValidationError) as exc:
            AgentMessage(
                sender="agent://a.example.com",
                recipient="agent://b.example.com",
                headers={"Priority": 5},  # int — rejected
            )
        assert "header values must be strings" in str(exc.value)

    def test_headers_reject_bool_values(self):
        with pytest.raises(ValidationError) as exc:
            AgentMessage(
                sender="agent://a.example.com",
                recipient="agent://b.example.com",
                headers={"Authorized": True},
            )
        assert "RFC 7230" in str(exc.value)

    def test_headers_reject_list_values(self):
        with pytest.raises(ValidationError):
            AgentMessage(
                sender="agent://a.example.com",
                recipient="agent://b.example.com",
                headers={"Via": ["agent-1", "agent-2"]},
            )

    def test_headers_accept_string_values(self):
        msg = AgentMessage(
            sender="agent://a.example.com",
            recipient="agent://b.example.com",
            headers={"Priority": "high", "Session-Id": "sess-1"},
        )
        assert msg.headers["Priority"] == "high"


class TestBodyMatchesBodyType:
    """Issue #27 — envelope-level best-effort body/body_type consistency hook.

    The hook dispatches to validate_body when body_type is registered;
    failures are swallowed because server-side request routing is the
    authoritative enforcement point (see ampro.server.core).
    """

    def test_envelope_validates_body_against_body_type(self):
        # Valid task.create body — must construct cleanly.
        msg = AgentMessage(
            sender="agent://a.example.com",
            recipient="agent://b.example.com",
            body_type="task.create",
            body={"description": "Do something"},
        )
        assert msg.body_type == "task.create"
        assert msg.body["description"] == "Do something"

    def test_envelope_accepts_extension_body_type(self):
        # Unknown body_type — validator is a no-op.
        msg = AgentMessage(
            sender="agent://a.example.com",
            recipient="agent://b.example.com",
            body_type="com.acme.custom-event",
            body={"any": "shape"},
        )
        assert msg.body == {"any": "shape"}

    def test_envelope_validator_swallows_mismatched_body(self):
        # Mismatched body for a registered body_type — envelope construction
        # still succeeds (server-side is authoritative).  This proves the
        # hook does not break existing fixtures but is present as a cheap
        # type-consistency stub.
        msg = AgentMessage(
            sender="agent://a.example.com",
            recipient="agent://b.example.com",
            body_type="task.acknowledge",
            body={"task_id": "t-1"},  # partial / schema-incomplete
        )
        assert msg.body_type == "task.acknowledge"
