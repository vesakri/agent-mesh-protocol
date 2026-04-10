"""
Agent Protocol — Registry Search.

Structured service discovery for finding agents by capability and trust
criteria. Any registry implementing GET /registry/search returns results
in this format.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RegistrySearchRequest(BaseModel):
    """Query parameters for GET /registry/search."""

    capability: str = Field(description="Capability to search for")
    min_trust_score: int | None = Field(
        default=None,
        description="Minimum trust score (0-1000)",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum matches to return",
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

    model_config = {"extra": "ignore"}
