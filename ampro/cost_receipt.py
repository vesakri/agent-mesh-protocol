"""
Agent Protocol — Cost Receipts.

Per-hop cost tracking for delegation chain cost attribution. Each agent
in a delegation chain attaches a signed cost receipt to its response,
enabling end-to-end cost visibility.

This module is PURE — only stdlib + pydantic.
No platform-specific imports (app.*, etc.).
Designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
    signature: str | None = Field(
        default=None,
        description="Ed25519 signature for tamper detection",
    )
    issued_at: str = Field(
        description="ISO-8601 timestamp when receipt was issued",
    )

    model_config = {"extra": "ignore"}


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

    def add_receipt(self, receipt: CostReceipt) -> None:
        """Append a receipt and update the running total."""
        self.receipts.append(receipt)
        self.total_cost_usd += receipt.cost_usd
