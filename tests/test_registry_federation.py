"""Tests for registry federation request and response types."""
import pytest
from pydantic import ValidationError

# A valid trust_proof string: 64+ chars, valid base64
_VALID_TRUST_PROOF = "QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQQ=="


class TestFederationRequest:
    def test_all_fields(self):
        from ampro import RegistryFederationRequest

        req = RegistryFederationRequest(
            registry_id="agent://registry-a.example.com",
            capabilities=["resolve", "search", "presence"],
            trust_proof=_VALID_TRUST_PROOF,
        )
        assert req.registry_id == "agent://registry-a.example.com"
        assert req.capabilities == ["resolve", "search", "presence"]
        assert req.trust_proof == _VALID_TRUST_PROOF

    def test_missing_required_raises(self):
        from ampro import RegistryFederationRequest

        with pytest.raises(ValidationError):
            RegistryFederationRequest(
                registry_id="agent://reg.example.com",
                # missing capabilities, trust_proof
            )

    def test_extra_fields_ignored(self):
        from ampro import RegistryFederationRequest

        req = RegistryFederationRequest(
            registry_id="agent://reg.example.com",
            capabilities=["resolve"],
            trust_proof=_VALID_TRUST_PROOF,
            extra_field="ignored",
        )
        assert not hasattr(req, "extra_field")


class TestFederationResponseAccepted:
    def test_accepted_with_federation_id(self):
        from ampro import RegistryFederationResponse

        resp = RegistryFederationResponse(
            accepted=True,
            federation_id="fed-001",
            terms={"rate_limit_rpm": 100, "retention_days": 30},
        )
        assert resp.accepted is True
        assert resp.federation_id == "fed-001"
        assert resp.terms["rate_limit_rpm"] == 100
        assert resp.terms["retention_days"] == 30

    def test_accepted_terms_default_empty(self):
        from ampro import RegistryFederationResponse

        resp = RegistryFederationResponse(
            accepted=True,
            federation_id="fed-002",
        )
        assert resp.terms == {}


class TestFederationResponseRejected:
    def test_rejected_no_federation_id(self):
        from ampro import RegistryFederationResponse

        resp = RegistryFederationResponse(
            accepted=False,
            federation_id=None,
        )
        assert resp.accepted is False
        assert resp.federation_id is None

    def test_rejected_default_federation_id(self):
        from ampro import RegistryFederationResponse

        resp = RegistryFederationResponse(accepted=False)
        assert resp.federation_id is None

    def test_rejected_with_terms(self):
        from ampro import RegistryFederationResponse

        resp = RegistryFederationResponse(
            accepted=False,
            terms={"reason": "trust requirements not met"},
        )
        assert resp.accepted is False
        assert resp.terms["reason"] == "trust requirements not met"


class TestBodyRegistryRequest:
    def test_validate_body(self):
        from ampro import RegistryFederationRequest, validate_body

        body = validate_body("registry.federation_request", {
            "registry_id": "agent://reg-a.example.com",
            "capabilities": ["resolve", "search"],
            "trust_proof": _VALID_TRUST_PROOF,
        })
        assert isinstance(body, RegistryFederationRequest)
        assert body.registry_id == "agent://reg-a.example.com"

    def test_validate_body_invalid(self):
        from ampro import validate_body

        with pytest.raises(ValidationError):
            validate_body("registry.federation_request", {})


class TestBodyRegistryResponse:
    def test_validate_body(self):
        from ampro import RegistryFederationResponse, validate_body

        body = validate_body("registry.federation_response", {
            "accepted": True,
            "federation_id": "fed-100",
            "terms": {"max_queries_per_day": 10000},
        })
        assert isinstance(body, RegistryFederationResponse)
        assert body.accepted is True
        assert body.federation_id == "fed-100"

    def test_validate_body_rejected(self):
        from ampro import RegistryFederationResponse, validate_body

        body = validate_body("registry.federation_response", {
            "accepted": False,
        })
        assert isinstance(body, RegistryFederationResponse)
        assert body.accepted is False
        assert body.federation_id is None
