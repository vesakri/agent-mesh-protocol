"""
Agent Protocol — Task Redirect.

Load-aware routing primitive. When an agent is overloaded or not the
best fit for a task, it responds with task.redirect pointing the caller
to a more appropriate agent.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

from pydantic import BaseModel, Field

from ampro.errors import RedirectLoopError


class TaskRedirectBody(BaseModel):
    """body.type = 'task.redirect' — Redirect a task to another agent."""

    task_id: str = Field(description="ID of the task being redirected")
    redirect_to: str = Field(
        description="agent:// URI of the suggested target agent",
    )
    reason: str = Field(
        description=(
            "Why the redirect is happening "
            "(e.g. overloaded, capability_mismatch, maintenance)"
        ),
    )
    original_description: str | None = Field(
        default=None,
        description="Original task description for forwarding",
    )
    load_level: int | None = Field(
        default=None,
        description="Redirecting agent's current load (0-100)",
    )
    alternative_agents: list[str] | None = Field(
        default=None,
        description="Additional agent URIs the caller could try",
    )
    retry_after_seconds: int | None = Field(
        default=None,
        description="When the agent expects to be available again",
    )
    visited_agents: list[str] = Field(
        default_factory=list,
        max_length=10,
        description=(
            "Chain of agent:// URIs that have already processed this "
            "redirect, used to detect cycles"
        ),
    )
    max_hops: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum allowed redirect chain length before a loop error is raised",
    )

    model_config = {"extra": "ignore"}


def check_redirect_chain(body: TaskRedirectBody, current_agent_id: str) -> None:
    """Validate that following this redirect would not loop or exceed ``max_hops``.

    Callers MUST invoke this before following a ``task.redirect`` so that
    malicious or misconfigured agents cannot trap callers in a redirect
    cycle or force an unbounded redirect chain.

    Raises:
        RedirectLoopError: when ``current_agent_id`` already appears in
            ``visited_agents`` (cycle detected) or when ``len(visited_agents)``
            has reached ``max_hops``.
    """
    if current_agent_id in body.visited_agents:
        raise RedirectLoopError(
            f"Redirect cycle detected: agent {current_agent_id!r} already "
            f"appears in visited_agents={body.visited_agents}"
        )
    if len(body.visited_agents) >= body.max_hops:
        raise RedirectLoopError(
            f"Redirect chain exceeded max_hops={body.max_hops}: "
            f"visited={body.visited_agents}"
        )
