"""
Agent Protocol — Status Codes.

15 agent-specific status codes compatible with HTTP status codes.
Each code has a description and category (1xx=acknowledged, 2xx=success,
3xx=redirect, 4xx=sender error, 5xx=receiver error).
"""

from __future__ import annotations

from enum import IntEnum


class AgentStatus(IntEnum):
    """Agent protocol status codes — HTTP-compatible."""

    # 1xx — Acknowledged
    RECEIVED = 100
    PROCESSING = 101
    INPUT_REQUIRED = 102

    # 2xx — Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202

    # 3xx — Redirect
    MOVED = 301
    REFER = 302
    ESCALATED = 303

    # 4xx — Sender Problem
    INVALID = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TIMEOUT = 408
    CONFLICT = 409
    PAYLOAD_TOO_LARGE = 413
    RATE_LIMITED = 429

    # 5xx — Receiver Problem
    ERROR = 500
    NOT_IMPLEMENTED = 501
    UNAVAILABLE = 503

    @property
    def description(self) -> str:
        return _DESCRIPTIONS.get(self, "Unknown status")

    @property
    def is_success(self) -> bool:
        return 200 <= self.value < 300

    @property
    def is_error(self) -> bool:
        return self.value >= 400


_DESCRIPTIONS: dict[AgentStatus, str] = {
    AgentStatus.RECEIVED: "Message received",
    AgentStatus.PROCESSING: "Processing request",
    AgentStatus.INPUT_REQUIRED: "Additional input needed",
    AgentStatus.OK: "Success",
    AgentStatus.CREATED: "Resource created (booking, order, membership)",
    AgentStatus.ACCEPTED: "Accepted for async processing",
    AgentStatus.MOVED: "Agent moved to new address",
    AgentStatus.REFER: "Try this other agent",
    AgentStatus.ESCALATED: "Handed to a human",
    AgentStatus.INVALID: "Malformed message",
    AgentStatus.UNAUTHORIZED: "Authentication required",
    AgentStatus.FORBIDDEN: "Access denied",
    AgentStatus.NOT_FOUND: "Agent not found",
    AgentStatus.TIMEOUT: "Request timed out",
    AgentStatus.CONFLICT: "Conflict (double booking, race condition)",
    AgentStatus.PAYLOAD_TOO_LARGE: "Message exceeds size limit",
    AgentStatus.RATE_LIMITED: "Too many requests",
    AgentStatus.ERROR: "Internal error",
    AgentStatus.NOT_IMPLEMENTED: "Capability not implemented",
    AgentStatus.UNAVAILABLE: "Agent is down or paused",
}
