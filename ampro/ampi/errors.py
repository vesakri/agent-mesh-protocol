"""AMPI error hierarchy.

All AMPI-specific exceptions derive from AMPError.
"""
from __future__ import annotations

from typing import Any

from ampro.errors import AmpError
from ampro.wire.errors import ProblemDetail


class AMPError(AmpError):
    """Base error for AMPI operations."""

    def __init__(self, code: str, message: str = "", *, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"{code}: {message}" if message else code)

    def to_problem_detail(self, status: int = 500) -> ProblemDetail:
        return ProblemDetail(
            type=f"urn:amp:error:{self.code}",
            title=self.code.replace("_", " ").title(),
            status=status,
            detail=f"{self.code}: {self.message}" if self.message else self.code,
        )


class StreamLimitExceeded(AMPError):
    """Raised when a streaming handler exceeds server-enforced limits."""

    def __init__(self, reason: str, *, limit: int, current: int) -> None:
        self.limit = limit
        self.current = current
        super().__init__("stream_limit_exceeded", f"{reason}: limit={limit}, current={current}")


class BackpressureError(AMPError):
    """Raised when the client is too slow and backpressure triggers."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__("backpressure", reason)
