"""Tests for ampro.jurisdiction — v0.1.6 cross-border jurisdiction."""

import pytest

from ampro.compliance.jurisdiction import (
    JurisdictionInfo,
    check_jurisdiction_conflict,
    validate_jurisdiction_code,
)
from ampro.core.envelope import STANDARD_HEADERS


class TestJurisdictionInfoCreation:
    def test_jurisdiction_info_creation(self):
        """JurisdictionInfo stores primary, additional, and frameworks."""
        info = JurisdictionInfo(
            primary="DE",
            additional=["FR", "IT"],
            frameworks=["GDPR"],
        )
        assert info.primary == "DE"
        assert info.additional == ["FR", "IT"]
        assert info.frameworks == ["GDPR"]

    def test_defaults(self):
        """additional and frameworks default to empty lists."""
        info = JurisdictionInfo(primary="US")
        assert info.additional == []
        assert info.frameworks == []


class TestValidateJurisdictionCode:
    @pytest.mark.parametrize("code", ["US", "DE", "JP", "BR"])
    def test_validate_code_valid(self, code: str):
        """Valid ISO 3166-1 alpha-2 codes return True."""
        assert validate_jurisdiction_code(code) is True

    @pytest.mark.parametrize("code", ["USA", "us", "1A", ""])
    def test_validate_code_invalid(self, code: str):
        """Invalid codes return False."""
        assert validate_jurisdiction_code(code) is False


class TestJurisdictionConflict:
    def test_no_conflict_same_jurisdiction(self):
        """Same primary jurisdiction — no conflict regardless of frameworks."""
        sender = JurisdictionInfo(primary="DE", frameworks=["GDPR"])
        receiver = JurisdictionInfo(primary="DE", frameworks=[])
        has_conflict, detail = check_jurisdiction_conflict(sender, receiver)
        assert has_conflict is False
        assert detail is None

    def test_conflict_different_frameworks(self):
        """Sender has GDPR, receiver doesn't, different primaries -> conflict."""
        sender = JurisdictionInfo(primary="DE", frameworks=["GDPR"])
        receiver = JurisdictionInfo(primary="US", frameworks=["CCPA"])
        has_conflict, detail = check_jurisdiction_conflict(sender, receiver)
        assert has_conflict is True
        assert detail is not None
        assert "GDPR" in detail

    def test_no_conflict_shared_frameworks(self):
        """Both share GDPR — no conflict even with different primaries."""
        sender = JurisdictionInfo(primary="DE", frameworks=["GDPR"])
        receiver = JurisdictionInfo(primary="FR", frameworks=["GDPR"])
        has_conflict, detail = check_jurisdiction_conflict(sender, receiver)
        assert has_conflict is False
        assert detail is None


class TestJurisdictionHeader:
    def test_jurisdiction_header_in_standard_headers(self):
        """'Jurisdiction' is a registered standard header."""
        assert "Jurisdiction" in STANDARD_HEADERS
