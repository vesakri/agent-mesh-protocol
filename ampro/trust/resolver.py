"""
Agent Protocol — Multi-Method Trust Resolver.

Resolves trust tier from Authorization header using:
  1. Same organization → INTERNAL
  2. Bearer JWT with EdDSA + owner scope → OWNER
  3. Bearer JWT with EdDSA → VERIFIED
  4. DID proof → VERIFIED (not yet implemented)
  5. API key in allowlist → VERIFIED
  6. mTLS → VERIFIED
  7. Everything else → EXTERNAL
"""

from __future__ import annotations

import logging

from ampro.identity.auth_methods import AuthMethod, parse_authorization
from ampro.trust.tiers import TrustTier
from ampro.transport.api_key_store import ApiKeyStore

logger = logging.getLogger(__name__)

_api_key_store = ApiKeyStore(max_failures=10, block_seconds=900)


async def resolve_trust_tier(
    authorization: str | None,
    caller_org_id: str | None,
    target_org_id: str | None,
    client_ip: str | None = None,
) -> TrustTier:
    # Intentional: same org_id → INTERNAL trust. This is by design —
    # agents within the same organization skip external auth checks.
    # The org_id values are server-side derived, not user-supplied.
    if caller_org_id and target_org_id and caller_org_id == target_org_id:
        return TrustTier.INTERNAL

    parsed = parse_authorization(authorization)

    if parsed.method == AuthMethod.JWT:
        return await _resolve_jwt(parsed.token, caller_org_id, target_org_id)

    if parsed.method == AuthMethod.DID:
        return await _resolve_did(parsed.token)

    if parsed.method == AuthMethod.API_KEY:
        return _resolve_api_key(parsed.token, client_ip)

    if parsed.method == AuthMethod.MTLS:
        return TrustTier.VERIFIED

    return TrustTier.EXTERNAL


async def _resolve_jwt(token: str, caller_org_id: str | None, target_org_id: str | None) -> TrustTier:
    """Resolve trust from JWT. Requires a runtime-provided jwt_trust_resolver.

    The jwt_trust_resolver module is NOT included in the ampro package
    because it requires platform-specific infrastructure (JWKS fetching,
    configuration). Platforms provide their own implementation.

    Falls back to EXTERNAL if no resolver is available.
    """
    try:
        from ampro.jwt_trust_resolver import resolve_trust_tier_from_jwt  # type: ignore[import-not-found]
        return await resolve_trust_tier_from_jwt(
            authorization=f"Bearer {token}",
            caller_org_id=caller_org_id,
            target_org_id=target_org_id,
        )
    except ImportError:
        # Fail-open: no JWT resolver installed → EXTERNAL (lowest trust).
        # This is acceptable because EXTERNAL triggers all safety checks.
        logger.warning("JWT resolver not available — install a platform-specific jwt_trust_resolver")
        return TrustTier.EXTERNAL
    except Exception as exc:
        # Fail-open: resolution error → EXTERNAL (lowest trust).
        logger.warning("JWT resolution failed: %s", exc)
        return TrustTier.EXTERNAL


async def _resolve_did(token: str) -> TrustTier:
    """
    Resolve trust from a DID auth proof.

    Supports did:key (self-verifying — the key IS the identifier).
    did:web requires external resolution (not yet implemented).
    """
    try:
        import json
        import base64

        # DID proof is a JWT-like structure: base64(header).base64(payload).signature
        parts = token.split(".")
        if len(parts) < 2:
            logger.debug("DID proof has insufficient parts")
            return TrustTier.EXTERNAL

        # Decode payload
        payload_b64 = parts[1]
        if len(payload_b64) > 10000:
            logger.warning("DID proof payload too large (%d bytes)", len(payload_b64))
            return TrustTier.EXTERNAL
        # Add padding
        remainder = len(payload_b64) % 4
        if remainder:
            payload_b64 += "=" * (4 - remainder)
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)

        did = payload.get("did", "")
        if not did:
            logger.debug("DID proof missing 'did' field")
            return TrustTier.EXTERNAL

        # did:key is self-verifying — the public key is embedded in the DID.
        # However, full Ed25519 signature verification over the JWT proof
        # is not yet implemented (requires key material extraction from
        # multicodec-encoded did:key). Fail closed: treat as EXTERNAL.
        if did.startswith("did:key:"):
            logger.warning(
                "DID signature verification not implemented — treating as EXTERNAL: %s",
                did[:40],
            )
            return TrustTier.EXTERNAL

        # did:web requires fetching DID document — not yet implemented
        if did.startswith("did:web:"):
            logger.debug("did:web resolution not yet implemented for %s", did)
            return TrustTier.EXTERNAL

        logger.debug("Unknown DID method: %s", did)
        return TrustTier.EXTERNAL

    except Exception as exc:
        logger.debug("DID resolution failed: %s", exc)
        return TrustTier.EXTERNAL


def _resolve_api_key(key: str, client_ip: str | None = None) -> TrustTier:
    if client_ip and _api_key_store.is_blocked(client_ip):
        logger.warning("API key auth blocked for IP %s (brute force)", client_ip)
        return TrustTier.EXTERNAL

    agent_id = _api_key_store.validate(key)
    if agent_id is not None:
        if client_ip:
            _api_key_store.reset_failures(client_ip)
        return TrustTier.VERIFIED

    if client_ip:
        _api_key_store.record_failure(client_ip)
    return TrustTier.EXTERNAL
