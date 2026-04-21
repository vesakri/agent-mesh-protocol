"""Agent Protocol — Circuit breaker protocol types. PURE."""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
#
# This module defines the response envelope (`CircuitBreakerInfo`)
# emitted by circuit-aware endpoints. It does not include a
# controller — servers bring their own circuit logic and populate
# this envelope when reporting state on health / rate-limit
# introspection endpoints.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CircuitState(str, Enum):
    """Protocol-level circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreakerInfo(BaseModel):
    """Circuit breaker state for response headers."""

    state: CircuitState = Field(description="Current circuit breaker state (closed, open, half-open)")
    failures: int = Field(default=0, description="Consecutive failure count since last successful call")
    reset_at: str | None = Field(default=None, description="ISO 8601 timestamp when the circuit breaker will attempt reset")

    model_config = {"extra": "ignore"}

    def to_headers(self) -> dict[str, str]:
        """Format as HTTP response headers."""
        headers = {
            "X-Circuit-State": self.state.value,
            "X-Circuit-Failures": str(self.failures),
        }
        if self.reset_at:
            headers["X-Circuit-Reset-At"] = self.reset_at
        return headers
