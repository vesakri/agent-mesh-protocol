"""
AMP Reference Server — Core.

A minimal server like Python's ``http.server``.  One class: ``AgentServer``.

Framework-agnostic routing via ``route(method, path, body)``; optional
adapters for FastAPI and Flask.

Usage::

    from ampro.server import AgentServer

    server = AgentServer(agent_id="@weather", endpoint="https://weather.example.com")

    @server.on("task.create")
    async def handle_create(msg):
        return {"result": "sunny"}

    server.run(port=8000)

PURE — zero platform-specific imports at module level.
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

import asyncio
import inspect
import json
import logging
import time
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ampro.ampi.app import AgentApp

from pydantic import BaseModel, ValidationError

from ampro.core.envelope import AgentMessage
from ampro.core.body_schemas import validate_body
from ampro.core.versioning import CURRENT_VERSION
from ampro.agent.schema import AgentJson
from ampro.agent.health import HealthResponse
from ampro.wire.errors import (
    ProblemDetail,
    invalid_message,
    internal_error,
    not_implemented,
    not_found,
)
from ampro.wire.config import WireConfig, DEFAULTS

logger = logging.getLogger(__name__)


class AgentServer:
    """Minimal AMP reference server.

    Registers body-type handlers with ``@server.on("task.create")`` and
    routes incoming messages to them.  All routing goes through the
    framework-agnostic ``route(method, path, body)`` method; ``run()``
    starts a real HTTP server via FastAPI or Flask.
    """

    def __init__(
        self,
        agent_id: str,
        endpoint: str,
        config: WireConfig | None = None,
        agent_json: AgentJson | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.endpoint = endpoint
        self.config = config or DEFAULTS
        self._start_time = time.monotonic()

        # Build agent.json — use provided or auto-generate a minimal one.
        if agent_json is not None:
            self.agent_json = agent_json
        else:
            self.agent_json = AgentJson(
                protocol_version=CURRENT_VERSION,
                identifiers=[agent_id],
                endpoint=endpoint,
            )

        # Handler registries.
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._default_handler: Callable[..., Any] | None = None

    # ------------------------------------------------------------------
    # Alternate constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_app(cls, app: AgentApp) -> AgentServer:
        """Create an AgentServer from an AgentApp.

        Maps AgentApp handlers to AgentServer handlers. Handlers
        registered with ``@app.on("body_type")`` are wrapped to
        accept the old ``(msg)`` signature if needed.
        """
        from ampro.ampi.app import AgentApp as _AgentApp  # avoid circular at module level

        server = cls(
            agent_id=app.agent_id,
            endpoint=app.endpoint,
            agent_json=app.agent_json,
        )
        # Copy handlers — AgentServer's old API uses (msg) only,
        # but AMPI handlers use (msg, ctx).  We keep them as-is
        # and let the handler pipeline deal with arity.
        for body_type, handler in app.handlers.items():
            server._handlers[body_type] = handler
        if app.error_handler:
            server._default_handler = app.error_handler
        return server

    # ------------------------------------------------------------------
    # Decorators
    # ------------------------------------------------------------------

    def on(self, body_type: str) -> Callable[..., Any]:
        """Register a handler for a specific body_type.

        Example::

            @server.on("task.create")
            async def handle(msg: AgentMessage):
                return {"status": "ok"}
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self._handlers[body_type] = fn
            return fn

        return decorator

    def default(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        """Register a fallback handler for unrecognised body types.

        Example::

            @server.default
            async def fallback(msg: AgentMessage):
                return {"echo": msg.body}
        """
        self._default_handler = fn
        return fn

    # ------------------------------------------------------------------
    # Framework-agnostic routing
    # ------------------------------------------------------------------

    async def route(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any], str]:
        """Route an HTTP-like request to the appropriate handler.

        Returns:
            ``(status_code, headers, json_body_string)``
        """
        method = method.upper()
        path = path.rstrip("/")

        # 1. GET /.well-known/agent.json
        if method == "GET" and path == "/.well-known/agent.json":
            return self._agent_json_response()

        # 2. GET /agent/health
        if method == "GET" and path == "/agent/health":
            return self._health_response()

        # 3. POST /agent/message
        if method == "POST" and path == "/agent/message":
            return await self._handle_message(body)

        # 4. GET /agent/stream (placeholder SSE)
        if method == "GET" and path == "/agent/stream":
            return self._stream_placeholder()

        # ---------------------------------------------------------------
        # Level 2-5 stubs — return 501 Not Implemented (not 404)
        # so clients know the endpoint exists in the spec but isn't
        # available on this server yet.
        # ---------------------------------------------------------------

        # Level 2 — Tools listing
        if path == "/agent/tools":
            return self._level_stub_response(2)

        # Level 3 — Task management
        if path == "/agent/tasks" or path.startswith("/agent/tasks/"):
            return self._level_stub_response(3)

        # Level 4 — Delegation
        if path == "/agent/delegate" or path.startswith("/agent/delegate/"):
            return self._level_stub_response(4)

        # Level 5 — Admin
        if path == "/agent/admin" or path.startswith("/agent/admin/"):
            return self._level_stub_response(5)

        # Everything else → 404
        err = not_found(f"No route for {method} {path}")
        return self._error_response(err)

    # ------------------------------------------------------------------
    # Built-in endpoint handlers
    # ------------------------------------------------------------------

    def _agent_json_response(self) -> tuple[int, dict[str, Any], str]:
        """Return the agent.json document."""
        payload = self.agent_json.model_dump(mode="json")
        return (
            200,
            {"Content-Type": "application/json"},
            json.dumps(payload),
        )

    def _health_response(self) -> tuple[int, dict[str, Any], str]:
        """Return a HealthResponse."""
        uptime = int(time.monotonic() - self._start_time)
        health = HealthResponse(
            status="healthy",
            protocol_version=CURRENT_VERSION,
            uptime_seconds=uptime,
        )
        return (
            200,
            {"Content-Type": "application/json"},
            json.dumps(health.model_dump(mode="json")),
        )

    def _stream_placeholder(self) -> tuple[int, dict[str, Any], str]:
        """Placeholder for SSE streaming endpoint."""
        return (
            200,
            {"Content-Type": "text/event-stream"},
            "event: ping\ndata: {}\n\n",
        )

    def _level_stub_response(self, level: int) -> tuple[int, dict[str, Any], str]:
        """Return 501 Not Implemented for a protocol level 2-5 endpoint.

        This is semantically correct: the endpoint exists in the AMP spec
        but this server has not implemented it yet.  A 404 would wrongly
        imply the endpoint is unknown to the protocol.
        """
        err = not_implemented(
            f"Level {level} endpoint not yet available"
        )
        payload = err.model_dump(mode="json", exclude_none=True)
        payload["protocol_level"] = level
        return (
            501,
            {"Content-Type": "application/problem+json"},
            json.dumps(payload),
        )

    # ------------------------------------------------------------------
    # Message handling pipeline
    # ------------------------------------------------------------------

    async def _handle_message(
        self,
        body: dict[str, Any] | None,
    ) -> tuple[int, dict[str, Any], str]:
        """Process POST /agent/message."""

        # Step 1: Parse body as AgentMessage (Pydantic validation).
        if body is None:
            err = invalid_message("Request body is required")
            return self._error_response(err)

        try:
            msg = AgentMessage.model_validate(body)
        except ValidationError as exc:
            err = invalid_message(f"Invalid envelope: {exc.error_count()} validation error(s)")
            return self._error_response(err)

        # Step 2: Validate body against body_type schema.
        if msg.body is not None and isinstance(msg.body, dict):
            try:
                validate_body(msg.body_type, msg.body)
            except ValidationError as exc:
                err = invalid_message(
                    f"Body validation failed for '{msg.body_type}': "
                    f"{exc.error_count()} error(s)"
                )
                return self._error_response(err)

        # Step 3: Look up handler.
        handler = self._handlers.get(msg.body_type, self._default_handler)
        if handler is None:
            err = not_implemented(
                f"No handler registered for body_type '{msg.body_type}'"
            )
            return self._error_response(err)

        # Step 4: Call handler (supports sync and async).
        try:
            result = handler(msg)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            logger.exception("Handler raised for body_type '%s'", msg.body_type)
            err = internal_error(
                "An unexpected error occurred while processing the request."
            )
            return self._error_response(err)

        # Step 5: Serialize result.
        return self._success_response(result)

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _error_response(
        problem: ProblemDetail,
    ) -> tuple[int, dict[str, Any], str]:
        """Format an RFC 7807 error response."""
        return (
            problem.status,
            {"Content-Type": "application/problem+json"},
            json.dumps(problem.model_dump(mode="json", exclude_none=True)),
        )

    @staticmethod
    def _success_response(
        result: Any,
    ) -> tuple[int, dict[str, Any], str]:
        """Format a 202 Accepted success response."""
        if isinstance(result, AgentMessage):
            payload = result.model_dump(mode="json")
        elif isinstance(result, BaseModel):
            payload = result.model_dump(mode="json")
        elif isinstance(result, dict):
            payload = result
        else:
            payload = {"result": result}

        return (
            202,
            {"Content-Type": "application/json"},
            json.dumps(payload),
        )

    # ------------------------------------------------------------------
    # Server runners (optional — require framework deps)
    # ------------------------------------------------------------------

    def run(self, port: int = 8000, adapter: str = "fastapi") -> None:
        """Start the server using the specified adapter.

        Args:
            port:    TCP port to listen on.
            adapter: ``"fastapi"`` (default) or ``"flask"``.
        """
        if adapter == "fastapi":
            self._run_fastapi(port)
        elif adapter == "flask":
            self._run_flask(port)
        else:
            raise ValueError(f"Unknown adapter '{adapter}'. Use 'fastapi' or 'flask'.")

    def _run_fastapi(self, port: int) -> None:
        """Start with FastAPI + uvicorn."""
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import JSONResponse, PlainTextResponse
            import uvicorn
        except ImportError as exc:
            raise RuntimeError(
                "FastAPI adapter requires 'fastapi' and 'uvicorn'. "
                "Install them: pip install fastapi uvicorn"
            ) from exc

        app = FastAPI(title=f"AMP Agent: {self.agent_id}")

        @app.get("/.well-known/agent.json")
        async def agent_json_endpoint() -> JSONResponse:
            status, headers, body_str = self._agent_json_response()
            return JSONResponse(content=json.loads(body_str), status_code=status)

        @app.get("/agent/health")
        async def health_endpoint() -> JSONResponse:
            status, headers, body_str = self._health_response()
            return JSONResponse(content=json.loads(body_str), status_code=status)

        @app.post("/agent/message")
        async def message_endpoint(request: Request) -> JSONResponse:
            raw = await request.json()
            status, headers, body_str = await self._handle_message(raw)
            return JSONResponse(
                content=json.loads(body_str),
                status_code=status,
                media_type=headers.get("Content-Type", "application/json"),
            )

        @app.get("/agent/stream")
        async def stream_endpoint() -> PlainTextResponse:
            status, headers, body_str = self._stream_placeholder()
            return PlainTextResponse(
                content=body_str,
                status_code=status,
                media_type="text/event-stream",
            )

        uvicorn.run(app, host="0.0.0.0", port=port)

    def _run_flask(self, port: int) -> None:
        """Start with Flask."""
        try:
            from flask import Flask, request as flask_request, jsonify, Response
        except ImportError as exc:
            raise RuntimeError(
                "Flask adapter requires 'flask'. "
                "Install it: pip install flask"
            ) from exc

        app = Flask(__name__)

        @app.route("/.well-known/agent.json", methods=["GET"])
        def agent_json_endpoint():  # type: ignore[no-untyped-def]
            status, headers, body_str = self._agent_json_response()
            return Response(body_str, status=status, content_type=headers["Content-Type"])

        @app.route("/agent/health", methods=["GET"])
        def health_endpoint():  # type: ignore[no-untyped-def]
            status, headers, body_str = self._health_response()
            return Response(body_str, status=status, content_type=headers["Content-Type"])

        @app.route("/agent/message", methods=["POST"])
        def message_endpoint():  # type: ignore[no-untyped-def]
            raw = flask_request.get_json(force=True)
            status, headers, body_str = asyncio.run(self._handle_message(raw))
            return Response(body_str, status=status, content_type=headers["Content-Type"])

        @app.route("/agent/stream", methods=["GET"])
        def stream_endpoint():  # type: ignore[no-untyped-def]
            status, headers, body_str = self._stream_placeholder()
            return Response(body_str, status=status, content_type=headers["Content-Type"])

        app.run(host="0.0.0.0", port=port)
