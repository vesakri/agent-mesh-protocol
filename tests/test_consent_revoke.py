"""Tests for ampro.consent_revoke — v0.1.6 consent revocation."""

import pytest
from pydantic import ValidationError

from ampro.compliance.consent_revoke import DataConsentRevokeBody
from ampro.core.body_schemas import validate_body


class TestConsentRevokeBody:
    def test_full_revocation(self):
        """Empty scopes list means full revocation of all scopes."""
        body = DataConsentRevokeBody(
            grant_id="grant-001",
            requester="agent://admin.example.com",
            target="agent://worker.example.com",
            scopes=[],
            reason="User requested full data removal",
        )
        assert body.scopes == []
        assert body.grant_id == "grant-001"

    def test_partial_revocation(self):
        """Subset of scopes for partial revocation."""
        body = DataConsentRevokeBody(
            grant_id="grant-002",
            requester="agent://admin.example.com",
            target="agent://worker.example.com",
            scopes=["read:profile", "write:analytics"],
            reason="Reducing permissions",
        )
        assert body.scopes == ["read:profile", "write:analytics"]
        assert len(body.scopes) == 2

    def test_immediate_revocation(self):
        """effective_at=None means immediate revocation."""
        body = DataConsentRevokeBody(
            grant_id="grant-003",
            requester="agent://admin.example.com",
            target="agent://worker.example.com",
            reason="Immediate termination",
        )
        assert body.effective_at is None

    def test_scheduled_revocation(self):
        """effective_at set means scheduled revocation."""
        body = DataConsentRevokeBody(
            grant_id="grant-004",
            requester="agent://admin.example.com",
            target="agent://worker.example.com",
            reason="Scheduled phase-out",
            effective_at="2026-05-01T00:00:00Z",
        )
        assert body.effective_at == "2026-05-01T00:00:00Z"


class TestConsentRevokeBodyRegistry:
    def test_body_registry(self):
        """validate_body('data.consent_revoke', ...) returns correct type."""
        body = validate_body("data.consent_revoke", {
            "grant_id": "grant-099",
            "requester": "agent://a.example.com",
            "target": "agent://b.example.com",
            "reason": "Policy change",
        })
        assert isinstance(body, DataConsentRevokeBody)
        assert body.grant_id == "grant-099"


class TestConsentRevokeValidation:
    def test_missing_grant_id(self):
        """grant_id is required — omitting it raises ValidationError."""
        with pytest.raises(ValidationError):
            DataConsentRevokeBody(
                requester="agent://admin.example.com",
                target="agent://worker.example.com",
                reason="Missing grant ID",
            )
