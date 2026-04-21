"""Tests for TestServer."""
from __future__ import annotations

import asyncio

import pytest

from ampro.core.envelope import AgentMessage
from ampro.ampi.app import AgentApp
from ampro.trust.tiers import TrustTier


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_dispatch_simple_handler():
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on("task.create")
    async def handle(msg, ctx):
        return {"result": "done", "sender": ctx.sender_address}

    server = TestServer(agent)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="task.create",
        body={"description": "test"},
    )
    result = _run(server.send(msg))
    assert result["result"] == "done"
    assert result["sender"] == "agent://caller.example.com"


def test_dispatch_with_trust_tier():
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on("task.create")
    async def handle(msg, ctx):
        return {"tier": ctx.trust_tier.value}

    server = TestServer(agent, trust_tier=TrustTier.EXTERNAL)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="task.create",
        body={},
    )
    result = _run(server.send(msg))
    assert result["tier"] == "external"


def test_dispatch_unknown_body_type():
    from ampro.server.test import TestServer
    from ampro.ampi.errors import AMPError

    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    server = TestServer(agent)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="unknown.type",
        body={},
    )
    with pytest.raises(AMPError, match="no_handler"):
        _run(server.send(msg))


def test_middleware_runs():
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    calls: list[str] = []

    @agent.middleware
    async def track(msg, ctx, next_handler):
        calls.append("before")
        result = await next_handler(msg, ctx)
        calls.append("after")
        return result

    @agent.on("message")
    async def handle(msg, ctx):
        calls.append("handler")
        return {"ok": True}

    server = TestServer(agent)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="message",
        body={},
    )
    _run(server.send(msg))
    assert calls == ["before", "handler", "after"]


def test_multiple_middleware_ordering():
    """Middleware should run in registration order (first registered = outermost)."""
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    calls: list[str] = []

    @agent.middleware
    async def first(msg, ctx, next_handler):
        calls.append("first-before")
        result = await next_handler(msg, ctx)
        calls.append("first-after")
        return result

    @agent.middleware
    async def second(msg, ctx, next_handler):
        calls.append("second-before")
        result = await next_handler(msg, ctx)
        calls.append("second-after")
        return result

    @agent.on("message")
    async def handle(msg, ctx):
        calls.append("handler")
        return {"ok": True}

    server = TestServer(agent)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="message",
        body={},
    )
    _run(server.send(msg))
    assert calls == [
        "first-before",
        "second-before",
        "handler",
        "second-after",
        "first-after",
    ]


def test_lifecycle_hooks():
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    events: list[str] = []

    @agent.on_startup
    async def on_startup():
        events.append("startup")

    @agent.on_shutdown
    async def on_shutdown():
        events.append("shutdown")

    @agent.on("message")
    async def handle(msg, ctx):
        return {}

    server = TestServer(agent)
    _run(server.startup())
    _run(server.shutdown())
    assert events == ["startup", "shutdown"]


def test_dict_app():
    from ampro.server.test import TestServer

    async def handle(msg, ctx):
        return {"from_dict": True}

    app = {
        "agent_id": "agent://dict.example.com",
        "endpoint": "https://dict.example.com",
        "handlers": {"message": handle},
    }
    server = TestServer(app)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://dict.example.com",
        body_type="message",
        body={},
    )
    result = _run(server.send(msg))
    assert result["from_dict"] is True


def test_sync_handler():
    """TestServer should handle sync (non-async) handlers."""
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on("ping")
    def handle(msg, ctx):
        return {"pong": True}

    server = TestServer(agent)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="ping",
        body={},
    )
    result = _run(server.send(msg))
    assert result["pong"] is True


def test_context_has_trace_ids():
    """AMPContext should have non-empty trace_id and span_id."""
    from ampro.server.test import TestServer

    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    captured_ctx = {}

    @agent.on("message")
    async def handle(msg, ctx):
        captured_ctx["trace_id"] = ctx.trace_id
        captured_ctx["span_id"] = ctx.span_id
        return {}

    server = TestServer(agent)
    msg = AgentMessage(
        sender="agent://caller.example.com",
        recipient="agent://test.example.com",
        body_type="message",
        body={},
    )
    _run(server.send(msg))
    assert len(captured_ctx["trace_id"]) == 32  # 128-bit hex
    assert len(captured_ctx["span_id"]) == 16  # 64-bit hex


def test_import_from_server_package():
    """TestServer should be importable from ampro.server."""
    from ampro.server import TestServer

    assert TestServer is not None
