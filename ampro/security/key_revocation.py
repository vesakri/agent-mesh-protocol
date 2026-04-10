"""
Agent Protocol — Key Revocation.

Emergency key revocation broadcast. When an agent's private key is
compromised, this body type allows broadcasting the revocation to all
agents that may have cached the old key.

Revocation reasons:
  - key_compromise: key was stolen or leaked
  - key_rotation: routine key rotation (not emergency, but caches should refresh)
  - agent_decommissioned: agent is shutting down permanently

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

import json
import logging
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Revocation reason enum
# ---------------------------------------------------------------------------


class RevocationReason(str, Enum):
    """Reasons an agent key may be revoked."""

    KEY_COMPROMISE = "key_compromise"
    KEY_ROTATION = "key_rotation"
    AGENT_DECOMMISSIONED = "agent_decommissioned"


# ---------------------------------------------------------------------------
# Key revocation body type
# ---------------------------------------------------------------------------


class KeyRevocationBody(BaseModel):
    """body.type = 'key.revocation' — Broadcast that an agent key is revoked."""

    agent_id: str = Field(
        description="agent:// URI of the agent whose key is revoked",
    )
    revoked_key_id: str = Field(
        description="Key ID being revoked",
    )
    revoked_at: str = Field(
        description="ISO-8601 timestamp of revocation",
    )
    reason: str = Field(
        description="Revocation reason (key_compromise, key_rotation, agent_decommissioned)",
    )
    replacement_key_id: str | None = Field(
        default=None,
        description="Replacement key ID, if key was rotated",
    )
    jwks_url: str | None = Field(
        default=None,
        description="URL to fetch updated JWKS",
    )
    signature: str = Field(
        description="Ed25519 signature proving authenticity of this revocation",
    )

    model_config = {"extra": "ignore"}


def validate_revocation_signature(body: KeyRevocationBody, public_key_bytes: bytes) -> bool:
    """Verify the Ed25519 signature over the canonical revocation fields.

    The canonical message is a JSON object with fields sorted alphabetically,
    excluding the ``signature`` field itself.

    Args:
        body: The key revocation body containing the signature to verify.
        public_key_bytes: Raw 32-byte Ed25519 public key of the revoking agent.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        logger.error(
            "cryptography package not installed — cannot verify revocation signature. "
            "Install with: pip install cryptography"
        )
        return False

    # Build canonical message: all fields except 'signature', sorted by key
    canonical = {
        "agent_id": body.agent_id,
        "jwks_url": body.jwks_url,
        "reason": body.reason,
        "replacement_key_id": body.replacement_key_id,
        "revoked_at": body.revoked_at,
        "revoked_key_id": body.revoked_key_id,
    }
    message = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")

    try:
        import base64

        signature_bytes = base64.urlsafe_b64decode(body.signature + "==")
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, message)
        return True
    except Exception as exc:
        logger.warning("Revocation signature verification failed: %s", exc)
        return False
