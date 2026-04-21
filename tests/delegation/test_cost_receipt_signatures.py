"""Tests for C10 — Cost receipt signature verification and replay defense.

Verifies that CostReceipt.signature is mandatory, CostReceiptChain.add_receipt
verifies Ed25519 signatures, and replayed nonces are rejected.
"""

from __future__ import annotations

import base64
import json
import secrets
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from ampro.delegation.cost_receipt import (
    CostReceipt,
    CostReceiptChain,
    CostReceiptVerificationError,
)
from ampro.trust.resolver import _PUBLIC_KEY_CACHE, _reset_public_key_cache_for_tests

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_AGENT_ID = "agent://test-signer.example.com"
TEST_AGENT_ID_2 = "agent://other-signer.example.com"


@pytest.fixture(autouse=True)
def _clean_key_cache():
    """Reset the public key cache before and after each test."""
    _reset_public_key_cache_for_tests()
    yield
    _reset_public_key_cache_for_tests()


def _seed_key(agent_id: str) -> Ed25519PrivateKey:
    """Generate an Ed25519 keypair, seed it in the resolver cache, return the private key."""
    private = Ed25519PrivateKey.generate()
    pub_bytes = private.public_key().public_bytes_raw()
    _PUBLIC_KEY_CACHE[agent_id] = (time.time() + 3600, pub_bytes)
    return private


def _sign_receipt(private_key: Ed25519PrivateKey, receipt_canonical: bytes) -> str:
    """Sign canonical bytes, return base64url signature (no padding)."""
    sig = private_key.sign(receipt_canonical)
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def _make_signed_receipt(
    agent_id: str,
    private_key: Ed25519PrivateKey,
    task_id: str = "t-1",
    cost_usd: float = 0.05,
    nonce: str | None = None,
    issued_at: str = "2026-04-10T00:00:00Z",
    **kwargs,
) -> CostReceipt:
    """Build a CostReceipt with a valid signature."""
    if nonce is None:
        nonce = secrets.token_urlsafe(16)

    # Build canonical payload to compute signature
    canonical = json.dumps(
        {
            "agent_id": agent_id,
            "task_id": task_id,
            "cost_usd": cost_usd,
            "currency": kwargs.get("currency", "USD"),
            "issued_at": issued_at,
            "nonce": nonce,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    sig = _sign_receipt(private_key, canonical)

    return CostReceipt(
        agent_id=agent_id,
        task_id=task_id,
        cost_usd=cost_usd,
        nonce=nonce,
        signature=sig,
        issued_at=issued_at,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCostReceiptSignatures:
    """C10: Cost receipt signature verification."""

    def test_1_valid_signature_accepted(self):
        """A properly signed receipt is accepted by CostReceiptChain.add_receipt."""
        pk = _seed_key(TEST_AGENT_ID)
        receipt = _make_signed_receipt(TEST_AGENT_ID, pk)

        chain = CostReceiptChain()
        chain.add_receipt(receipt)

        assert len(chain.receipts) == 1
        assert chain.total_cost_usd_float == pytest.approx(0.05)

    def test_2_tampered_cost_rejected(self):
        """A receipt whose cost_usd was tampered after signing is rejected."""
        pk = _seed_key(TEST_AGENT_ID)
        receipt = _make_signed_receipt(TEST_AGENT_ID, pk, cost_usd=0.05)

        # Tamper: change cost_usd after signing
        tampered = receipt.model_copy(update={"cost_usd": 999.99})

        chain = CostReceiptChain()
        with pytest.raises(CostReceiptVerificationError, match="signature verification failed"):
            chain.add_receipt(tampered)

    def test_3_tampered_agent_id_rejected(self):
        """A receipt whose agent_id was tampered after signing is rejected."""
        pk = _seed_key(TEST_AGENT_ID)
        other_pk = _seed_key(TEST_AGENT_ID_2)
        receipt = _make_signed_receipt(TEST_AGENT_ID, pk)

        # Tamper: change agent_id (public key lookup will find the other key)
        tampered = receipt.model_copy(update={"agent_id": TEST_AGENT_ID_2})

        chain = CostReceiptChain()
        with pytest.raises(CostReceiptVerificationError, match="signature verification failed"):
            chain.add_receipt(tampered)

    def test_4_replay_same_nonce_rejected(self):
        """A nonce that was already consumed in this chain is rejected."""
        pk = _seed_key(TEST_AGENT_ID)
        nonce = secrets.token_urlsafe(16)

        receipt1 = _make_signed_receipt(TEST_AGENT_ID, pk, nonce=nonce, cost_usd=0.01)
        receipt2 = _make_signed_receipt(TEST_AGENT_ID, pk, nonce=nonce, cost_usd=0.02)

        chain = CostReceiptChain()
        chain.add_receipt(receipt1)

        with pytest.raises(CostReceiptVerificationError, match="already consumed"):
            chain.add_receipt(receipt2)

    def test_5_unknown_agent_key_rejected(self):
        """A receipt from an agent with no registered public key is rejected."""
        pk = Ed25519PrivateKey.generate()
        # Deliberately NOT seeding this key in the cache
        receipt = _make_signed_receipt("agent://unknown.example.com", pk)

        chain = CostReceiptChain()
        with pytest.raises(CostReceiptVerificationError, match="no public key"):
            chain.add_receipt(receipt)

    def test_6_corrupt_signature_base64_rejected(self):
        """A receipt with an invalid base64 signature is rejected."""
        pk = _seed_key(TEST_AGENT_ID)
        receipt = _make_signed_receipt(TEST_AGENT_ID, pk)

        # Replace with invalid base64 content
        corrupted = receipt.model_copy(update={"signature": "!!!not-valid-base64!!!"})

        chain = CostReceiptChain()
        with pytest.raises(CostReceiptVerificationError, match="signature"):
            chain.add_receipt(corrupted)

    def test_7_multi_hop_chain_all_verified(self):
        """Multiple receipts from different agents in the same chain all verify."""
        pk1 = _seed_key(TEST_AGENT_ID)
        pk2 = _seed_key(TEST_AGENT_ID_2)

        r1 = _make_signed_receipt(TEST_AGENT_ID, pk1, cost_usd=0.03)
        r2 = _make_signed_receipt(TEST_AGENT_ID_2, pk2, cost_usd=0.07)

        chain = CostReceiptChain()
        chain.add_receipt(r1)
        chain.add_receipt(r2)

        assert len(chain.receipts) == 2
        assert chain.total_cost_usd_float == pytest.approx(0.10)

    def test_8_canonical_for_signing_deterministic(self):
        """canonical_for_signing() produces identical bytes for identical fields."""
        pk = _seed_key(TEST_AGENT_ID)
        nonce = secrets.token_urlsafe(16)

        r1 = _make_signed_receipt(TEST_AGENT_ID, pk, nonce=nonce)
        r2 = _make_signed_receipt(TEST_AGENT_ID, pk, nonce=nonce)

        assert r1.canonical_for_signing() == r2.canonical_for_signing()

    def test_9_signature_field_mandatory(self):
        """CostReceipt construction without signature raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CostReceipt(
                agent_id=TEST_AGENT_ID,
                task_id="t-1",
                cost_usd=0.01,
                nonce=secrets.token_urlsafe(16),
                issued_at="2026-04-10T00:00:00Z",
                # signature deliberately omitted
            )

    def test_10_nonce_field_mandatory(self):
        """CostReceipt construction without nonce raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CostReceipt(
                agent_id=TEST_AGENT_ID,
                task_id="t-1",
                cost_usd=0.01,
                signature="some-sig",
                issued_at="2026-04-10T00:00:00Z",
                # nonce deliberately omitted
            )
