"""
Agent Protocol — Identity Migration.

When an agent moves to a new address, it publishes a migration proof.
The old address serves a moved_to pointer in agent.json so callers
can follow the redirect.

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IdentityMigrationBody(BaseModel):
    """body.type = 'identity.migration' — Announce address migration."""

    old_id: str = Field(description="Previous agent:// URI")
    new_id: str = Field(description="New agent:// URI")
    migration_proof: str = Field(
        description="Signed by both old and new keys",
    )
    effective_at: str = Field(
        description="ISO-8601 timestamp when migration takes effect",
    )

    model_config = {"extra": "ignore"}


def _b64url_decode(data: str) -> bytes:
    """URL-safe base64 decode with forgiving padding."""
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def validate_migration_proof(body: IdentityMigrationBody) -> bool:
    """Verify a migration proof is signed by BOTH the old and new agent keys.

    The ``migration_proof`` field is expected to be a JWS-style triple of
    the form ``header.payload.old_signature:new_signature`` — the payload
    MUST contain ``old_id``, ``new_id``, and ``timestamp`` (ISO-8601).
    BOTH signatures MUST verify under the respective public keys (looked
    up via :func:`ampro.trust.resolver.get_public_key`), and the
    ``timestamp`` MUST be within :data:`CLOCK_SKEW_SECONDS` of now.

    Returns ``True`` only when all checks pass. Any parse error, missing
    key, invalid signature, or timestamp outside the skew window returns
    ``False``.

    The ``get_public_key`` resolver is host-pluggable (see
    :func:`ampro.trust.resolver.register_public_key_resolver`).
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
    except ImportError:
        logger.error(
            "cryptography package not installed — cannot verify migration proof."
        )
        return False

    from ampro.trust.resolver import get_public_key
    from ampro.trust.tiers import CLOCK_SKEW_SECONDS

    parts = body.migration_proof.split(".")
    if len(parts) != 3:
        logger.warning("migration_proof must be header.payload.signature triple")
        return False

    header_b64, payload_b64, sig_combined = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as exc:
        logger.warning("migration_proof payload not decodable: %s", exc)
        return False

    # Consistency: payload must reference the same ids as the body
    if payload.get("old_id") != body.old_id or payload.get("new_id") != body.new_id:
        logger.warning("migration_proof payload id mismatch")
        return False

    # Timestamp freshness check
    ts_raw = payload.get("timestamp")
    if not isinstance(ts_raw, str):
        logger.warning("migration_proof missing 'timestamp' field")
        return False
    try:
        proof_ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        if proof_ts.tzinfo is None:
            proof_ts = proof_ts.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        logger.warning("migration_proof timestamp unparseable: %s", exc)
        return False
    now = datetime.now(timezone.utc)
    if abs((now - proof_ts).total_seconds()) > CLOCK_SKEW_SECONDS:
        logger.warning(
            "migration_proof timestamp outside clock-skew window: %s", ts_raw,
        )
        return False

    # Split the two signatures — "<old_sig_b64>:<new_sig_b64>"
    if ":" not in sig_combined:
        logger.warning(
            "migration_proof signature must be 'old_sig:new_sig' (requires both keys)",
        )
        return False
    old_sig_b64, new_sig_b64 = sig_combined.split(":", 1)

    try:
        old_sig = _b64url_decode(old_sig_b64)
        new_sig = _b64url_decode(new_sig_b64)
    except Exception as exc:
        logger.warning("migration_proof signature decode error: %s", exc)
        return False

    # Resolve both keys via the host-pluggable resolver
    old_pub_bytes = get_public_key(body.old_id)
    if old_pub_bytes is None:
        logger.warning("migration_proof: no public key for old_id %s", body.old_id)
        return False
    new_pub_bytes = get_public_key(body.new_id)
    if new_pub_bytes is None:
        logger.warning("migration_proof: no public key for new_id %s", body.new_id)
        return False

    try:
        Ed25519PublicKey.from_public_bytes(old_pub_bytes).verify(old_sig, signing_input)
        Ed25519PublicKey.from_public_bytes(new_pub_bytes).verify(new_sig, signing_input)
    except Exception as exc:
        logger.warning("migration_proof signature verification failed: %s", exc)
        return False

    return True
