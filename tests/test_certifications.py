"""Tests for v0.1.9 certifications module."""

import json

import pytest


class TestCertificationLink:
    """CertificationLink — Compliance certification links."""

    def test_certification_link_creation(self):
        from ampro import CertificationLink

        link = CertificationLink(
            standard="SOC2",
            url="https://certs.example.com/soc2-report.pdf",
            verified_by="agent://auditor.example.com",
            expires_at="2027-01-01T00:00:00Z",
        )
        assert link.standard == "SOC2"
        assert link.url == "https://certs.example.com/soc2-report.pdf"
        assert link.verified_by == "agent://auditor.example.com"
        assert link.expires_at == "2027-01-01T00:00:00Z"

    def test_agent_json_certifications_default(self):
        from ampro import AgentJson

        aj = AgentJson(
            protocol_version="0.1.9",
            identifiers=["agent://test.com"],
            endpoint="https://test.com/agent/message",
        )
        assert aj.certifications == []

    def test_agent_json_with_certifications(self):
        from ampro import AgentJson

        aj = AgentJson(
            protocol_version="0.1.9",
            identifiers=["agent://certified.com"],
            endpoint="https://certified.com/agent/message",
            certifications=[
                {
                    "standard": "SOC2",
                    "url": "https://certs.example.com/soc2.pdf",
                    "verified_by": "agent://auditor.com",
                    "expires_at": "2027-06-01T00:00:00Z",
                },
                {
                    "standard": "ISO27001",
                    "url": "https://certs.example.com/iso27001.pdf",
                    "verified_by": "agent://iso-auditor.com",
                    "expires_at": "2027-12-31T00:00:00Z",
                },
            ],
        )
        assert len(aj.certifications) == 2
        assert aj.certifications[0]["standard"] == "SOC2"
        assert aj.certifications[1]["standard"] == "ISO27001"

    def test_json_round_trip(self):
        from ampro import CertificationLink

        link = CertificationLink(
            standard="ISO27001",
            url="https://example.com/iso.pdf",
            verified_by="agent://verifier.com",
            expires_at="2028-06-15T12:00:00Z",
        )
        json_str = link.model_dump_json()
        restored = CertificationLink.model_validate_json(json_str)
        assert restored.standard == link.standard
        assert restored.url == link.url
        assert restored.verified_by == link.verified_by
        assert restored.expires_at == link.expires_at
