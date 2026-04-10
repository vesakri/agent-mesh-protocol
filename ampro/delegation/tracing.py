"""
Agent Protocol — Distributed Tracing.

W3C Trace Context (https://www.w3.org/TR/trace-context/) inspired
distributed tracing primitives for agent-to-agent message flows.

Provides trace/span ID generation, header injection/extraction for
propagating trace context across agent boundaries.

PURE — zero platform-specific imports. Only stdlib.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def generate_trace_id() -> str:
    """Generate a 32-character lowercase hex trace ID (128 bits)."""
    return os.urandom(16).hex()


def generate_span_id() -> str:
    """Generate a 16-character lowercase hex span ID (64 bits)."""
    return os.urandom(8).hex()


@dataclass
class TraceContext:
    """Immutable trace context propagated across agent boundaries."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    trace_flags: int = 1  # 1 = sampled


def inject_trace_headers(ctx: TraceContext) -> dict[str, str]:
    """Inject trace context into HTTP-style headers.

    Returns a dict with ``Trace-Id``, ``Span-Id``, and optionally
    ``Parent-Span-Id`` headers.
    """
    headers: dict[str, str] = {
        "Trace-Id": ctx.trace_id,
        "Span-Id": ctx.span_id,
    }
    if ctx.parent_span_id is not None:
        headers["Parent-Span-Id"] = ctx.parent_span_id
    return headers


def extract_trace_context(headers: dict[str, str]) -> TraceContext | None:
    """Extract trace context from HTTP-style headers.

    Returns ``None`` if the required ``Trace-Id`` or ``Span-Id`` headers
    are missing.
    """
    trace_id = headers.get("Trace-Id")
    span_id = headers.get("Span-Id")
    if trace_id is None or span_id is None:
        return None
    return TraceContext(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=headers.get("Parent-Span-Id"),
    )
