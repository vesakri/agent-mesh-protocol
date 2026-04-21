"""
Agent Protocol — Registry Search.

Structured service discovery for finding agents by capability and trust
criteria. Any registry implementing GET /registry/search returns results
in this format.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class RegistrySearchRequest(BaseModel):
    """Query parameters for GET /registry/search.

    Cursor-based pagination (issue #42): callers page by passing the
    ``next_cursor`` returned by a previous :class:`RegistrySearchResult`
    into ``cursor`` on the next request. ``max_results`` is retained as a
    deprecated alias for ``limit``.
    """

    capability: str = Field(description="Capability to search for")
    min_trust_score: int | None = Field(
        default=None,
        description="Minimum trust score (0-1000)",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum matches to return per page",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque cursor from previous response",
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Additional filter criteria",
    )
    include_load_level: bool = Field(
        default=True,
        description="Include current load level in results",
    )

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _coerce_deprecated_max_results(cls, values: Any) -> Any:
        """Backwards-compat: copy ``max_results`` into ``limit`` if ``limit`` absent."""
        if not isinstance(values, dict):
            return values
        if "max_results" in values and "limit" not in values:
            values["limit"] = values["max_results"]
        return values

    @property
    def max_results(self) -> int:
        """Deprecated alias for :attr:`limit`."""
        return self.limit


class RegistrySearchMatch(BaseModel):
    """A single agent matching a registry search query."""

    agent_id: str = Field(description="Canonical agent:// URI")
    endpoint: str = Field(description="HTTPS endpoint for /agent/message")
    capabilities: list[str] = Field(
        description="Capability groups the agent supports",
    )
    trust_score: int = Field(description="Current trust score (0-1000)")
    trust_tier: str = Field(description="Trust tier")
    load_level: int | None = Field(
        default=None,
        description="Current load percentage (0-100)",
    )
    status: str = Field(default="active", description="Lifecycle status")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional agent metadata",
    )

    model_config = {"extra": "ignore"}


class RegistrySearchResult(BaseModel):
    """Response envelope for GET /registry/search."""

    matches: list[RegistrySearchMatch] = Field(
        default_factory=list,
        description="Ranked list of matching agents",
    )
    total_available: int = Field(
        default=0,
        description="Total matching agents (may exceed max_results)",
    )
    search_time_ms: float = Field(
        default=0.0,
        description="Search execution time in milliseconds",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor to pass as ``cursor`` on the next request",
    )
    has_more: bool = Field(
        default=False,
        description="True when more results are available beyond this page",
    )

    model_config = {"extra": "ignore"}


# Back-compat export: some callers import ``RegistrySearchResponse``.
RegistrySearchResponse = RegistrySearchResult
