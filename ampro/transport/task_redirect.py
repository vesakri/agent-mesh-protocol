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

    model_config = {"extra": "ignore"}
