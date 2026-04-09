"""Tests for trust upgrade body types."""
import pytest
from pydantic import ValidationError


class TestTrustUpgradeRequestBody:
    def test_all_fields(self):
        from ampro import TrustUpgradeRequestBody
        body = TrustUpgradeRequestBody(
            session_id="sess-42",
            current_tier="external",
            required_tier="verified",
            verification_methods=["jwt", "did:web", "oauth2"],
            verification_url="https://auth.example.com/verify",
            reason="This operation requires verified identity",
            timeout_seconds=600,
        )
        assert body.session_id == "sess-42"
        assert body.current_tier == "external"
        assert body.required_tier == "verified"
        assert body.verification_methods == ["jwt", "did:web", "oauth2"]
        assert body.verification_url == "https://auth.example.com/verify"
        assert body.reason == "This operation requires verified identity"
        assert body.timeout_seconds == 600

    def test_default_timeout_seconds(self):
        from ampro import TrustUpgradeRequestBody
        body = TrustUpgradeRequestBody(
            session_id="sess-1",
            current_tier="external",
            required_tier="verified",
            verification_methods=["jwt"],
            reason="Upgrade needed",
        )
        assert body.timeout_seconds == 300

    def test_verification_url_optional(self):
        from ampro import TrustUpgradeRequestBody
        body = TrustUpgradeRequestBody(
            session_id="sess-1",
            current_tier="external",
            required_tier="owner",
            verification_methods=["did:web"],
            reason="Need owner access",
        )
        assert body.verification_url is None

    def test_missing_required_raises(self):
        from ampro import TrustUpgradeRequestBody
        with pytest.raises(ValidationError):
            TrustUpgradeRequestBody(session_id="sess-1")


class TestTrustUpgradeResponseBody:
    def test_all_fields(self):
        from ampro import TrustUpgradeResponseBody
        body = TrustUpgradeResponseBody(
            session_id="sess-42",
            method="jwt",
            proof="eyJhbGciOiJFZDI1NTE5Ii...",
            new_tier="verified",
            new_score=750,
        )
        assert body.session_id == "sess-42"
        assert body.method == "jwt"
        assert body.proof == "eyJhbGciOiJFZDI1NTE5Ii..."
        assert body.new_tier == "verified"
        assert body.new_score == 750

    def test_new_score_optional(self):
        from ampro import TrustUpgradeResponseBody
        body = TrustUpgradeResponseBody(
            session_id="sess-1",
            method="did:web",
            proof="did-proof-xyz",
            new_tier="verified",
        )
        assert body.new_score is None

    def test_missing_required_raises(self):
        from ampro import TrustUpgradeResponseBody
        with pytest.raises(ValidationError):
            TrustUpgradeResponseBody(session_id="sess-1", method="jwt")


class TestTrustUpgradeRegistry:
    def test_validate_body_upgrade_request(self):
        from ampro import validate_body, TrustUpgradeRequestBody
        body = validate_body("trust.upgrade_request", {
            "session_id": "sess-1",
            "current_tier": "external",
            "required_tier": "verified",
            "verification_methods": ["jwt"],
            "reason": "Need verified access",
        })
        assert isinstance(body, TrustUpgradeRequestBody)
        assert body.required_tier == "verified"

    def test_validate_body_upgrade_response(self):
        from ampro import validate_body, TrustUpgradeResponseBody
        body = validate_body("trust.upgrade_response", {
            "session_id": "sess-1",
            "method": "jwt",
            "proof": "token-abc",
            "new_tier": "verified",
            "new_score": 800,
        })
        assert isinstance(body, TrustUpgradeResponseBody)
        assert body.new_score == 800

    def test_validate_body_not_raw_dict(self):
        from ampro import validate_body
        for body_type in ("trust.upgrade_request", "trust.upgrade_response"):
            if body_type == "trust.upgrade_request":
                data = {
                    "session_id": "s", "current_tier": "external",
                    "required_tier": "verified", "verification_methods": ["jwt"],
                    "reason": "test",
                }
            else:
                data = {
                    "session_id": "s", "method": "jwt",
                    "proof": "p", "new_tier": "verified",
                }
            result = validate_body(body_type, data)
            assert not isinstance(result, dict), f"{body_type} should be registered"
