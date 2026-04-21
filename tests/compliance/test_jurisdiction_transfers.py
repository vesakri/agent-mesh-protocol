"""Tests for cross-border transfer mechanisms and multi-jurisdiction rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ampro.compliance.jurisdiction import (
    AdequacyDecision,
    AdequacyRegistry,
    JurisdictionInfo,
    NoOpAdequacyRegistry,
    TransferDecision,
    TransferMechanism,
    applicable_rules,
    check_cross_border_transfer,
    get_adequacy_registry,
    register_adequacy_registry,
)


class StaticRegistry:
    """Test-only registry backed by an in-memory dict."""

    def __init__(self, entries: dict[tuple[str, str], AdequacyDecision] | None = None):
        self._entries = entries or {}

    def lookup(
        self, from_jurisdiction: str, to_jurisdiction: str
    ) -> AdequacyDecision | None:
        return self._entries.get((from_jurisdiction, to_jurisdiction))


@pytest.fixture(autouse=True)
def _reset_adequacy_registry():
    """Keep the process-wide registry at NoOp between tests."""
    yield
    register_adequacy_registry(NoOpAdequacyRegistry())


def _info(primary: str, additional: list[str] | None = None) -> JurisdictionInfo:
    return JurisdictionInfo(primary=primary, additional=additional or [])


def test_adequacy_decision_respected():
    """A valid, non-expired AdequacyDecision allows the transfer."""
    decision = AdequacyDecision(
        from_jurisdiction="DE",
        to_jurisdiction="US",
        mechanism=TransferMechanism.ADEQUACY,
        expires_at=datetime.now(UTC) + timedelta(days=365),
    )
    registry = StaticRegistry({("DE", "US"): decision})

    result, detail = check_cross_border_transfer(_info("DE"), _info("US"), registry)

    assert result == TransferDecision.ALLOWED
    assert detail is None


def test_expired_adequacy_blocks_transfer():
    """An expired mechanism returns WARNING, not ALLOWED."""
    expired = AdequacyDecision(
        from_jurisdiction="DE",
        to_jurisdiction="US",
        mechanism=TransferMechanism.ADEQUACY,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    registry = StaticRegistry({("DE", "US"): expired})

    result, detail = check_cross_border_transfer(_info("DE"), _info("US"), registry)

    assert result == TransferDecision.WARNING
    assert detail is not None
    assert "expired" in detail


def test_same_jurisdiction_always_allowed():
    """Intra-jurisdiction transfers bypass the adequacy check."""
    result, detail = check_cross_border_transfer(
        _info("DE"), _info("DE"), StaticRegistry({})
    )
    assert result == TransferDecision.ALLOWED
    assert detail is None


def test_no_mechanism_blocks_transfer():
    """The default NoOp registry blocks all cross-border transfers."""
    result, detail = check_cross_border_transfer(
        _info("DE"), _info("US"), NoOpAdequacyRegistry()
    )
    assert result == TransferDecision.BLOCKED
    assert detail is not None
    assert "No adequacy decision" in detail


def test_mechanism_none_blocks_transfer():
    """An explicit TransferMechanism.NONE entry blocks the transfer."""
    decision = AdequacyDecision(
        from_jurisdiction="DE",
        to_jurisdiction="CN",
        mechanism=TransferMechanism.NONE,
    )
    registry = StaticRegistry({("DE", "CN"): decision})

    result, detail = check_cross_border_transfer(_info("DE"), _info("CN"), registry)

    assert result == TransferDecision.BLOCKED
    assert detail is not None


def test_process_wide_registry_is_pluggable():
    """register_adequacy_registry swaps the default lookup."""
    decision = AdequacyDecision(
        from_jurisdiction="DE",
        to_jurisdiction="US",
        mechanism=TransferMechanism.SCC,
    )
    register_adequacy_registry(StaticRegistry({("DE", "US"): decision}))

    assert isinstance(get_adequacy_registry(), AdequacyRegistry)
    result, _ = check_cross_border_transfer(_info("DE"), _info("US"))
    assert result == TransferDecision.ALLOWED


def test_applicable_rules_respects_primary_then_additional():
    """Multi-jurisdiction rule precedence follows the documented hierarchy."""
    info = JurisdictionInfo(primary="DE", additional=["FR", "IT"])

    # Data in primary -> only primary rules apply.
    assert applicable_rules(info, "DE") == ["DE"]

    # Data in an additional jurisdiction -> additional first (strictest), then primary.
    assert applicable_rules(info, "FR") == ["FR", "DE"]
    assert applicable_rules(info, "IT") == ["IT", "DE"]

    # Data in an unknown region -> default to primary.
    assert applicable_rules(info, "JP") == ["DE"]
