"""Agent Protocol — Circuit breaker protocol types. PURE."""

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

    state: CircuitState
    failures: int = 0
    reset_at: str | None = None

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
