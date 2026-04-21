"""Tests for AMPContext."""
from __future__ import annotations

import asyncio
import uuid

import pytest

from ampro.trust.tiers import TrustTier
from ampro.core.capabilities import CapabilitySet
from ampro.compliance.types import ContentClassification


def _make_ctx(**overrides):
    from ampro.ampi.context import AMPContext

    defaults = {
        "agent_address": "agent://test.example.com",
        "sender_address": "agent://sender.example.com",
        "request_id": str(uuid.uuid4()),
        "trust_tier": TrustTier.VERIFIED,
        "trace_id": "trace-123",
        "span_id": "span-456",
    }
    defaults.update(overrides)
    return AMPContext(**defaults)


def test_context_creation():
    ctx = _make_ctx()
    assert ctx.agent_address == "agent://test.example.com"
    assert ctx.trust_tier == TrustTier.VERIFIED
    assert ctx.priority == "normal"


def test_context_trust_tier_readable():
    ctx = _make_ctx(trust_tier=TrustTier.EXTERNAL)
    assert ctx.trust_tier == TrustTier.EXTERNAL


def test_context_delegation_fields():
    ctx = _make_ctx(
        remaining_budget="3.50USD",
        delegation_depth_remaining=2,
        visited_agents=["agent://a.com", "agent://b.com"],
    )
    assert ctx.remaining_budget == "3.50USD"
    assert ctx.delegation_depth_remaining == 2
    assert len(ctx.visited_agents) == 2


def test_context_compliance_fields():
    ctx = _make_ctx(
        jurisdiction="EU",
        data_residency="eu-west-1",
        retention_policy="30d",
    )
    assert ctx.jurisdiction == "EU"


def test_context_headers_present():
    ctx = _make_ctx(headers={"X-Custom": "ok"})
    assert ctx.headers["X-Custom"] == "ok"


def test_context_methods_exist():
    ctx = _make_ctx()
    for method in [
        "emit",
        "emit_audit",
        "emit_event",
        "send",
        "discover",
        "delegate",
        "search_registry",
        "verify_identity",
        "check_consent",
        "request_trust_upgrade",
        "pause_session",
        "resume_session",
        "close_session",
    ]:
        assert callable(getattr(ctx, method))


def test_context_emit_raises_not_implemented():
    ctx = _make_ctx()
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(ctx.emit(None))
