"""Tests for audit attestation multi-party verification (Task 1.5).

Validates:
- Model validator: agents <-> attestation_signatures parity
- verify_attestation: Ed25519 signature verification for all agents
- Canonical payload determinism
"""
from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from ampro.compliance.audit_attestation import (
    AuditAttestationBody,
    canonical_attestation_payload,
    verify_attestation,
)

# ── Helpers ──────────────────────────────────────────────────────────────

def _generate_keypair() -> tuple[Ed25519PrivateKey, bytes]:
    """Generate an Ed25519 keypair; returns (private_key, public_key_bytes)."""
    private = Ed25519PrivateKey.generate()
    public_bytes = private.public_key().public_bytes_raw()
    return private, public_bytes


def _sign_attestation(
    private_key: Ed25519PrivateKey,
    body_for_signing: AuditAttestationBody,
) -> str:
    """Sign the canonical attestation payload and return base64 signature."""
    # Build a temporary body just to get canonical bytes (signatures don't matter for payload)
    canonical = canonical_attestation_payload(body_for_signing)
    sig = private_key.sign(canonical)
    return base64.b64encode(sig).decode()


def _build_signed_attestation(
    agents: list[str],
    keypairs: dict[str, tuple[Ed25519PrivateKey, bytes]],
    audit_id: str = "att-test",
    events_hash: str = "sha256:abc123",
    timestamp: str = "2026-04-16T12:00:00Z",
) -> AuditAttestationBody:
    """Build a fully signed AuditAttestationBody for the given agents."""
    # We need to create a "template" body first to compute canonical payload,
    # then sign, then create the real body with signatures.
    # The canonical payload does not include signatures, so we can use
    # a dummy signatures dict for the template.
    template = AuditAttestationBody.model_construct(
        audit_id=audit_id,
        agents=agents,
        events_hash=events_hash,
        attestation_signatures={a: "" for a in agents},
        timestamp=timestamp,
    )
    canonical = canonical_attestation_payload(template)
    sigs: dict[str, str] = {}
    for agent_uri in agents:
        priv, _ = keypairs[agent_uri]
        sig = priv.sign(canonical)
        sigs[agent_uri] = base64.b64encode(sig).decode()
    return AuditAttestationBody(
        audit_id=audit_id,
        agents=agents,
        events_hash=events_hash,
        attestation_signatures=sigs,
        timestamp=timestamp,
    )


# ── Model Validator Tests ────────────────────────────────────────────────

class TestAttestationModelValidator:
    """The model_validator MUST enforce agents == signature keys."""

    def test_all_fields(self):
        body = AuditAttestationBody(
            audit_id="att-001",
            agents=[
                "agent://alice.example.com",
                "agent://bob.example.com",
            ],
            events_hash="sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            attestation_signatures={
                "agent://alice.example.com": "sig-alice-base64",
                "agent://bob.example.com": "sig-bob-base64",
            },
            timestamp="2026-04-09T15:00:00Z",
        )
        assert body.audit_id == "att-001"
        assert len(body.agents) == 2
        assert body.agents[0] == "agent://alice.example.com"
        assert body.agents[1] == "agent://bob.example.com"
        assert body.events_hash.startswith("sha256:")
        assert len(body.attestation_signatures) == 2
        assert body.attestation_signatures["agent://alice.example.com"] == "sig-alice-base64"
        assert body.timestamp == "2026-04-09T15:00:00Z"

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            AuditAttestationBody(
                audit_id="att-bad",
                # missing agents, events_hash, attestation_signatures, timestamp
            )

    def test_extra_fields_ignored(self):
        body = AuditAttestationBody(
            audit_id="att-002",
            agents=["agent://a.example.com", "agent://b.example.com"],
            events_hash="sha256:0" * 32,
            attestation_signatures={
                "agent://a.example.com": "sig-a",
                "agent://b.example.com": "sig-b",
            },
            timestamp="2026-04-09T16:00:00Z",
            extra_field="ignored",
        )
        assert not hasattr(body, "extra_field")

    def test_missing_agent_signature_fails(self):
        """An agent without a corresponding signature MUST fail validation."""
        with pytest.raises(ValidationError, match="agents missing signatures"):
            AuditAttestationBody(
                audit_id="att-missing",
                agents=[
                    "agent://alice.example.com",
                    "agent://bob.example.com",
                ],
                events_hash="sha256:abc",
                attestation_signatures={
                    "agent://alice.example.com": "sig-alice",
                    # bob is missing
                },
                timestamp="2026-04-16T12:00:00Z",
            )

    def test_extra_signature_not_in_agents_fails(self):
        """A signature for an agent not in the agents list MUST fail validation."""
        with pytest.raises(ValidationError, match="signatures for non-listed agents"):
            AuditAttestationBody(
                audit_id="att-extra",
                agents=["agent://alice.example.com"],
                events_hash="sha256:abc",
                attestation_signatures={
                    "agent://alice.example.com": "sig-alice",
                    "agent://evil.example.com": "sig-evil",
                },
                timestamp="2026-04-16T12:00:00Z",
            )

    def test_both_missing_and_extra_fails(self):
        """Missing + extra at the same time MUST fail."""
        with pytest.raises(ValidationError):
            AuditAttestationBody(
                audit_id="att-both",
                agents=["agent://alice.example.com", "agent://bob.example.com"],
                events_hash="sha256:abc",
                attestation_signatures={
                    "agent://alice.example.com": "sig-alice",
                    "agent://carol.example.com": "sig-carol",  # carol not in agents, bob missing
                },
                timestamp="2026-04-16T12:00:00Z",
            )

    def test_three_agents_three_signatures(self):
        agents = [
            "agent://alice.example.com",
            "agent://bob.example.com",
            "agent://carol.example.com",
        ]
        signatures = {
            "agent://alice.example.com": "sig-alice",
            "agent://bob.example.com": "sig-bob",
            "agent://carol.example.com": "sig-carol",
        }
        body = AuditAttestationBody(
            audit_id="att-3party",
            agents=agents,
            events_hash="sha256:threeparty",
            attestation_signatures=signatures,
            timestamp="2026-04-09T18:00:00Z",
        )
        assert len(body.agents) == 3
        assert len(body.attestation_signatures) == 3
        for agent in agents:
            assert agent in body.attestation_signatures


# ── Body Registry Tests ──────────────────────────────────────────────────

class TestBodyRegistry:
    def test_validate_body(self):
        from ampro import AuditAttestationBody as AB
        from ampro import validate_body

        body = validate_body("audit.attestation", {
            "audit_id": "att-100",
            "agents": ["agent://x.example.com", "agent://y.example.com"],
            "events_hash": "sha256:deadbeef",
            "attestation_signatures": {
                "agent://x.example.com": "sig-x",
                "agent://y.example.com": "sig-y",
            },
            "timestamp": "2026-04-09T17:00:00Z",
        })
        assert isinstance(body, AB)
        assert body.audit_id == "att-100"

    def test_validate_body_invalid(self):
        from ampro import validate_body

        with pytest.raises(ValidationError):
            validate_body("audit.attestation", {})


# ── Cryptographic Verification Tests ─────────────────────────────────────

class TestVerifyAttestation:
    """Ed25519 signature verification for multi-party attestations."""

    def test_all_valid_signatures_returns_true(self):
        agents = [
            "agent://alice.example.com",
            "agent://bob.example.com",
        ]
        keypairs = {}
        pub_keys: dict[str, bytes] = {}
        for agent_uri in agents:
            priv, pub = _generate_keypair()
            keypairs[agent_uri] = (priv, pub)
            pub_keys[agent_uri] = pub

        body = _build_signed_attestation(agents, keypairs)

        def resolver(uri: str) -> bytes | None:
            return pub_keys.get(uri)

        assert verify_attestation(body, resolver) is True

    def test_three_party_valid(self):
        agents = [
            "agent://alice.example.com",
            "agent://bob.example.com",
            "agent://carol.example.com",
        ]
        keypairs = {}
        pub_keys: dict[str, bytes] = {}
        for agent_uri in agents:
            priv, pub = _generate_keypair()
            keypairs[agent_uri] = (priv, pub)
            pub_keys[agent_uri] = pub

        body = _build_signed_attestation(agents, keypairs)

        def resolver(uri: str) -> bytes | None:
            return pub_keys.get(uri)

        assert verify_attestation(body, resolver) is True

    def test_forged_signature_returns_false(self):
        """One agent's signature is replaced with a different key's signature."""
        agents = [
            "agent://alice.example.com",
            "agent://bob.example.com",
        ]
        keypairs = {}
        pub_keys: dict[str, bytes] = {}
        for agent_uri in agents:
            priv, pub = _generate_keypair()
            keypairs[agent_uri] = (priv, pub)
            pub_keys[agent_uri] = pub

        body = _build_signed_attestation(agents, keypairs)

        # Forge: replace bob's signature with a signature from a different key
        forger_priv, _ = _generate_keypair()
        forged_sig = forger_priv.sign(canonical_attestation_payload(body))
        body_dict = body.model_dump()
        body_dict["attestation_signatures"]["agent://bob.example.com"] = base64.b64encode(forged_sig).decode()
        # Use model_construct to bypass validator (we want to test verify_attestation, not the validator)
        forged_body = AuditAttestationBody.model_construct(**body_dict)

        def resolver(uri: str) -> bytes | None:
            return pub_keys.get(uri)

        assert verify_attestation(forged_body, resolver) is False

    def test_missing_key_returns_false(self):
        """If key_resolver returns None for any agent, verification fails."""
        agents = [
            "agent://alice.example.com",
            "agent://bob.example.com",
        ]
        keypairs = {}
        pub_keys: dict[str, bytes] = {}
        for agent_uri in agents:
            priv, pub = _generate_keypair()
            keypairs[agent_uri] = (priv, pub)
            pub_keys[agent_uri] = pub

        body = _build_signed_attestation(agents, keypairs)

        def resolver(uri: str) -> bytes | None:
            if uri == "agent://bob.example.com":
                return None  # simulate missing key
            return pub_keys.get(uri)

        assert verify_attestation(body, resolver) is False

    def test_canonical_payload_is_deterministic(self):
        """Same fields in different order MUST produce identical canonical bytes."""
        body1 = AuditAttestationBody.model_construct(
            audit_id="att-det",
            agents=["agent://bob.example.com", "agent://alice.example.com"],
            events_hash="sha256:xyz",
            attestation_signatures={
                "agent://alice.example.com": "sig-a",
                "agent://bob.example.com": "sig-b",
            },
            timestamp="2026-04-16T12:00:00Z",
        )
        body2 = AuditAttestationBody.model_construct(
            audit_id="att-det",
            agents=["agent://alice.example.com", "agent://bob.example.com"],
            events_hash="sha256:xyz",
            attestation_signatures={
                "agent://bob.example.com": "sig-b",
                "agent://alice.example.com": "sig-a",
            },
            timestamp="2026-04-16T12:00:00Z",
        )
        assert canonical_attestation_payload(body1) == canonical_attestation_payload(body2)
