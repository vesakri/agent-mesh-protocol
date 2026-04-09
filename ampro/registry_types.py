"""
Agent Protocol — Registry Types.

Models for the registry resolution and registration contract.
Any HTTP server implementing these becomes a valid agent registry.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class RegistryResolution(BaseModel):
    """Response from GET /agent/resolve/{slug}."""

    agent_uri: str = Field(description="Canonical agent:// URI")
    endpoint: str = Field(description="HTTPS endpoint for /agent/message")
    agent_json_url: str = Field(default="", description="URL to fetch agent.json")
    ttl_seconds: int = Field(default=3600, ge=1)

    model_config = {"extra": "ignore"}


class RegistryRegistration(BaseModel):
    """Request body for POST /agent/register."""

    slug: str = Field(description="Desired slug name")
    endpoint: str = Field(description="Agent's HTTPS endpoint")
    public_key: str = Field(description="Base64-encoded Ed25519 public key")
    proof: str = Field(description="Signed challenge for ownership verification")

    model_config = {"extra": "ignore"}
