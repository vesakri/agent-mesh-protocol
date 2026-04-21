"""Tests for handler exception sanitization (Task 5.9).

Validates that exception messages from handler code are NOT leaked to
external callers. The server MUST return a generic error message and
log the full traceback server-side via logger.exception().
"""

from __future__ import annotations

import asyncio
import json

from ampro.server import AgentServer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def _make_envelope(**overrides) -> dict:
    """Build a minimal valid envelope dict."""
    base = {
        "sender": "@alice",
        "recipient": "@test-agent",
        "body_type": "message",
        "body": {"text": "hello"},
    }
    base.update(overrides)
    return base


def _make_server(**kwargs) -> AgentServer:
    """Create a server with sensible defaults."""
    defaults = {"agent_id": "@test-agent", "endpoint": "https://test.example.com"}
    defaults.update(kwargs)
    return AgentServer(**defaults)


# ===========================================================================
# TestExceptionSanitization
# ===========================================================================


class TestExceptionSanitization:
    """Handler exceptions must not leak internal details to callers."""

    def test_value_error_message_not_leaked(self):
        """ValueError message must not appear in the response."""
        server = _make_server()
        secret = "secret_db_password=hunter2"

        @server.on("message")
        async def handle(msg):
            raise ValueError(secret)

        envelope = _make_envelope()
        status, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        data = json.loads(body_str)
        assert status == 500
        assert secret not in body_str
        assert secret not in data.get("detail", "")

    def test_runtime_error_returns_generic_message(self):
        """RuntimeError should produce a generic 'unexpected error' response."""
        server = _make_server()

        @server.on("message")
        async def handle(msg):
            raise RuntimeError("internal path /opt/app/db.py line 42")

        envelope = _make_envelope()
        status, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        data = json.loads(body_str)
        assert status == 500
        assert "unexpected error" in data["detail"].lower()
        assert "/opt/app" not in body_str

    def test_exception_returns_500_status(self):
        """Any unhandled handler exception must return HTTP 500."""
        server = _make_server()

        @server.on("message")
        async def handle(msg):
            raise TypeError("unexpected None")

        envelope = _make_envelope()
        status, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        assert status == 500
        data = json.loads(body_str)
        assert data["type"] == "urn:amp:error:internal-error"

    def test_exception_detail_is_generic(self):
        """The detail field must be a fixed generic string."""
        server = _make_server()

        @server.on("message")
        async def handle(msg):
            raise Exception("should not appear in response")

        envelope = _make_envelope()
        _, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        data = json.loads(body_str)
        assert data["detail"] == (
            "An unexpected error occurred while processing the request."
        )

    def test_normal_handler_unaffected(self):
        """Successful handlers must not be affected by sanitization logic."""
        server = _make_server()

        @server.on("message")
        async def handle(msg):
            return {"status": "ok", "echo": msg.body}

        envelope = _make_envelope()
        status, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        assert status == 202
        data = json.loads(body_str)
        assert data["status"] == "ok"
        assert data["echo"]["text"] == "hello"

    def test_key_error_not_leaked(self):
        """KeyError with sensitive key name must not leak."""
        server = _make_server()

        @server.on("message")
        async def handle(msg):
            d = {}
            return d["api_key_for_stripe"]  # KeyError with sensitive name

        envelope = _make_envelope()
        status, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        assert status == 500
        assert "api_key_for_stripe" not in body_str
        assert "stripe" not in body_str.lower()

    def test_sync_handler_exception_sanitized(self):
        """Sync (non-async) handlers should also be sanitized."""
        server = _make_server()

        @server.on("message")
        def handle(msg):
            raise RuntimeError("sync handler leak attempt")

        envelope = _make_envelope()
        status, _, body_str = _run(
            server.route("POST", "/agent/message", envelope)
        )
        assert status == 500
        data = json.loads(body_str)
        assert "sync handler leak attempt" not in body_str
        assert "unexpected error" in data["detail"].lower()
