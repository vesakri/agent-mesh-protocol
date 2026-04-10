"""Tests for v0.1.9 trust proof module."""

import json

import pytest


class TestTrustProofBody:
    """TrustProofBody — Zero-knowledge trust proofs."""

    def test_trust_proof_creation(self):
        from ampro import TrustProofBody

        body = TrustProofBody(
            agent_id="agent://prover.example.com",
            claim="score_above_500",
            proof_type="zkp",
            proof="zk-proof-data-abc",
            verifier_key_id="key-verifier-1",
        )
        assert body.agent_id == "agent://prover.example.com"
        assert body.claim == "score_above_500"
        assert body.proof_type == "zkp"
        assert body.proof == "zk-proof-data-abc"
        assert body.verifier_key_id == "key-verifier-1"

    def test_body_registry(self):
        from ampro import validate_body, TrustProofBody

        result = validate_body("trust.proof", {
            "agent_id": "agent://a.example.com",
            "claim": "score_above_500",
            "proof_type": "zkp",
            "proof": "proof-data",
            "verifier_key_id": "vk-1",
        })
        assert isinstance(result, TrustProofBody)
        assert result.agent_id == "agent://a.example.com"
        assert result.claim == "score_above_500"

    def test_various_claims(self):
        from ampro import TrustProofBody

        for claim in ("score_above_500", "score_above_800"):
            body = TrustProofBody(
                agent_id="agent://test.example.com",
                claim=claim,
                proof_type="zkp",
                proof="proof",
                verifier_key_id="vk",
            )
            assert body.claim == claim

    def test_json_round_trip(self):
        from ampro import TrustProofBody

        body = TrustProofBody(
            agent_id="agent://roundtrip.example.com",
            claim="score_above_800",
            proof_type="zkp",
            proof="round-trip-proof",
            verifier_key_id="vk-rt",
        )
        json_str = body.model_dump_json()
        restored = TrustProofBody.model_validate_json(json_str)
        assert restored.agent_id == body.agent_id
        assert restored.claim == body.claim
        assert restored.proof_type == body.proof_type
        assert restored.proof == body.proof
        assert restored.verifier_key_id == body.verifier_key_id
