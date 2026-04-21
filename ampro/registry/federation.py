"""
Agent Protocol — Registry Federation.

Inter-registry trust establishment. Two registries negotiate mutual
trust so agents registered in one can be discovered through the other.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

import base64
import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

_TRUST_PROOF_MIN_LENGTH = 64  # Base64-encoded Ed25519 signature minimum


class RegistryFederationRequest(BaseModel):
    """Request to establish federation between two registries."""

    registry_id: str = Field(description="agent:// URI of the requesting registry")
    capabilities: list[str] = Field(
        description="Capabilities offered (resolve, search, presence)",
    )
    trust_proof: str = Field(
        description="Signed proof of registry identity",
        min_length=1,
    )

    model_config = {"extra": "ignore"}

    @field_validator("trust_proof")
    @classmethod
    def validate_trust_proof(cls, v: str) -> str:
        """Validate trust_proof is non-empty and meets minimum length for Ed25519 sig."""
        if not v or not v.strip():
            raise ValueError("trust_proof must be a non-empty string")
        if len(v) < _TRUST_PROOF_MIN_LENGTH:
            raise ValueError(
                f"trust_proof must be at least {_TRUST_PROOF_MIN_LENGTH} characters "
                f"(base64-encoded Ed25519 signature minimum), got {len(v)}"
            )
        return v


class RegistryFederationResponse(BaseModel):
    """Response to a registry federation request."""

    accepted: bool = Field(description="Whether federation was accepted")
    federation_id: str | None = Field(
        default=None,
        description="Unique federation ID (required when accepted)",
    )
    terms: dict[str, Any] = Field(
        default_factory=dict,
        description="Federation terms (rate limits, retention, etc.)",
    )

    model_config = {"extra": "ignore"}


def verify_federation_trust_proof(request: RegistryFederationRequest) -> bool:
    """Verify a federation trust proof.

    v1 implementation: validates format only (non-empty, valid base64).
    Full cryptographic verification requires the federation registry
    resolver, which is deferred to a future release.

    Returns True if the trust_proof passes format validation,
    False for garbage / invalid input.
    """
    proof = request.trust_proof

    # Basic sanity: must be non-empty and meet minimum length
    if not proof or len(proof) < _TRUST_PROOF_MIN_LENGTH:
        return False

    # Strip whitespace that some encoders add
    proof = proof.strip()

    # Validate base64 encoding (standard or URL-safe)
    try:
        # Accept both standard and URL-safe base64
        # Pad if necessary
        padded = proof + "=" * (-len(proof) % 4)
        decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
        if len(decoded) == 0:
            return False
    except Exception:
        logger.warning(
            "Federation trust_proof from registry %s failed base64 validation. "
            "Full cryptographic verification deferred to federation registry resolver.",
            request.registry_id,
        )
        return False

    logger.info(
        "Federation trust_proof from registry %s passed format validation (v1). "
        "Full cryptographic verification deferred to federation registry resolver.",
        request.registry_id,
    )
    return True
