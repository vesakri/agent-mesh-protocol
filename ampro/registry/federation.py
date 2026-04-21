"""
Agent Protocol — Registry Federation.

Inter-registry trust establishment. Two registries negotiate mutual
trust so agents registered in one can be discovered through the other.

Federation sync
---------------

Sync is poll-based; receivers push an incremental delta. Each registry
implementation defines its own change-record shape, so
:class:`RegistryFederationSyncResponseBody.changes` carries opaque dicts
(typically ``{"op": "upsert"|"delete", "agent_uri": "...", ...}``) plus a
``next_cursor`` for paging through large deltas.
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
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

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


# ---------------------------------------------------------------------------
# Issue #39 — Federation revocation
# ---------------------------------------------------------------------------


class RegistryFederationRevokeBody(BaseModel):
    """body.type = 'registry.federation_revoke' — Tear down a federation link."""

    model_config = {"extra": "ignore"}

    revoking_registry: str = Field(..., description="Registry initiating the revoke")
    revoked_registry: str = Field(..., description="Registry being revoked")
    reason: str = Field(..., max_length=1024)
    effective_at: datetime = Field(
        ..., description="UTC; revocation effective from this time"
    )
    signature: str = Field(
        ..., description="Ed25519 signature by revoking_registry's key"
    )


# ---------------------------------------------------------------------------
# Issue #40 — Federation sync protocol
# ---------------------------------------------------------------------------


class RegistryFederationSyncBody(BaseModel):
    """body.type = 'registry.federation_sync' — Request a delta from a peer registry."""

    model_config = {"extra": "ignore"}

    since: datetime = Field(
        ..., description="UTC; return changes after this timestamp"
    )
    registry_id: str
    cursor: str | None = Field(
        default=None,
        description="Opaque pagination cursor from previous sync response",
    )


class RegistryFederationSyncResponseBody(BaseModel):
    """body.type = 'registry.federation_sync_response' — Delta + cursor."""

    model_config = {"extra": "ignore"}

    changes: list[dict] = Field(
        ...,
        max_length=500,
        description=(
            "Opaque change records — each registry defines its own "
            "schema (typically includes an op: insert|update|delete field)."
        ),
    )
    next_cursor: str | None = None
    has_more: bool = False


# ---------------------------------------------------------------------------
# Issue #41 — Federation conflict resolution
# ---------------------------------------------------------------------------

# Coarse ordering of trust tiers — higher index wins.
_TRUST_TIER_ORDER: dict[str, int] = {
    "external": 0,
    "verified": 1,
    "owner": 2,
    "internal": 3,
}


def _tier_rank(value: Any) -> int:
    """Return a comparable integer for a trust-tier value."""
    if value is None:
        return -1
    if isinstance(value, int):
        return value
    return _TRUST_TIER_ORDER.get(str(value).lower(), -1)


def _get_field(record: Any, name: str) -> Any:
    """Read ``name`` from either a dict-like or attribute-based record."""
    if isinstance(record, Mapping):
        return record.get(name)
    return getattr(record, name, None)


def _parse_ts(value: Any) -> datetime | None:
    """Best-effort parse of a datetime or ISO-8601 string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            raw = value.replace("Z", "+00:00") if value.endswith("Z") else value
            return datetime.fromisoformat(raw)
        except ValueError:
            return None
    return None


def resolve_federation_conflict(local_record: Any, remote_record: Any) -> Literal["local", "remote"]:
    """Determine precedence when the same agent_uri exists in two federated registries.

    Returns ``'local'`` if the local record wins; ``'remote'`` otherwise.

    Precedence order:

    1. Higher trust tier wins.
    2. More recent ``last_seen`` wins.
    3. Lexicographic ``agent_uri`` fallback (deterministic tiebreaker).
    """
    local_tier = _tier_rank(_get_field(local_record, "trust_tier"))
    remote_tier = _tier_rank(_get_field(remote_record, "trust_tier"))
    if local_tier != remote_tier:
        return "local" if local_tier > remote_tier else "remote"

    local_seen = _parse_ts(_get_field(local_record, "last_seen"))
    remote_seen = _parse_ts(_get_field(remote_record, "last_seen"))
    if local_seen is not None and remote_seen is not None and local_seen != remote_seen:
        return "local" if local_seen > remote_seen else "remote"
    if local_seen is not None and remote_seen is None:
        return "local"
    if local_seen is None and remote_seen is not None:
        return "remote"

    local_uri = str(_get_field(local_record, "agent_uri") or "")
    remote_uri = str(_get_field(remote_record, "agent_uri") or "")
    # Deterministic lex fallback — local wins iff its URI sorts first.
    return "local" if local_uri <= remote_uri else "remote"


# ---------------------------------------------------------------------------
# Existing trust-proof verification
# ---------------------------------------------------------------------------


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
