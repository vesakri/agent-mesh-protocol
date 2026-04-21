"""Tests for v0.1.3 Cost Receipt feature.

Updated for C10: signature and nonce are now mandatory fields.
"""

from __future__ import annotations

import base64
import json
import secrets
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from ampro.trust.resolver import _PUBLIC_KEY_CACHE, _reset_public_key_cache_for_tests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_key(agent_id: str) -> Ed25519PrivateKey:
    """Generate a keypair, seed it in the resolver cache, return private key."""
    private = Ed25519PrivateKey.generate()
    pub_bytes = private.public_key().public_bytes_raw()
    _PUBLIC_KEY_CACHE[agent_id] = (time.time() + 3600, pub_bytes)
    return private


def _sign_receipt_fields(
    private_key: Ed25519PrivateKey,
    agent_id: str,
    task_id: str,
    cost_usd: float,
    currency: str,
    issued_at: str,
    nonce: str,
) -> str:
    """Compute Ed25519 signature over canonical receipt fields, return base64url."""
    canonical = json.dumps(
        {
            "agent_id": agent_id,
            "task_id": task_id,
            "cost_usd": cost_usd,
            "currency": currency,
            "issued_at": issued_at,
            "nonce": nonce,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    sig = private_key.sign(canonical)
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


@pytest.fixture(autouse=True)
def _clean_key_cache():
    _reset_public_key_cache_for_tests()
    yield
    _reset_public_key_cache_for_tests()


class TestCostReceipt:
    def test_all_fields(self):
        from ampro import CostReceipt
        nonce = secrets.token_urlsafe(16)
        pk = _seed_key("agent://worker.example.com")
        sig = _sign_receipt_fields(
            pk, "agent://worker.example.com", "t-42", 0.05, "USD",
            "2026-04-09T12:00:00Z", nonce,
        )
        receipt = CostReceipt(
            agent_id="agent://worker.example.com",
            task_id="t-42",
            cost_usd=0.05,
            currency="USD",
            breakdown={"llm": 0.04, "tools": 0.01},
            token_usage={"input": 1000, "output": 500},
            duration_seconds=2.5,
            nonce=nonce,
            signature=sig,
            issued_at="2026-04-09T12:00:00Z",
        )
        assert receipt.agent_id == "agent://worker.example.com"
        assert receipt.task_id == "t-42"
        assert receipt.cost_usd == 0.05
        assert receipt.currency == "USD"
        assert receipt.breakdown == {"llm": 0.04, "tools": 0.01}
        assert receipt.token_usage == {"input": 1000, "output": 500}
        assert receipt.duration_seconds == 2.5
        assert receipt.signature == sig
        assert receipt.nonce == nonce
        assert receipt.issued_at == "2026-04-09T12:00:00Z"

    def test_optional_fields_default_none(self):
        from ampro import CostReceipt
        nonce = secrets.token_urlsafe(16)
        pk = _seed_key("agent://a.example.com")
        sig = _sign_receipt_fields(
            pk, "agent://a.example.com", "t-1", 0.01, "USD",
            "2026-04-09T00:00:00Z", nonce,
        )
        receipt = CostReceipt(
            agent_id="agent://a.example.com",
            task_id="t-1",
            cost_usd=0.01,
            nonce=nonce,
            signature=sig,
            issued_at="2026-04-09T00:00:00Z",
        )
        assert receipt.breakdown is None
        assert receipt.token_usage is None
        assert receipt.duration_seconds is None

    def test_currency_defaults_to_usd(self):
        from ampro import CostReceipt
        nonce = secrets.token_urlsafe(16)
        pk = _seed_key("agent://a.example.com")
        sig = _sign_receipt_fields(
            pk, "agent://a.example.com", "t-1", 1.00, "USD",
            "2026-04-09T00:00:00Z", nonce,
        )
        receipt = CostReceipt(
            agent_id="agent://a.example.com",
            task_id="t-1",
            cost_usd=1.00,
            nonce=nonce,
            signature=sig,
            issued_at="2026-04-09T00:00:00Z",
        )
        assert receipt.currency == "USD"

    def test_missing_required_raises(self):
        from ampro import CostReceipt
        with pytest.raises(ValidationError):
            CostReceipt()


class TestCostReceiptChain:
    def test_starts_empty_with_zero_total(self):
        from ampro import CostReceiptChain
        chain = CostReceiptChain()
        assert chain.receipts == []
        assert chain.total_cost_usd == 0
        assert chain.total_cost_usd_float == 0.0

    def test_add_receipt_appends_and_updates_total(self):
        from ampro import CostReceiptChain, CostReceipt
        chain = CostReceiptChain()
        nonce = secrets.token_urlsafe(16)
        pk = _seed_key("agent://a.example.com")
        sig = _sign_receipt_fields(
            pk, "agent://a.example.com", "t-1", 0.10, "USD",
            "2026-04-09T00:00:00Z", nonce,
        )
        receipt = CostReceipt(
            agent_id="agent://a.example.com",
            task_id="t-1",
            cost_usd=0.10,
            nonce=nonce,
            signature=sig,
            issued_at="2026-04-09T00:00:00Z",
        )
        chain.add_receipt(receipt)
        assert len(chain.receipts) == 1
        assert chain.total_cost_usd_float == pytest.approx(0.10)

    def test_multiple_receipts_maintain_order(self):
        from ampro import CostReceiptChain, CostReceipt
        chain = CostReceiptChain()

        agents = [
            ("agent://first.example.com", 0.05, "2026-04-09T00:00:00Z"),
            ("agent://second.example.com", 0.15, "2026-04-09T00:01:00Z"),
            ("agent://third.example.com", 0.30, "2026-04-09T00:02:00Z"),
        ]

        for agent_id, cost, issued in agents:
            nonce = secrets.token_urlsafe(16)
            pk = _seed_key(agent_id)
            sig = _sign_receipt_fields(pk, agent_id, "t-1", cost, "USD", issued, nonce)
            receipt = CostReceipt(
                agent_id=agent_id,
                task_id="t-1",
                cost_usd=cost,
                nonce=nonce,
                signature=sig,
                issued_at=issued,
            )
            chain.add_receipt(receipt)

        assert len(chain.receipts) == 3
        assert chain.receipts[0].agent_id == "agent://first.example.com"
        assert chain.receipts[1].agent_id == "agent://second.example.com"
        assert chain.receipts[2].agent_id == "agent://third.example.com"
        assert chain.total_cost_usd_float == pytest.approx(0.50)


class TestCostReceiptChainMixedCurrency:
    def test_chain_rejects_mixed_currency(self):
        """Chain locks on first receipt's currency and rejects mismatches."""
        from ampro import CostReceiptChain, CostReceipt
        from ampro.delegation.cost_receipt import CostReceiptVerificationError

        chain = CostReceiptChain()

        # Receipt 1 — USD
        nonce1 = secrets.token_urlsafe(16)
        pk1 = _seed_key("agent://usd.example.com")
        sig1 = _sign_receipt_fields(
            pk1, "agent://usd.example.com", "t-1", 1.00, "USD",
            "2026-04-09T00:00:00Z", nonce1,
        )
        r1 = CostReceipt(
            agent_id="agent://usd.example.com",
            task_id="t-1",
            cost_usd=1.00,
            currency="USD",
            nonce=nonce1,
            signature=sig1,
            issued_at="2026-04-09T00:00:00Z",
        )
        chain.add_receipt(r1)
        assert chain.currency == "USD"

        # Receipt 2 — EUR (mismatch) — must reject
        nonce2 = secrets.token_urlsafe(16)
        pk2 = _seed_key("agent://eur.example.com")
        sig2 = _sign_receipt_fields(
            pk2, "agent://eur.example.com", "t-1", 1.00, "EUR",
            "2026-04-09T00:01:00Z", nonce2,
        )
        r2 = CostReceipt(
            agent_id="agent://eur.example.com",
            task_id="t-1",
            cost_usd=1.00,
            currency="EUR",
            nonce=nonce2,
            signature=sig2,
            issued_at="2026-04-09T00:01:00Z",
        )
        with pytest.raises(CostReceiptVerificationError, match="currency mismatch"):
            chain.add_receipt(r2)

    def test_chain_uses_decimal_arithmetic(self):
        """Summing 0.1 three times should equal exactly 0.3 (not 0.30000...4)."""
        from decimal import Decimal
        from ampro import CostReceiptChain, CostReceipt

        chain = CostReceiptChain()
        for i in range(3):
            nonce = secrets.token_urlsafe(16)
            agent_id = f"agent://a{i}.example.com"
            pk = _seed_key(agent_id)
            sig = _sign_receipt_fields(
                pk, agent_id, "t-1", 0.1, "USD",
                f"2026-04-09T00:0{i}:00Z", nonce,
            )
            r = CostReceipt(
                agent_id=agent_id,
                task_id="t-1",
                cost_usd=0.1,
                currency="USD",
                nonce=nonce,
                signature=sig,
                issued_at=f"2026-04-09T00:0{i}:00Z",
            )
            chain.add_receipt(r)

        # Exact Decimal equality — this is the whole point of the fix.
        assert chain.total_cost_usd == Decimal("0.3")
        # Float view is available for callers that need it.
        assert chain.total_cost_usd_float == pytest.approx(0.3)


class TestTaskCompleteBodyCostReceipt:
    def test_accepts_cost_receipt_dict(self):
        from ampro import TaskCompleteBody
        body = TaskCompleteBody(
            task_id="t-99",
            result="done",
            cost_receipt={
                "agent_id": "agent://worker.example.com",
                "task_id": "t-99",
                "cost_usd": 0.25,
                "issued_at": "2026-04-09T00:00:00Z",
            },
        )
        assert body.cost_receipt is not None
        assert body.cost_receipt["cost_usd"] == 0.25

    def test_cost_receipt_defaults_to_none(self):
        from ampro import TaskCompleteBody
        body = TaskCompleteBody(
            task_id="t-100",
            result="done",
        )
        assert body.cost_receipt is None
