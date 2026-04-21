"""TestServer — the simplest AMPI server for unit testing.

No HTTP, no network. Just: build context, call handler, return result.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
#
# Intended for `pip install agent-protocol && python -m ampro.server`.
# Full-stack implementers mount AMPI handlers into their own HTTP
# framework and do not use this server.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

import inspect
import uuid
from typing import Any

from ampro.ampi.app import AgentApp
from ampro.ampi.context import AMPContext
from ampro.ampi.errors import AMPError
from ampro.core.envelope import AgentMessage
from ampro.delegation.tracing import generate_span_id, generate_trace_id
from ampro.trust.tiers import TrustTier


class TestServer:
    """AMPI test harness — dispatch messages to handlers without transport."""

    def __init__(
        self,
        app: AgentApp | dict,
        *,
        trust_tier: TrustTier = TrustTier.VERIFIED,
    ) -> None:
        if isinstance(app, dict):
            self._handlers = app.get("handlers", {})
            self._middleware: list = app.get("middleware", [])
            self._startup: list = app.get("startup", [])
            self._shutdown: list = app.get("shutdown", [])
            self._error_handler = app.get("error_handler")
            self._agent_id = app.get("agent_id", "agent://test")
            self._streaming: set = set()
        else:
            self._handlers = app.handlers
            self._middleware = app.middleware_chain
            self._startup = app.startup_hooks
            self._shutdown = app.shutdown_hooks
            self._error_handler = app.error_handler
            self._agent_id = app.agent_id
            self._streaming = app.streaming_handlers
        self._trust_tier = trust_tier

    def _build_context(self, message: AgentMessage) -> AMPContext:
        return AMPContext(
            agent_address=self._agent_id,
            sender_address=message.sender or "agent://unknown",
            request_id=message.id or str(uuid.uuid4()),
            trust_tier=self._trust_tier,
            trace_id=generate_trace_id(),
            span_id=generate_span_id(),
            headers=dict(message.headers) if message.headers else {},
        )

    async def send(self, message: AgentMessage) -> Any:
        """Dispatch *message* through middleware and handler. Returns handler result."""
        ctx = self._build_context(message)
        handler = self._handlers.get(message.body_type)
        if handler is None:
            raise AMPError(
                "no_handler",
                f"No handler for body_type '{message.body_type}'",
            )

        # Terminal handler (always async-safe).
        async def call_handler(msg: AgentMessage, c: AMPContext) -> Any:
            result = handler(msg, c)
            if inspect.isawaitable(result):
                result = await result
            return result

        # Build middleware chain inside-out so the first-registered
        # middleware runs first (outermost wrapper).
        chain = call_handler
        for mw in reversed(self._middleware):
            prev = chain  # capture current chain for this closure

            def _wrap(m: Any = mw, nxt: Any = prev) -> Any:
                async def wrapped(msg: AgentMessage, c: AMPContext) -> Any:
                    return await m(msg, c, nxt)
                return wrapped

            chain = _wrap()

        return await chain(message, ctx)

    async def startup(self) -> None:
        """Run all registered startup hooks."""
        for hook in self._startup:
            result = hook()
            if inspect.isawaitable(result):
                await result

    async def shutdown(self) -> None:
        """Run all registered shutdown hooks."""
        for hook in self._shutdown:
            result = hook()
            if inspect.isawaitable(result):
                await result
