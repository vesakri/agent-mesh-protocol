"""Tests for jurisdiction cryptographic binding (Task 1.6).

Ensures jurisdiction comes from the agent's signed agent.json
descriptor, not from untrusted per-message headers.
"""

from __future__ import annotations

from ampro.compliance.jurisdiction import (
    JurisdictionInfo,
    check_jurisdiction_conflict,
    validate_jurisdiction_source,
)
from ampro.core.envelope import AgentMessage


def _make_msg(**header_overrides: str) -> AgentMessage:
    """Helper: build an AgentMessage with optional header overrides."""
    headers = {"Jurisdiction": "XX", **header_overrides}
    return AgentMessage(
        sender="@alice",
        recipient="@bob",
        body="hello",
        headers=headers,
    )


# -----------------------------------------------------------------------
# validate_jurisdiction_source
# -----------------------------------------------------------------------


class TestValidateJurisdictionSource:
    """validate_jurisdiction_source trusts agent.json, ignores headers."""

    def test_agent_json_with_jurisdiction_returns_value(self) -> None:
        msg = _make_msg(Jurisdiction="US")
        result = validate_jurisdiction_source(msg, agent_json={"jurisdiction": "DE"})
        assert result == "DE"

    def test_agent_json_without_jurisdiction_returns_none(self) -> None:
        msg = _make_msg(Jurisdiction="US")
        result = validate_jurisdiction_source(msg, agent_json={"name": "bot"})
        assert result is None

    def test_no_agent_json_returns_none(self) -> None:
        msg = _make_msg(Jurisdiction="EU")
        result = validate_jurisdiction_source(msg, agent_json=None)
        assert result is None

    def test_ignores_message_header_jurisdiction(self) -> None:
        """The Jurisdiction header in the message MUST be ignored."""
        msg = _make_msg(Jurisdiction="CN")
        # No agent_json → should return None, NOT "CN" from the header
        result = validate_jurisdiction_source(msg)
        assert result is None

    def test_agent_json_jurisdiction_overrides_header(self) -> None:
        """agent.json is authoritative even if the header says something else."""
        msg = _make_msg(Jurisdiction="CN")
        result = validate_jurisdiction_source(msg, agent_json={"jurisdiction": "JP"})
        assert result == "JP"


# -----------------------------------------------------------------------
# check_jurisdiction_conflict with trusted_jurisdiction
# -----------------------------------------------------------------------


class TestCheckJurisdictionConflictTrusted:
    """check_jurisdiction_conflict respects trusted_jurisdiction override."""

    def test_trusted_jurisdiction_overrides_sender_primary(self) -> None:
        sender = JurisdictionInfo(primary="US", frameworks=["CCPA"])
        receiver = JurisdictionInfo(primary="DE", frameworks=["GDPR"])

        # Without trusted: US vs DE with mismatched frameworks → conflict
        has_conflict, _ = check_jurisdiction_conflict(sender, receiver)
        assert has_conflict

        # With trusted_jurisdiction="DE" → same primary → no conflict
        has_conflict, _ = check_jurisdiction_conflict(
            sender, receiver, trusted_jurisdiction="DE"
        )
        assert not has_conflict

    def test_trusted_jurisdiction_none_falls_back_to_sender(self) -> None:
        sender = JurisdictionInfo(primary="US", frameworks=["CCPA"])
        receiver = JurisdictionInfo(primary="DE", frameworks=["GDPR"])

        # trusted_jurisdiction=None → falls back to sender.primary
        has_conflict, detail = check_jurisdiction_conflict(
            sender, receiver, trusted_jurisdiction=None
        )
        assert has_conflict
        assert "US" in (detail or "")

    def test_trusted_jurisdiction_invalid_code_fails_closed(self) -> None:
        sender = JurisdictionInfo(primary="US", frameworks=[])
        receiver = JurisdictionInfo(primary="DE", frameworks=[])

        has_conflict, detail = check_jurisdiction_conflict(
            sender, receiver, trusted_jurisdiction="bad"
        )
        assert has_conflict
        assert "Invalid sender jurisdiction code" in (detail or "")

    def test_trusted_jurisdiction_same_as_receiver_no_conflict(self) -> None:
        sender = JurisdictionInfo(primary="XX", frameworks=["GDPR"])
        receiver = JurisdictionInfo(primary="DE", frameworks=["GDPR"])

        has_conflict, _ = check_jurisdiction_conflict(
            sender, receiver, trusted_jurisdiction="DE"
        )
        assert not has_conflict
