"""Tests for ampro.tracing — v0.1.5 distributed tracing primitives."""

import re

import pytest

from ampro.delegation.tracing import (
    TraceContext,
    generate_trace_id,
    generate_span_id,
    inject_trace_headers,
    extract_trace_context,
)


class TestGenerateTraceId:
    def test_generate_trace_id_format(self):
        """Trace IDs must be 32 lowercase hex characters (128 bits)."""
        tid = generate_trace_id()
        assert len(tid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", tid)

    def test_trace_id_uniqueness(self):
        """100 generated trace IDs must all be unique."""
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100


class TestGenerateSpanId:
    def test_generate_span_id_format(self):
        """Span IDs must be 16 lowercase hex characters (64 bits)."""
        sid = generate_span_id()
        assert len(sid) == 16
        assert re.fullmatch(r"[0-9a-f]{16}", sid)


class TestTraceContext:
    def test_trace_context_creation(self):
        """All fields round-trip through the dataclass."""
        ctx = TraceContext(
            trace_id="a" * 32,
            span_id="b" * 16,
            parent_span_id="c" * 16,
            trace_flags=0,
        )
        assert ctx.trace_id == "a" * 32
        assert ctx.span_id == "b" * 16
        assert ctx.parent_span_id == "c" * 16
        assert ctx.trace_flags == 0

    def test_trace_context_defaults(self):
        """parent_span_id defaults to None, trace_flags defaults to 1."""
        ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
        assert ctx.parent_span_id is None
        assert ctx.trace_flags == 1


class TestInjectExtract:
    def test_inject_extract_round_trip(self):
        """inject -> extract must reproduce the original context."""
        original = TraceContext(
            trace_id=generate_trace_id(),
            span_id=generate_span_id(),
            parent_span_id=generate_span_id(),
            trace_flags=1,
        )
        headers = inject_trace_headers(original)
        restored = extract_trace_context(headers)

        assert restored is not None
        assert restored.trace_id == original.trace_id
        assert restored.span_id == original.span_id
        assert restored.parent_span_id == original.parent_span_id

    def test_extract_missing_headers(self):
        """Returns None when required headers are absent."""
        assert extract_trace_context({}) is None
        assert extract_trace_context({"Trace-Id": "abc"}) is None
        assert extract_trace_context({"Span-Id": "def"}) is None

    def test_parent_span_propagation(self):
        """parent_span_id flows through inject/extract."""
        parent = generate_span_id()
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            span_id=generate_span_id(),
            parent_span_id=parent,
        )
        headers = inject_trace_headers(ctx)
        assert headers["Parent-Span-Id"] == parent

        restored = extract_trace_context(headers)
        assert restored is not None
        assert restored.parent_span_id == parent

    def test_inject_without_parent_omits_header(self):
        """When parent_span_id is None, Parent-Span-Id header is not emitted."""
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            span_id=generate_span_id(),
        )
        headers = inject_trace_headers(ctx)
        assert "Parent-Span-Id" not in headers
