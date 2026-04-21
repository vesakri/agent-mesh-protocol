"""
Agent Protocol — Per-Tool Consent.

Fine-grained consent for tool invocation. While capability-level auth
grants access to the 'tools' group, per-tool consent controls which
specific tools can be called and under what constraints.

Tools with consent_required=true MUST NOT be invoked without a valid grant.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Consent request / grant
# ---------------------------------------------------------------------------


class ToolConsentRequestBody(BaseModel):
    """body.type = 'tool.consent.request' — Request consent for a specific tool."""

    tool_name: str = Field(description="Name of the tool requiring consent")
    scopes: list[str] = Field(description="Permission scopes being requested")
    reason: str = Field(description="Human-readable reason for the request")
    session_id: str = Field(description="Session to scope the grant to")
    ttl_seconds: int = Field(
        default=3600,
        description="Requested grant lifetime in seconds",
    )

    model_config = {"extra": "ignore"}


class ToolConsentGrantBody(BaseModel):
    """body.type = 'tool.consent.grant' — Grant consent for a specific tool."""

    tool_name: str = Field(description="Name of the tool consent is granted for")
    scopes: list[str] = Field(
        description="Granted scopes (may be subset of requested)",
    )
    grant_id: str = Field(description="Unique grant identifier")
    valid_for_session: str = Field(
        description="Session ID this grant is scoped to",
    )
    expires_at: str = Field(description="ISO-8601 expiration timestamp")
    restrictions: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional constraints (max_invocations, allowed_params, etc.)",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------


class ToolDefinition(BaseModel):
    """Schema for a single tool exposed by an agent."""

    name: str = Field(description="Tool name")
    description: str = Field(description="Human-readable tool description")
    consent_required: bool = Field(
        default=False,
        description="Whether explicit consent is needed before invocation",
    )
    consent_scopes: list[str] = Field(
        default_factory=list,
        description="Scopes required for this tool",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for tool parameters",
    )
    category: str | None = Field(
        default=None,
        description="Tool category for organization",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Searchable tags",
    )

    model_config = {"extra": "ignore"}
