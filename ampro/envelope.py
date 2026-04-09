"""
Agent Protocol — Message Envelope.

The universal message format for agent-to-agent communication.
Built on HTTP conventions. Extensible via headers.
Receivers MUST ignore unknown headers (forward-compatibility).
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


# Standard headers that the protocol defines.
# Receivers should understand these but MUST ignore unknown headers.
STANDARD_HEADERS = frozenset({
    "Authorization",
    "Content-Type",
    "Content-Classification",
    "Identity-Context",
    "Delegation-Depth",
    "Visited-Agents",
    "Session-Id",
    "In-Reply-To",
    "Priority",
    "Trust-Tier",
    "Protocol-Version",
    "Capabilities",
    "Accept-Capabilities",
    "Accept-Version",
    "Accept-Language",
    "Chain-Budget",
    "Callback-URL",
    "Callback-Events",
    "Nonce",
    "Via",
    "Timeout",
    "Negotiated-Capabilities",
    "Negotiated-Level",
    "Downgrade-Warning",
    "X-Circuit-State",
    "X-Circuit-Failures",
    "X-Circuit-Reset-At",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "X-Session-Restarted",
    "Content-Language",
    "Trust-Upgrade",
    "Poll-Interval",
    "Retry-After",
    # v0.1.1 — Handshake, trust scoring, context schema
    "Session-Binding",
    "Trust-Score",
    "Context-Schema",
    "Transaction-Id",
    "Correlation-Group",
    "Commitment-Level",
})


class AgentMessage(BaseModel):
    """
    The universal message envelope for agent communication.

    Designed for HTTP transport. Any HTTP client can construct this.
    Headers are extensible — receivers ignore what they don't understand.

    Example:
        msg = AgentMessage(
            sender="@alice-agi",
            recipient="@weather-service",
            body="What is the forecast for tomorrow?",
            headers={"Session-Id": "conv-123", "Priority": "normal"},
        )
    """

    sender: str = Field(
        description="Agent address of the sender (@slug, DID, or URL)",
    )
    recipient: str = Field(
        description="Agent address of the recipient (@slug, DID, or URL)",
    )
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique message identifier for dedup and correlation",
    )
    body_type: str = Field(
        default="message",
        description="Body type — one of 23 canonical types or a reverse-domain extension",
    )
    headers: dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible key-value headers. Receivers ignore unknown headers.",
    )
    body: Any = Field(
        default=None,
        description="Message content — text, structured JSON, or binary reference",
    )

    model_config = {"extra": "ignore"}
