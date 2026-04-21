"""
Agent Protocol — Erasure Propagation Status.

Tracks GDPR erasure requests as they propagate across the agent mesh.
When Agent A requests erasure from Agent B, and B had shared data with
Agent C, B reports back to A via erasure.propagation_status for each
downstream agent.

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel, Field

# Retry policy constants (exposed for observability/tests).
MAX_ERASURE_RETRIES = 30
DEFAULT_RETRY_BASE_DELAY_SEC = 60
MAX_RETRY_DELAY_SEC = 24 * 60 * 60  # cap individual backoff at 24h


class ErasurePropagationStatus(str, Enum):
    """Possible states for an erasure propagation report."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ErasurePropagationStatusBody(BaseModel):
    """body.type = 'erasure.propagation_status' — downstream erasure report.

    Downstream receivers may be offline when an erasure is first
    propagated.  Senders SHOULD retry with exponential backoff and
    record retry metadata on the body.  See :func:`compute_next_retry`.

    Compliance-driven cache invalidations (e.g. dropping cached
    ``agent.json`` or visibility metadata after a revocation) MAY reuse
    the push-style flow.  See
    :class:`ampro.agent.schema.AgentMetadataInvalidateBody` for the
    canonical invalidation body type.
    """

    erasure_id: str = Field(description="ID of the original erasure request")
    agent_id: str = Field(description="Agent reporting its erasure status")
    status: str = Field(
        description="Propagation status: pending, completed, or failed",
    )
    records_affected: int = Field(
        description="Number of records erased or attempted",
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp of this status report",
    )
    detail: str | None = Field(
        default=None,
        description="Human-readable detail, especially on failure",
    )
    downstream_agents: list[str] = Field(
        default_factory=list,
        description="Agents this node propagated the erasure to",
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        le=MAX_ERASURE_RETRIES,
        description="Number of retry attempts",
    )
    next_retry_at: datetime | None = Field(
        default=None,
        description="When the next retry is scheduled",
    )
    last_error: str | None = Field(
        default=None,
        max_length=1024,
        description="Last error observed while propagating",
    )
    final: bool = Field(
        default=False,
        description="True when retries are exhausted",
    )

    model_config = {"extra": "ignore"}


def compute_next_retry(
    retry_count: int,
    base_delay_sec: int = DEFAULT_RETRY_BASE_DELAY_SEC,
    *,
    now: datetime | None = None,
    jitter: float | None = None,
) -> datetime:
    """Compute the next retry time using exponential backoff with jitter.

    The delay is ``base_delay_sec * 2**retry_count`` seconds, plus a
    uniform random jitter in ``[0, base_delay_sec)`` to avoid thundering
    herds.  The result is capped at :data:`MAX_RETRY_DELAY_SEC`.

    When ``retry_count >= MAX_ERASURE_RETRIES`` the caller SHOULD set
    ``final=True`` on the status body and stop retrying.

    Args:
        retry_count: The attempt index (0 for the first retry).
        base_delay_sec: Base delay in seconds; defaults to 60s.
        now: Optional clock override for deterministic testing.
        jitter: Optional fixed jitter in seconds; if ``None`` a random
            value in ``[0, base_delay_sec)`` is used.
    """
    current = now if now is not None else datetime.now(timezone.utc)
    # Clamp exponent to avoid huge shifts on near-exhausted retries.
    exponent = min(retry_count, 20)
    delay = min(base_delay_sec * (2**exponent), MAX_RETRY_DELAY_SEC)
    jitter_seconds = (
        jitter if jitter is not None else random.uniform(0, base_delay_sec)
    )
    return current + timedelta(seconds=delay + jitter_seconds)
