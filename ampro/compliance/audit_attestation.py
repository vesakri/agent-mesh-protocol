"""
Agent Protocol — Audit Attestation.

Signed proof that both parties agree on what happened during a session.
Creates a tamper-proof record without requiring a third-party auditor.

Multi-party verification ensures every listed agent actually signed
the attestation — a single agent cannot forge consensus.

PURE — zero platform-specific imports. Uses pydantic, stdlib, and
cryptography (Ed25519 verification).
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


class AuditAttestationBody(BaseModel):
    """body.type = 'audit.attestation' — mutual session attestation.

    The ``model_validator`` guarantees that the set of agents exactly
    matches the set of signature keys — no missing and no extra
    signatures are allowed.
    """

    audit_id: str = Field(description="Unique attestation identifier")
    agents: list[str] = Field(
        description="agent:// URIs of all participating agents",
    )
    events_hash: str = Field(
        description="SHA-256 hash of all session events",
    )
    attestation_signatures: dict[str, str] = Field(
        description="Agent URI -> base64-encoded Ed25519 signature mapping",
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp of attestation",
    )

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def _check_agent_signature_parity(self) -> AuditAttestationBody:
        """Every agent MUST have a signature and vice-versa."""
        agent_set = set(self.agents)
        sig_set = set(self.attestation_signatures.keys())
        missing = agent_set - sig_set
        extra = sig_set - agent_set
        errors: list[str] = []
        if missing:
            errors.append(f"agents missing signatures: {sorted(missing)}")
        if extra:
            errors.append(f"signatures for non-listed agents: {sorted(extra)}")
        if errors:
            raise ValueError("; ".join(errors))
        return self


def canonical_attestation_payload(body: AuditAttestationBody) -> bytes:
    """Build the canonical byte string that each agent signs.

    Deterministic JSON with sorted keys and compact separators ensures
    every implementation produces identical bytes.
    """
    payload: dict[str, Any] = {
        "agents": sorted(body.agents),
        "audit_id": body.audit_id,
        "events_hash": body.events_hash,
        "timestamp": body.timestamp,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def verify_attestation(
    body: AuditAttestationBody,
    key_resolver: Callable[[str], bytes | None],
) -> bool:
    """Verify that every agent's Ed25519 signature is valid.

    Parameters
    ----------
    body:
        The attestation body whose signatures will be checked.
    key_resolver:
        ``(agent_uri) -> raw_public_key_bytes | None``.
        Returns the 32-byte Ed25519 public key for the given agent URI,
        or ``None`` if the key cannot be resolved.

    Returns
    -------
    bool
        ``True`` only if every agent's signature verifies against
        the canonical payload using the resolved public key.
    """
    import base64

    canonical = canonical_attestation_payload(body)
    for agent_uri in body.agents:
        pub_bytes = key_resolver(agent_uri)
        if pub_bytes is None:
            logger.warning("verify_attestation: no key for %s", agent_uri)
            return False
        sig_b64 = body.attestation_signatures.get(agent_uri)
        if sig_b64 is None:
            # Should never happen after model validation, but be safe
            return False
        try:
            sig_bytes = base64.b64decode(sig_b64)
            pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, canonical)
        except Exception:
            logger.warning("verify_attestation: bad signature for %s", agent_uri)
            return False
    return True
