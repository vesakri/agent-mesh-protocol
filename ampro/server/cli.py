"""ampro-server CLI — run any AMPI agent.

Usage::
    ampro-server main:agent --port 8000
    python -m ampro.server main:agent --port 8000
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

import argparse
import importlib
import sys


def _parse_app_string(app_str: str) -> tuple[str, str]:
    """Parse 'module:attribute' string. Default attribute is 'agent'."""
    if ":" in app_str:
        module, attr = app_str.rsplit(":", 1)
    else:
        module, attr = app_str, "agent"
    return module, attr


def _load_app(app_str: str):
    """Import module and return the app object."""
    module_name, attr_name = _parse_app_string(app_str)
    if "." not in sys.path:
        sys.path.insert(0, ".")
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ampro-server",
        description="Run an AMP agent via AMPI.",
    )
    parser.add_argument("app", help="App to run, e.g. 'main:agent'")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args(argv)
    app = _load_app(args.app)

    agent_id = getattr(app, "agent_id", "unknown")
    print(f"\n  AMP agent running on http://{args.host}:{args.port}")
    print(f"  Agent ID:  {agent_id}")
    print(f"  Endpoints:")
    print(f"    GET  /.well-known/agent.json")
    print(f"    GET  /agent/health")
    print(f"    POST /agent/message")
    print(f"    GET  /agent/stream")
    print()

    from ampro.server.core import AgentServer
    if hasattr(app, "handlers"):
        server = AgentServer(
            agent_id=app.agent_id,
            endpoint=app.endpoint,
            agent_json=getattr(app, "agent_json", None),
        )
        for body_type, handler in app.handlers.items():
            server._handlers[body_type] = handler
    else:
        server = app
    server.run(port=args.port)
