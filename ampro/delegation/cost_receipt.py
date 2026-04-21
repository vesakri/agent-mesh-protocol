"""
Agent Protocol — Cost Receipts.

Per-hop cost tracking for delegation chain cost attribution. Each agent
in a delegation chain attaches a signed cost receipt to its response,
enabling end-to-end cost visibility.

This module is PURE — only stdlib + pydantic + cryptography.
No platform-specific imports (app.*, etc.).
Designed for extraction as part of `pip install agent-protocol`.
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
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CostReceiptVerificationError(Exception):
    """Raised when a CostReceipt fails signature verification or replay check."""


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CostReceipt(BaseModel):
    """A single per-hop cost receipt attached by an agent."""

    agent_id: str = Field(description="Agent that incurred the cost")
    task_id: str = Field(description="Task the cost is associated with")
    cost_usd: float = Field(description="Cost in USD")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    breakdown: dict[str, Any] | None = Field(
        default=None,
        description="Itemized cost breakdown",
    )
    token_usage: dict[str, int] | None = Field(
        default=None,
        description="Token counts (e.g. input, output)",
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Wall-clock time spent in seconds",
    )
    nonce: str = Field(
        description="Single-use nonce for replay defense (use secrets.token_urlsafe(16))",
    )
    signature: str = Field(
        description="Ed25519 signature (base64url) over canonical_for_signing() bytes",
    )
    issued_at: str = Field(
        description="ISO-8601 timestamp when receipt was issued",
    )

    model_config = {"extra": "ignore"}

    def canonical_for_signing(self) -> bytes:
        """Bytes the signature covers — the receipt minus the signature itself.

        Uses stdlib json.dumps with sort_keys=True, separators, ensure_ascii=False
        — byte-identical to ampro's other canonical-form helpers.
        """
        return json.dumps(
            {
                "agent_id": self.agent_id,
                "task_id": self.task_id,
                "cost_usd": self.cost_usd,
                "currency": self.currency,
                "issued_at": self.issued_at,
                "nonce": self.nonce,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")


class CostReceiptChain(BaseModel):
    """Ordered collection of cost receipts across a delegation chain."""

    receipts: list[CostReceipt] = Field(
        default_factory=list,
        description="Ordered list of receipts, one per delegation hop",
    )
    total_cost_usd: float = Field(
        default=0.0,
        description="Sum of all hop costs",
    )

    model_config = {"extra": "ignore"}

    def model_post_init(self, __context: Any) -> None:
        """Initialize internal nonce tracking set after Pydantic init."""
        object.__setattr__(self, "_consumed_nonces", set())

    def add_receipt(self, receipt: CostReceipt) -> None:
        """Verify and append a receipt, updating the running total.

        Raises CostReceiptVerificationError on:
        - Replay: nonce already consumed in this chain
        - Unknown key: no public key found for agent_id
        - Bad signature: Ed25519 verification fails
        """
        consumed: set[str] = object.__getattribute__(self, "_consumed_nonces")

        # 1. Replay check
        if receipt.nonce in consumed:
            raise CostReceiptVerificationError(
                f"cost receipt nonce {receipt.nonce} already consumed"
            )

        # 2. Signature check
        from ampro.trust.resolver import get_public_key

        pub_bytes = get_public_key(receipt.agent_id)
        if pub_bytes is None:
            raise CostReceiptVerificationError(
                f"no public key for agent_id {receipt.agent_id}"
            )

        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
        from cryptography.exceptions import InvalidSignature
        import base64

        try:
            pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
            pad = "=" * (-len(receipt.signature) % 4)
            sig_bytes = base64.urlsafe_b64decode(receipt.signature + pad)
            pub_key.verify(sig_bytes, receipt.canonical_for_signing())
        except InvalidSignature as exc:
            raise CostReceiptVerificationError(
                f"signature verification failed for receipt nonce={receipt.nonce}: {exc}"
            ) from exc
        except Exception as exc:
            raise CostReceiptVerificationError(
                f"signature decode error for nonce={receipt.nonce}: {exc}"
            ) from exc

        # 3. All checks passed — append
        consumed.add(receipt.nonce)
        self.receipts.append(receipt)
        self.total_cost_usd += receipt.cost_usd
