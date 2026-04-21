"""Tests for identity linking proof body type."""
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

_FUTURE_EXPIRES = "2027-04-09T12:00:00Z"


class TestLinkProofCreation:
    def test_all_fields(self):
        from ampro import IdentityLinkProofBody

        body = IdentityLinkProofBody(
            source_id="agent://alice.example.com",
            target_id="agent://alice@registry.example.com",
            proof_type="ed25519_cross_sign",
            proof="base64-signature-data",
            timestamp="2026-04-09T12:00:00Z",
            expires_at=_FUTURE_EXPIRES,
        )
        assert body.source_id == "agent://alice.example.com"
        assert body.target_id == "agent://alice@registry.example.com"
        assert body.proof_type == "ed25519_cross_sign"
        assert body.proof == "base64-signature-data"
        assert body.timestamp == "2026-04-09T12:00:00Z"

    def test_missing_required_raises(self):
        from ampro import IdentityLinkProofBody

        with pytest.raises(ValidationError):
            IdentityLinkProofBody(
                source_id="agent://a.example.com",
                # missing target_id, proof_type, proof, timestamp, expires_at
            )

    def test_extra_fields_ignored(self):
        from ampro import IdentityLinkProofBody

        body = IdentityLinkProofBody(
            source_id="agent://a.example.com",
            target_id="agent://b.example.com",
            proof_type="ed25519_cross_sign",
            proof="sig",
            timestamp="2026-04-09T12:00:00Z",
            expires_at=_FUTURE_EXPIRES,
            unknown_field="should be ignored",
        )
        assert not hasattr(body, "unknown_field")


class TestLinkProofBodyRegistry:
    def test_validate_body(self):
        from ampro import IdentityLinkProofBody, validate_body

        body = validate_body("identity.link_proof", {
            "source_id": "agent://a.example.com",
            "target_id": "agent://b.example.com",
            "proof_type": "ed25519_cross_sign",
            "proof": "sig-data",
            "timestamp": "2026-04-09T12:00:00Z",
            "expires_at": _FUTURE_EXPIRES,
        })
        assert isinstance(body, IdentityLinkProofBody)
        assert body.source_id == "agent://a.example.com"

    def test_validate_body_invalid(self):
        from ampro import validate_body

        with pytest.raises(ValidationError):
            validate_body("identity.link_proof", {})


class TestJsonRoundTrip:
    def test_json_round_trip(self):
        from ampro import IdentityLinkProofBody

        original = IdentityLinkProofBody(
            source_id="agent://alice.example.com",
            target_id="agent://alice@registry.example.com",
            proof_type="ed25519_cross_sign",
            proof="base64-proof-data",
            timestamp="2026-04-09T14:30:00Z",
            expires_at=_FUTURE_EXPIRES,
        )
        serialized = original.model_dump_json()
        restored = IdentityLinkProofBody.model_validate_json(serialized)
        assert restored.source_id == original.source_id
        assert restored.target_id == original.target_id
        assert restored.proof_type == original.proof_type
        assert restored.proof == original.proof
        assert restored.timestamp == original.timestamp
        assert restored.expires_at == original.expires_at

    def test_dict_round_trip(self):
        from ampro import IdentityLinkProofBody

        original = IdentityLinkProofBody(
            source_id="agent://x.example.com",
            target_id="agent://y.example.com",
            proof_type="hmac_shared_secret",
            proof="hmac-proof",
            timestamp="2026-04-09T15:00:00Z",
            expires_at=_FUTURE_EXPIRES,
        )
        as_dict = original.model_dump()
        restored = IdentityLinkProofBody.model_validate(as_dict)
        assert restored == original


class TestLinkProofExpiry:
    """Issue #38 — link proofs carry an expires_at and are rejected once expired."""

    def test_link_proof_rejected_after_expires_at(self):
        from ampro.identity.link import IdentityLinkProofBody, is_link_proof_valid

        past_issue = datetime.now(tz=UTC) - timedelta(days=30)
        past_expires = past_issue + timedelta(days=1)
        body = IdentityLinkProofBody(
            source_id="agent://a.example.com",
            target_id="agent://b.example.com",
            proof_type="ed25519_cross_sign",
            proof="sig",
            timestamp=past_issue.isoformat().replace("+00:00", "Z"),
            expires_at=past_expires,
        )
        # Still valid at a time before expiry
        assert is_link_proof_valid(body, now=past_issue) is True
        # Rejected once now > expires_at
        assert is_link_proof_valid(body) is False

    def test_link_proof_cannot_be_minted_already_expired(self):
        from ampro import IdentityLinkProofBody

        issued_at = "2026-04-09T12:00:00Z"
        # expires_at before timestamp → validator rejects
        with pytest.raises(ValidationError):
            IdentityLinkProofBody(
                source_id="agent://a.example.com",
                target_id="agent://b.example.com",
                proof_type="ed25519_cross_sign",
                proof="sig",
                timestamp=issued_at,
                expires_at="2026-04-08T12:00:00Z",
            )
