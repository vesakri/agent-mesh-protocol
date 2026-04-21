"""C12: Federation trust_proof verification tests.

Validates that:
1. Empty trust_proof raises ValidationError
2. Too-short trust_proof raises ValidationError
3. Valid-length trust_proof passes field validation
4. verify_federation_trust_proof returns False for garbage input
"""

from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError


# A valid base64 string of 88 chars (decodes to 64 bytes — Ed25519 sig size)
_VALID_B64_PROOF = base64.b64encode(b"A" * 64).decode()  # 88 chars, valid base64


class TestTrustProofFieldValidation:
    """Field-level validation on RegistryFederationRequest.trust_proof."""

    def test_empty_trust_proof_rejected(self):
        """Empty string must be rejected by the field validator."""
        from ampro import RegistryFederationRequest

        with pytest.raises(ValidationError) as exc_info:
            RegistryFederationRequest(
                registry_id="agent://registry.example.com",
                capabilities=["resolve"],
                trust_proof="",
            )
        errors = exc_info.value.errors()
        assert any("trust_proof" in str(e) for e in errors)

    def test_too_short_trust_proof_rejected(self):
        """trust_proof shorter than 64 chars must be rejected."""
        from ampro import RegistryFederationRequest

        short_proof = "a" * 63  # One char below minimum
        with pytest.raises(ValidationError) as exc_info:
            RegistryFederationRequest(
                registry_id="agent://registry.example.com",
                capabilities=["resolve"],
                trust_proof=short_proof,
            )
        errors = exc_info.value.errors()
        assert any("trust_proof" in str(e) for e in errors)

    def test_valid_length_trust_proof_accepted(self):
        """trust_proof of 64+ chars passes field validation."""
        from ampro import RegistryFederationRequest

        req = RegistryFederationRequest(
            registry_id="agent://registry.example.com",
            capabilities=["resolve", "search"],
            trust_proof=_VALID_B64_PROOF,
        )
        assert req.trust_proof == _VALID_B64_PROOF
        assert len(req.trust_proof) >= 64


class TestVerifyFederationTrustProof:
    """Module-level verify_federation_trust_proof() function."""

    def test_garbage_input_returns_false(self):
        """Non-base64 garbage that passes the 64-char minimum
        should still return False from verify_federation_trust_proof."""
        from ampro import RegistryFederationRequest, verify_federation_trust_proof

        # Use a string that is 64+ chars but is NOT valid base64
        # (contains characters outside base64 alphabet)
        garbage_proof = "!" * 64 + "@@##$$%%^^&&**(())"  # 82 chars, not base64
        # We need to bypass the field validator for construction since it
        # only checks length, not base64-ness. The garbage passes length check.
        req = RegistryFederationRequest(
            registry_id="agent://registry.example.com",
            capabilities=["resolve"],
            trust_proof=garbage_proof,
        )

        result = verify_federation_trust_proof(req)
        assert result is False

    def test_valid_base64_proof_returns_true(self):
        """A properly base64-encoded proof of sufficient length returns True."""
        from ampro import RegistryFederationRequest, verify_federation_trust_proof

        req = RegistryFederationRequest(
            registry_id="agent://registry.example.com",
            capabilities=["resolve", "search"],
            trust_proof=_VALID_B64_PROOF,
        )

        result = verify_federation_trust_proof(req)
        assert result is True
