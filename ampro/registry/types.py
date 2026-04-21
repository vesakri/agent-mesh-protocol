"""
Agent Protocol — Registry Types.

Models for the registry resolution and registration contract.
Any HTTP server implementing these becomes a valid agent registry.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class RegistryResolution(BaseModel):
    """Response from GET /agent/resolve/{slug}."""

    agent_uri: str = Field(description="Canonical agent:// URI")
    endpoint: str = Field(
        description="HTTPS endpoint for /agent/message. "
        "Consumers MUST validate this is HTTPS before connecting.",
    )
    agent_json_url: str = Field(default="", description="URL to fetch agent.json")
    ttl_seconds: int = Field(default=3600, ge=1)
    # v0.1.3 — Agent lifecycle
    status: str = Field(default="active", description="Agent lifecycle status")
    gone: bool = Field(default=False, description="True when registry returns 410 Gone for decommissioned agents")

    model_config = {"extra": "ignore"}


_SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


class RegistryRegistration(BaseModel):
    """Request body for POST /agent/register."""

    slug: str = Field(
        min_length=3,
        max_length=30,
        description="Desired slug name (3-30 lowercase alphanumeric chars and hyphens, "
        "no consecutive hyphens, cannot start/end with hyphen)",
    )
    endpoint: str = Field(description="Agent's HTTPS endpoint")
    public_key: str = Field(description="Base64-encoded Ed25519 public key")
    proof: str = Field(description="Signed challenge for ownership verification")

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str) -> str:
        """Enforce slug format: lowercase alphanumeric + hyphens, no consecutive hyphens."""
        if "--" in v:
            raise ValueError(
                "Slug must not contain consecutive hyphens"
            )
        if not _SLUG_RE.match(v):
            raise ValueError(
                "Slug must contain only lowercase alphanumeric characters and hyphens, "
                "and cannot start or end with a hyphen"
            )
        return v

    model_config = {"extra": "ignore"}
