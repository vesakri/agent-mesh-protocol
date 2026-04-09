"""
Agent Protocol — Consent Revocation.

Revoke previously granted consent. Supports full revocation (all scopes)
or partial revocation (specific scopes only). Revocation can be immediate
or scheduled for a future time.

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DataConsentRevokeBody(BaseModel):
    """body.type = 'data.consent.revoke' — Revoke a consent grant."""

    grant_id: str = Field(description="ID of the consent grant being revoked")
    requester: str = Field(description="Agent requesting the revocation")
    target: str = Field(description="Agent whose consent grant is being revoked")
    scopes: list[str] = Field(
        default_factory=list,
        description="Scopes to revoke (empty = revoke all)",
    )
    reason: str = Field(description="Human-readable reason for revocation")
    effective_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when revocation takes effect; None = immediate",
    )

    model_config = {"extra": "ignore"}
