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

from enum import Enum

from pydantic import BaseModel, Field


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
