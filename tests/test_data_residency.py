"""Tests for ampro.data_residency — v0.1.6 data residency constraints."""

import pytest

from ampro.compliance.data_residency import (
    DataResidency,
    check_residency_violation,
    validate_residency_region,
)
from ampro.core.envelope import STANDARD_HEADERS


class TestDataResidencyCreation:
    def test_residency_creation(self):
        """DataResidency stores region, strict, and allowed_regions."""
        dr = DataResidency(
            region="eu-west-1",
            strict=True,
            allowed_regions=["eu-central-1", "eu-north-1"],
        )
        assert dr.region == "eu-west-1"
        assert dr.strict is True
        assert dr.allowed_regions == ["eu-central-1", "eu-north-1"]

    def test_defaults(self):
        """strict defaults to True, allowed_regions defaults to empty."""
        dr = DataResidency(region="us-east-1")
        assert dr.strict is True
        assert dr.allowed_regions == []


class TestValidateResidencyRegion:
    @pytest.mark.parametrize("region", ["eu-west-1", "us-east-1", "ap-southeast-1"])
    def test_validate_region_valid(self, region: str):
        """Valid region identifiers return True."""
        assert validate_residency_region(region) is True

    @pytest.mark.parametrize("region", ["EU_WEST", "", "a", "-bad"])
    def test_validate_region_invalid(self, region: str):
        """Invalid region identifiers return False."""
        assert validate_residency_region(region) is False


class TestResidencyViolation:
    def test_violation_strict_mismatch(self):
        """Different regions with strict=True produces a violation."""
        msg_res = DataResidency(region="eu-west-1", strict=True)
        agent_res = DataResidency(region="us-east-1")
        has_violation, detail = check_residency_violation(msg_res, agent_res)
        assert has_violation is True
        assert detail is not None
        assert "eu-west-1" in detail
        assert "us-east-1" in detail

    def test_no_violation_same_region(self):
        """Same region — no violation."""
        msg_res = DataResidency(region="eu-west-1", strict=True)
        agent_res = DataResidency(region="eu-west-1")
        has_violation, detail = check_residency_violation(msg_res, agent_res)
        assert has_violation is False
        assert detail is None

    def test_no_violation_allowed_regions(self):
        """Agent in allowed_regions list — no violation when strict=False."""
        msg_res = DataResidency(
            region="eu-west-1",
            strict=False,
            allowed_regions=["eu-central-1", "us-east-1"],
        )
        agent_res = DataResidency(region="us-east-1")
        has_violation, detail = check_residency_violation(msg_res, agent_res)
        assert has_violation is False
        assert detail is None


class TestDataResidencyHeader:
    def test_data_residency_header(self):
        """'Data-Residency' is a registered standard header."""
        assert "Data-Residency" in STANDARD_HEADERS
