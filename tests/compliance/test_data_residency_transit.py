"""Tests for the storage/transit distinction in DataResidency."""

from __future__ import annotations

from ampro.compliance.data_residency import DataResidency, check_residency_violation


def test_transit_region_violation_detected():
    """A transit region outside the allowed set MUST be rejected."""
    message = DataResidency(region="eu-west-1", strict=False, allowed_regions=["eu-central-1"])
    agent = DataResidency(
        region="eu-west-1",
        storage_regions=["eu-west-1"],
        transit_regions=["us-east-1"],  # <- violation
    )

    violation, detail = check_residency_violation(message, agent)

    assert violation is True
    assert detail is not None
    assert "transit" in detail
    assert "us-east-1" in detail


def test_storage_and_transit_both_compliant():
    """When both storage and transit stay within allowed set, no violation."""
    message = DataResidency(region="eu-west-1", strict=False, allowed_regions=["eu-central-1"])
    agent = DataResidency(
        region="eu-west-1",
        storage_regions=["eu-central-1"],
        transit_regions=["eu-west-1", "eu-central-1"],
    )

    violation, detail = check_residency_violation(message, agent)

    assert violation is False
    assert detail is None


def test_legacy_region_field_still_works():
    """Agents using only the legacy ``region`` field keep working."""
    message = DataResidency(region="eu-west-1", strict=True)
    agent = DataResidency(region="eu-west-1")

    violation, detail = check_residency_violation(message, agent)

    assert violation is False
    assert detail is None


def test_strict_storage_violation():
    """Strict mode rejects storage outside the message region."""
    message = DataResidency(region="eu-west-1", strict=True)
    agent = DataResidency(region="us-east-1", storage_regions=["us-east-1"])

    violation, detail = check_residency_violation(message, agent)

    assert violation is True
    assert detail is not None
    assert "strict residency" in detail
