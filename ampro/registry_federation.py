"""
Agent Protocol — Registry Federation.

Inter-registry trust establishment. Two registries negotiate mutual
trust so agents registered in one can be discovered through the other.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RegistryFederationRequest(BaseModel):
    """Request to establish federation between two registries."""

    registry_id: str = Field(description="agent:// URI of the requesting registry")
    capabilities: list[str] = Field(
        description="Capabilities offered (resolve, search, presence)",
    )
    trust_proof: str = Field(description="Signed proof of registry identity")

    model_config = {"extra": "ignore"}


class RegistryFederationResponse(BaseModel):
    """Response to a registry federation request."""

    accepted: bool = Field(description="Whether federation was accepted")
    federation_id: str | None = Field(
        default=None,
        description="Unique federation ID (required when accepted)",
    )
    terms: dict[str, Any] = Field(
        default_factory=dict,
        description="Federation terms (rate limits, retention, etc.)",
    )

    model_config = {"extra": "ignore"}
