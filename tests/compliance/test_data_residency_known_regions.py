"""Tests for KNOWN_REGIONS allowlist warning in data_residency (#26)."""

from __future__ import annotations

import logging

import pytest

from ampro.compliance.data_residency import (
    KNOWN_REGIONS,
    validate_residency_region,
)


class TestKnownRegionsAllowlist:
    @pytest.mark.parametrize(
        "region",
        ["us-east-1", "eu-west-1", "ap-south-1", "us-central1", "eastus"],
    )
    def test_known_region_no_warning(
        self, region: str, caplog: pytest.LogCaptureFixture
    ):
        """Known region codes validate cleanly with no warning."""
        assert region in KNOWN_REGIONS
        with caplog.at_level(logging.WARNING, logger="ampro.compliance.data_residency"):
            assert validate_residency_region(region) is True
        assert not any(
            "KNOWN_REGIONS" in r.message for r in caplog.records
        )

    def test_validate_region_logs_warning_on_unknown(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Unknown but shape-valid region logs WARNING and still passes."""
        # "zz-typo-1" is shape-valid but not a real provider region.
        with caplog.at_level(
            logging.WARNING, logger="ampro.compliance.data_residency"
        ):
            result = validate_residency_region("zz-typo-1")
        assert result is True
        assert any(
            "KNOWN_REGIONS" in r.message for r in caplog.records
        ), f"Expected WARNING about KNOWN_REGIONS, got records: {caplog.records}"

    def test_malformed_region_still_rejected(self):
        """Format violations still return False (no warning path)."""
        assert validate_residency_region("EU_WEST") is False
        assert validate_residency_region("") is False
        assert validate_residency_region("a") is False
