"""
Agent Protocol — Trust Upgrade.

Mid-conversation identity verification. Allows an agent to request
that the sender prove their identity to a higher trust tier without
restarting the session.

Flow:
  1. Agent sends trust.upgrade_request with required tier and accepted methods
  2. Sender provides proof via trust.upgrade_response
  3. Session continues with elevated trust tier
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrustUpgradeRequestBody(BaseModel):
    """body.type = 'trust.upgrade_request' — Request a trust tier upgrade."""

    session_id: str = Field(description="Session requiring the trust upgrade")
    current_tier: str = Field(description="Sender's current trust tier. Must be one of: internal, owner, verified, external")
    required_tier: str = Field(description="Trust tier needed to proceed. Must be one of: internal, owner, verified, external")
    verification_methods: list[str] = Field(
        description="Accepted verification methods (e.g. ['jwt', 'did:web', 'oauth2'])",
    )
    verification_url: str | None = Field(
        default=None,
        description="Optional URL for out-of-band verification",
    )
    reason: str = Field(description="Human-readable reason for the upgrade request")
    timeout_seconds: int = Field(
        default=300,
        description="How long to wait for verification",
    )

    model_config = {"extra": "ignore"}


class TrustUpgradeResponseBody(BaseModel):
    """body.type = 'trust.upgrade_response' — Respond with identity proof."""

    session_id: str = Field(description="Session the upgrade applies to")
    method: str = Field(description="Verification method used")
    proof: str = Field(description="The identity proof (JWT, DID proof, etc.)")
    new_tier: str = Field(description="Resulting trust tier after verification. Must be one of: internal, owner, verified, external")
    new_score: int | None = Field(
        default=None,
        description="Updated trust score, if available",
    )

    model_config = {"extra": "ignore"}
