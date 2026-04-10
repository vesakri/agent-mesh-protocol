"""
Agent Protocol — agent.json Schema.

The complete schema for /.well-known/agent.json as defined in the spec.
Used for validation when fetching and serving agent.json.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentJson(BaseModel):
    """Complete agent.json schema per protocol spec Section 1.5."""

    protocol_version: str = Field(description="Protocol version (e.g. '1.0.0')")
    identifiers: list[str] = Field(description="All agent:// URIs for this agent")
    endpoint: str = Field(description="HTTPS endpoint for POST /agent/message")
    jwks_url: str | None = Field(default=None, description="JWKS endpoint URL")
    capabilities: dict[str, Any] = Field(
        default_factory=lambda: {"groups": [], "level": 0}
    )
    constraints: dict[str, Any] = Field(default_factory=dict)
    security: dict[str, Any] = Field(default_factory=dict)
    billing: dict[str, Any] = Field(default_factory=dict)
    streaming: dict[str, Any] = Field(default_factory=dict)
    compliance: dict[str, Any] = Field(default_factory=dict)
    languages: list[str] = Field(default_factory=list)
    ttl_seconds: int = Field(default=3600, ge=1)
    # v0.1.1 — Visibility & context schemas
    visibility: dict[str, Any] = Field(
        default_factory=lambda: {"level": "public", "contact_policy": "open"},
        description="Visibility and contact policy configuration",
    )
    supported_schemas: list[str] = Field(
        default_factory=list,
        description="Context schema URNs this agent understands (e.g. urn:schema:purchase-order:v1)",
    )

    # v0.1.3 — Agent lifecycle
    status: str = Field(
        default="active",
        description="Agent lifecycle status: active, deactivating, or decommissioned",
    )
    # v0.1.8 — Identity migration
    moved_to: str | None = Field(
        default=None,
        description="agent:// URI this agent has migrated to. "
        "Consumers MUST validate this is a valid agent:// URI before following.",
    )
    # v0.1.9 — Certifications
    certifications: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Compliance certifications (SOC2, ISO27001, etc.)",
    )

    model_config = {"extra": "allow"}
