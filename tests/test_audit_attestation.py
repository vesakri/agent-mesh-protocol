"""Tests for audit attestation body type."""
import pytest
from pydantic import ValidationError


class TestAttestationBody:
    def test_all_fields(self):
        from ampro import AuditAttestationBody

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
        from ampro import AuditAttestationBody

        with pytest.raises(ValidationError):
            AuditAttestationBody(
                audit_id="att-bad",
                # missing agents, events_hash, attestation_signatures, timestamp
            )

    def test_extra_fields_ignored(self):
        from ampro import AuditAttestationBody

        body = AuditAttestationBody(
            audit_id="att-002",
            agents=["agent://a.com", "agent://b.com"],
            events_hash="sha256:0" * 32,
            attestation_signatures={
                "agent://a.com": "sig-a",
                "agent://b.com": "sig-b",
            },
            timestamp="2026-04-09T16:00:00Z",
            extra_field="ignored",
        )
        assert not hasattr(body, "extra_field")


class TestBodyRegistry:
    def test_validate_body(self):
        from ampro import validate_body, AuditAttestationBody

        body = validate_body("audit.attestation", {
            "audit_id": "att-100",
            "agents": ["agent://x.com", "agent://y.com"],
            "events_hash": "sha256:deadbeef",
            "attestation_signatures": {
                "agent://x.com": "sig-x",
                "agent://y.com": "sig-y",
            },
            "timestamp": "2026-04-09T17:00:00Z",
        })
        assert isinstance(body, AuditAttestationBody)
        assert body.audit_id == "att-100"

    def test_validate_body_invalid(self):
        from ampro import validate_body

        with pytest.raises(ValidationError):
            validate_body("audit.attestation", {})


class TestThreeParty:
    def test_three_agents_three_signatures(self):
        from ampro import AuditAttestationBody

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
