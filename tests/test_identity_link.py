"""Tests for identity linking proof body type."""
import json

import pytest
from pydantic import ValidationError


class TestLinkProofCreation:
    def test_all_fields(self):
        from ampro import IdentityLinkProofBody

        body = IdentityLinkProofBody(
            source_id="agent://alice.example.com",
            target_id="agent://alice@registry.example.com",
            proof_type="ed25519_cross_sign",
            proof="base64-signature-data",
            timestamp="2026-04-09T12:00:00Z",
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
                # missing target_id, proof_type, proof, timestamp
            )

    def test_extra_fields_ignored(self):
        from ampro import IdentityLinkProofBody

        body = IdentityLinkProofBody(
            source_id="agent://a.example.com",
            target_id="agent://b.example.com",
            proof_type="ed25519_cross_sign",
            proof="sig",
            timestamp="2026-04-09T12:00:00Z",
            unknown_field="should be ignored",
        )
        assert not hasattr(body, "unknown_field")


class TestLinkProofBodyRegistry:
    def test_validate_body(self):
        from ampro import validate_body, IdentityLinkProofBody

        body = validate_body("identity.link_proof", {
            "source_id": "agent://a.example.com",
            "target_id": "agent://b.example.com",
            "proof_type": "ed25519_cross_sign",
            "proof": "sig-data",
            "timestamp": "2026-04-09T12:00:00Z",
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
        )
        serialized = original.model_dump_json()
        restored = IdentityLinkProofBody.model_validate_json(serialized)
        assert restored.source_id == original.source_id
        assert restored.target_id == original.target_id
        assert restored.proof_type == original.proof_type
        assert restored.proof == original.proof
        assert restored.timestamp == original.timestamp

    def test_dict_round_trip(self):
        from ampro import IdentityLinkProofBody

        original = IdentityLinkProofBody(
            source_id="agent://x.example.com",
            target_id="agent://y.example.com",
            proof_type="hmac_shared_secret",
            proof="hmac-proof",
            timestamp="2026-04-09T15:00:00Z",
        )
        as_dict = original.model_dump()
        restored = IdentityLinkProofBody.model_validate(as_dict)
        assert restored == original
