"""Tests for key revocation body types and enum."""
import pytest
from pydantic import ValidationError


class TestRevocationReason:
    def test_key_compromise(self):
        from ampro import RevocationReason
        assert RevocationReason.KEY_COMPROMISE == "key_compromise"

    def test_key_rotation(self):
        from ampro import RevocationReason
        assert RevocationReason.KEY_ROTATION == "key_rotation"

    def test_agent_decommissioned(self):
        from ampro import RevocationReason
        assert RevocationReason.AGENT_DECOMMISSIONED == "agent_decommissioned"

    def test_three_values(self):
        from ampro import RevocationReason
        assert len(RevocationReason) == 3


class TestKeyRevocationBody:
    def test_all_required_fields(self):
        from ampro import KeyRevocationBody
        body = KeyRevocationBody(
            agent_id="agent://compromised.example.com",
            revoked_key_id="key-abc-123",
            revoked_at="2026-04-09T12:00:00Z",
            reason="key_compromise",
            signature="sig-ed25519-proof",
        )
        assert body.agent_id == "agent://compromised.example.com"
        assert body.revoked_key_id == "key-abc-123"
        assert body.revoked_at == "2026-04-09T12:00:00Z"
        assert body.reason == "key_compromise"
        assert body.signature == "sig-ed25519-proof"

    def test_optional_replacement_key_id_default(self):
        from ampro import KeyRevocationBody
        body = KeyRevocationBody(
            agent_id="agent://a.example.com",
            revoked_key_id="k1",
            revoked_at="2026-01-01T00:00:00Z",
            reason="key_rotation",
            signature="sig",
        )
        assert body.replacement_key_id is None

    def test_optional_replacement_key_id_set(self):
        from ampro import KeyRevocationBody
        body = KeyRevocationBody(
            agent_id="agent://a.example.com",
            revoked_key_id="k1",
            revoked_at="2026-01-01T00:00:00Z",
            reason="key_rotation",
            replacement_key_id="k2",
            signature="sig",
        )
        assert body.replacement_key_id == "k2"

    def test_optional_jwks_url_default(self):
        from ampro import KeyRevocationBody
        body = KeyRevocationBody(
            agent_id="agent://a.example.com",
            revoked_key_id="k1",
            revoked_at="2026-01-01T00:00:00Z",
            reason="agent_decommissioned",
            signature="sig",
        )
        assert body.jwks_url is None

    def test_optional_jwks_url_set(self):
        from ampro import KeyRevocationBody
        body = KeyRevocationBody(
            agent_id="agent://a.example.com",
            revoked_key_id="k1",
            revoked_at="2026-01-01T00:00:00Z",
            reason="key_rotation",
            jwks_url="https://a.example.com/.well-known/jwks.json",
            signature="sig",
        )
        assert body.jwks_url == "https://a.example.com/.well-known/jwks.json"

    def test_all_optional_fields_set(self):
        from ampro import KeyRevocationBody
        body = KeyRevocationBody(
            agent_id="agent://a.example.com",
            revoked_key_id="k1",
            revoked_at="2026-04-09T12:00:00Z",
            reason="key_rotation",
            replacement_key_id="k2",
            jwks_url="https://a.example.com/.well-known/jwks.json",
            signature="sig-proof",
        )
        assert body.replacement_key_id == "k2"
        assert body.jwks_url == "https://a.example.com/.well-known/jwks.json"

    def test_missing_required_field_raises(self):
        from ampro import KeyRevocationBody
        with pytest.raises(ValidationError):
            KeyRevocationBody(
                agent_id="agent://a.example.com",
                # missing revoked_key_id, revoked_at, reason, signature
            )


class TestKeyRevocationRegistry:
    def test_validate_body_key_revocation(self):
        from ampro import KeyRevocationBody, validate_body
        body = validate_body("key.revocation", {
            "agent_id": "agent://a.example.com",
            "revoked_key_id": "k1",
            "revoked_at": "2026-04-09T12:00:00Z",
            "reason": "key_compromise",
            "signature": "sig-123",
        })
        assert isinstance(body, KeyRevocationBody)
        assert body.agent_id == "agent://a.example.com"

    def test_validate_body_key_revocation_with_optionals(self):
        from ampro import KeyRevocationBody, validate_body
        body = validate_body("key.revocation", {
            "agent_id": "agent://a.example.com",
            "revoked_key_id": "k1",
            "revoked_at": "2026-04-09T12:00:00Z",
            "reason": "key_rotation",
            "replacement_key_id": "k2",
            "jwks_url": "https://a.example.com/jwks",
            "signature": "sig",
        })
        assert isinstance(body, KeyRevocationBody)
        assert body.replacement_key_id == "k2"
        assert body.jwks_url == "https://a.example.com/jwks"
