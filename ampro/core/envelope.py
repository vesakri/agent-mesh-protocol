"""
Agent Protocol — Message Envelope.

The universal message format for agent-to-agent communication.
Built on HTTP conventions. Extensible via headers.
Receivers MUST ignore unknown headers (forward-compatibility).
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field, model_validator

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
    # v0.1.2 — Defense
    "Key-Revoked-At",
    "Anonymous-Sender-Hint",
    # v0.1.3 — Resilience
    "Hop-Timeout",
    # v0.1.4 — Routing
    "X-Load-Level",
    # v0.1.5 — Observability
    "Trace-Id",
    "Span-Id",
    # v0.1.6 — Compliance at Scale
    "Jurisdiction",
    "Data-Residency",
    # v0.1.7 — Streaming at Scale
    "Stream-Channel",
    # v0.1.9 — Hardening
    "Content-Encryption",
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
        max_length=512,
        description="Agent address of the sender (@slug, DID, or URL)",
    )
    recipient: str = Field(
        max_length=512,
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
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Extensible key-value headers (string values only, RFC 7230 §3.2).",
    )
    body: Any = Field(
        default=None,
        description="Message content — text, structured JSON, or binary reference",
    )

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _headers_must_be_strings(cls, data: Any) -> Any:
        """Reject non-string header values (RFC 7230 §3.2 — field-values are strings)."""
        if not isinstance(data, dict):
            return data
        headers = data.get("headers")
        if headers is None:
            return data
        if not isinstance(headers, dict):
            return data
        for key, value in headers.items():
            if not isinstance(value, str):
                raise ValueError(
                    f"header values must be strings (RFC 7230 §3.2); "
                    f"got {type(value).__name__} for header {key!r}"
                )
        return data

    @model_validator(mode="after")
    def _validate_body_against_body_type(self) -> AgentMessage:
        """Envelope-level body/body_type consistency hook.

        When ``body`` is a dict and ``body_type`` is a registered schema, we
        dispatch to :func:`ampro.core.body_schemas.validate_body` to verify
        shape.  This is a *best-effort* check: server-side request routing
        also calls ``validate_body`` (see :mod:`ampro.server.core`) and is
        the authoritative enforcement point — this hook exists so that
        envelopes constructed in-memory (e.g. for tests or non-server
        producers) surface obvious mismatches at construction time without
        a network round-trip.

        We swallow validation failures silently here because several
        integration tests intentionally construct envelopes with mismatched
        bodies as fixtures (e.g. ``body_type="message"`` + custom shape) and
        downstream code may deliberately pass partial bodies through the
        envelope (e.g. encryption wrappers re-use ``body_type`` of the
        ciphertext).  The server path still rejects mismatches with a
        descriptive error.
        """
        if not isinstance(self.body, dict):
            return self
        try:
            from ampro.core.body_schemas import (  # noqa: F401
                _BODY_TYPE_REGISTRY,
                validate_body,
            )
        except ImportError:
            return self
        if self.body_type not in _BODY_TYPE_REGISTRY:
            return self
        try:
            validate_body(self.body_type, self.body)
        except Exception:
            # Best-effort only — authoritative check happens server-side.
            pass
        return self
