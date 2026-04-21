"""AMPI type definitions — handler, middleware, server protocol."""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypedDict,
    Union,
    runtime_checkable,
)

from ampro.core.envelope import AgentMessage
from ampro.streaming.events import StreamingEvent

# AMPContext may not exist yet (created by a parallel task).
# Under ``TYPE_CHECKING`` pyright / mypy always resolve the real class;
# at runtime we fall back to ``Any`` so the module loads regardless.
# Annotations use ``"AMPContext"`` string form so the name never has to
# resolve at runtime (PEP 563 is on via ``from __future__ import
# annotations`` at the top of this file).
if TYPE_CHECKING:
    from ampro.ampi.context import AMPContext
else:
    try:
        from ampro.ampi.context import AMPContext  # noqa: F401 — re-exported via __all__
    except ImportError:  # pragma: no cover — only while context.py is absent
        AMPContext = Any  # type: ignore[assignment,misc]


HandlerResult = Union[AgentMessage, dict, None]
HandlerFunc = Callable[[AgentMessage, AMPContext], Awaitable[HandlerResult]]
StreamingHandlerFunc = Callable[[AgentMessage, AMPContext], AsyncIterator[StreamingEvent]]

NextFunc = Callable[[AgentMessage, AMPContext], Awaitable[HandlerResult]]
MiddlewareFunc = Callable[[AgentMessage, AMPContext, NextFunc], Awaitable[HandlerResult]]


class AMPIApp(TypedDict, total=False):
    """Dict-based AMPI application (AgentApp alternative)."""

    agent_id: str
    endpoint: str
    handlers: dict[str, HandlerFunc | StreamingHandlerFunc]
    tools: dict[str, Callable]
    middleware: list[MiddlewareFunc]
    error_handler: Callable | None
    startup: list[Callable]
    shutdown: list[Callable]


@runtime_checkable
class AMPIServer(Protocol):
    """The AMPI server contract."""

    def __init__(self, app: Any) -> None: ...

    async def dispatch(
        self,
        message: AgentMessage,
        ctx: AMPContext,
    ) -> HandlerResult | AsyncIterator[StreamingEvent]: ...
