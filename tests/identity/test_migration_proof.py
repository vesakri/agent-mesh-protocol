"""Tests for ampro.identity.migration.validate_migration_proof (#37).

Covers the dual-signed migration proof verifier: both old and new Ed25519
keys must sign ``<header>.<payload>``, and the embedded ``timestamp`` must
be within the global CLOCK_SKEW_SECONDS window.
"""
from __future__ import annotations

import base64
import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ampro.identity.migration import (
    IdentityMigrationBody,
    validate_migration_proof,
)
from ampro.trust.resolver import (
    _PUBLIC_KEY_CACHE,
    _reset_public_key_cache_for_tests,
)

OLD_ID = "agent://alice.old.example.com"
NEW_ID = "agent://alice.new.example.com"


@pytest.fixture(autouse=True)
def _clean_key_cache():
    _reset_public_key_cache_for_tests()
    yield
    _reset_public_key_cache_for_tests()


def _b64url_nopad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _seed_key(agent_id: str) -> Ed25519PrivateKey:
    priv = Ed25519PrivateKey.generate()
    pub_bytes = priv.public_key().public_bytes_raw()
    _PUBLIC_KEY_CACHE[agent_id] = (time.monotonic() + 3600, pub_bytes)
    return priv


def _build_proof(
    old_priv: Ed25519PrivateKey,
    new_priv: Ed25519PrivateKey,
    *,
    timestamp: str | None = None,
    tamper_new_sig: bool = False,
) -> str:
    if timestamp is None:
        timestamp = datetime.now(UTC).isoformat()
    header = _b64url_nopad(json.dumps({"alg": "EdDSA"}).encode())
    payload = _b64url_nopad(
        json.dumps(
            {"old_id": OLD_ID, "new_id": NEW_ID, "timestamp": timestamp}
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    old_sig = _b64url_nopad(old_priv.sign(signing_input))
    if tamper_new_sig:
        # Sign with a different key → forged signature
        forger = Ed25519PrivateKey.generate()
        new_sig = _b64url_nopad(forger.sign(signing_input))
    else:
        new_sig = _b64url_nopad(new_priv.sign(signing_input))
    return f"{header}.{payload}.{old_sig}:{new_sig}"


def test_validate_migration_proof_accepts_valid_dual_signed():
    old_priv = _seed_key(OLD_ID)
    new_priv = _seed_key(NEW_ID)
    proof = _build_proof(old_priv, new_priv)
    body = IdentityMigrationBody(
        old_id=OLD_ID,
        new_id=NEW_ID,
        migration_proof=proof,
        effective_at="2026-04-21T00:00:00Z",
    )
    assert validate_migration_proof(body) is True


def test_validate_migration_proof_rejects_wrong_signature():
    """Forged new-key signature must fail verification."""
    old_priv = _seed_key(OLD_ID)
    new_priv = _seed_key(NEW_ID)
    proof = _build_proof(old_priv, new_priv, tamper_new_sig=True)
    body = IdentityMigrationBody(
        old_id=OLD_ID,
        new_id=NEW_ID,
        migration_proof=proof,
        effective_at="2026-04-21T00:00:00Z",
    )
    assert validate_migration_proof(body) is False


def test_validate_migration_proof_rejects_stale_timestamp():
    """Timestamp outside CLOCK_SKEW_SECONDS window is rejected."""
    old_priv = _seed_key(OLD_ID)
    new_priv = _seed_key(NEW_ID)
    stale = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    proof = _build_proof(old_priv, new_priv, timestamp=stale)
    body = IdentityMigrationBody(
        old_id=OLD_ID,
        new_id=NEW_ID,
        migration_proof=proof,
        effective_at="2026-04-21T00:00:00Z",
    )
    assert validate_migration_proof(body) is False


def test_validate_migration_proof_rejects_malformed_proof():
    body = IdentityMigrationBody(
        old_id=OLD_ID,
        new_id=NEW_ID,
        migration_proof="not-a-jwt",
        effective_at="2026-04-21T00:00:00Z",
    )
    assert validate_migration_proof(body) is False
