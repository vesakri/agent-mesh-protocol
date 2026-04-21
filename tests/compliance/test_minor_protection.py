"""Tests for check_minor_protection compliance middleware (C9).

Covers: no-op registry default, guardian authorization, minor blocking,
subject extraction from body and headers, and fixture cleanup.
"""
from __future__ import annotations

import pytest

from ampro.compliance.middleware import check_minor_protection, ComplianceCheckResult
from ampro.compliance.registry import (
    NoOpMinorRegistry,
    get_minor_registry,
    set_minor_registry,
)
from ampro.core.envelope import AgentMessage
from tests.compliance.conftest import MockMinorRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _msg(
    sender: str = "@agent-a",
    recipient: str = "@agent-b",
    body: dict | str | None = None,
    headers: dict | None = None,
) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        body=body,
        headers=headers or {},
    )


# ---------------------------------------------------------------------------
# Test 1: No-op registry (default) -> always allowed
# ---------------------------------------------------------------------------

def test_noop_registry_allows_all():
    """With the default NoOpMinorRegistry, every subject passes because
    is_minor() always returns False."""
    reg = get_minor_registry()
    assert isinstance(reg, NoOpMinorRegistry)

    msg = _msg(body={"subject_id": "any-user-123"})
    result = check_minor_protection(msg)
    assert result.allowed is True
    assert result.reason == ""


# ---------------------------------------------------------------------------
# Test 2: Minor with guardian, sender == guardian -> allowed
# ---------------------------------------------------------------------------

def test_minor_with_guardian_sender_is_guardian():
    """If the subject is a minor and the sender is the registered guardian,
    the message is allowed."""
    registry = MockMinorRegistry(minors={"kid-1": "@parent-1"})
    set_minor_registry(registry)

    msg = _msg(sender="@parent-1", body={"subject_id": "kid-1"})
    result = check_minor_protection(msg)
    assert result.allowed is True


# ---------------------------------------------------------------------------
# Test 3: Minor with guardian, sender != guardian -> blocked
# ---------------------------------------------------------------------------

def test_minor_with_guardian_sender_is_not_guardian():
    """If the subject is a minor but the sender is NOT the guardian,
    the message is blocked with reason='minor_protection'."""
    registry = MockMinorRegistry(minors={"kid-1": "@parent-1"})
    set_minor_registry(registry)

    msg = _msg(sender="@stranger", body={"subject_id": "kid-1"})
    result = check_minor_protection(msg)
    assert result.allowed is False
    assert result.reason == "minor_protection"
    assert "kid-1" in result.detail


# ---------------------------------------------------------------------------
# Test 4: Minor with no guardian -> blocked
# ---------------------------------------------------------------------------

def test_minor_with_no_guardian_blocked():
    """If the subject is a minor but has no guardian on record,
    the message is blocked regardless of sender."""
    registry = MockMinorRegistry(minors={"kid-2": None})
    set_minor_registry(registry)

    msg = _msg(sender="@anyone", body={"subject_id": "kid-2"})
    result = check_minor_protection(msg)
    assert result.allowed is False
    assert result.reason == "minor_protection"


# ---------------------------------------------------------------------------
# Test 5: Adult subject -> allowed
# ---------------------------------------------------------------------------

def test_adult_subject_allowed():
    """If the subject is NOT a minor (is_minor returns False), the message
    is allowed even with a real registry configured."""
    registry = MockMinorRegistry(minors={"kid-1": "@parent-1"})
    set_minor_registry(registry)

    msg = _msg(body={"subject_id": "adult-user"})
    result = check_minor_protection(msg)
    assert result.allowed is True


# ---------------------------------------------------------------------------
# Test 6: No subject in message -> allowed
# ---------------------------------------------------------------------------

def test_no_subject_in_message_allowed():
    """If the message has no subject_id in body or headers, there is nothing
    to protect and the check passes."""
    registry = MockMinorRegistry(minors={"kid-1": "@parent-1"})
    set_minor_registry(registry)

    # No subject_id in body or headers
    msg = _msg(body={"some_other_field": "value"})
    result = check_minor_protection(msg)
    assert result.allowed is True

    # Body is a string (not dict)
    msg2 = _msg(body="hello world")
    result2 = check_minor_protection(msg2)
    assert result2.allowed is True

    # Body is None, no headers
    msg3 = _msg(body=None)
    result3 = check_minor_protection(msg3)
    assert result3.allowed is True


# ---------------------------------------------------------------------------
# Test 7: Subject extracted from headers when body has no subject_id
# ---------------------------------------------------------------------------

def test_subject_from_header():
    """Subject-Id in headers is used as fallback when body has no subject_id."""
    registry = MockMinorRegistry(minors={"kid-h": "@guardian-h"})
    set_minor_registry(registry)

    # Body is not a dict, but header has Subject-Id
    msg = _msg(
        sender="@guardian-h",
        body="plain text body",
        headers={"Subject-Id": "kid-h"},
    )
    result = check_minor_protection(msg)
    assert result.allowed is True

    # Same but sender is NOT the guardian -> blocked
    msg2 = _msg(
        sender="@other",
        body=None,
        headers={"Subject-Id": "kid-h"},
    )
    result2 = check_minor_protection(msg2)
    assert result2.allowed is False
    assert result2.reason == "minor_protection"


# ---------------------------------------------------------------------------
# Test 8 (bonus): Registry reset restores no-op behavior
# ---------------------------------------------------------------------------

def test_registry_reset_restores_noop():
    """After setting a real registry and then resetting to NoOp, the default
    no-op behavior is restored (is_minor=False for everyone).
    The autouse fixture does this, but this test verifies it explicitly."""
    registry = MockMinorRegistry(minors={"kid-1": "@parent-1"})
    set_minor_registry(registry)

    # Confirm minor is detected
    msg = _msg(sender="@stranger", body={"subject_id": "kid-1"})
    assert check_minor_protection(msg).allowed is False

    # Reset to no-op
    set_minor_registry(NoOpMinorRegistry())

    # Same message now passes because NoOp says not a minor
    assert check_minor_protection(msg).allowed is True
