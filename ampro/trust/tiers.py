"""
Agent Protocol — Trust Tiers.

4 trust tiers that determine which safety checks apply.
The same protocol handles internal AND external communication —
the pipeline adapts based on the relationship between sender and receiver.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class TrustTier(str, Enum):
    """
    Trust relationship between sender and receiver.

    INTERNAL:  Same organization (agent-to-agent within one domain)
    OWNER:     The agent's owner/operator
    VERIFIED:  JWT-authenticated agent (signature verified, not owner)
    EXTERNAL:  Any other interaction (unknown agents, unauthenticated)
    """

    INTERNAL = "internal"
    OWNER = "owner"
    VERIFIED = "verified"
    EXTERNAL = "external"

    @property
    def requires_auth(self) -> bool:
        # VERIFIED has already been authenticated via JWT — no further auth needed.
        return self == TrustTier.EXTERNAL

    @property
    def requires_rate_limit(self) -> bool:
        return self in (TrustTier.VERIFIED, TrustTier.EXTERNAL)

    @property
    def requires_content_filter(self) -> bool:
        return self == TrustTier.EXTERNAL

    @property
    def requires_budget_check(self) -> bool:
        return self in (TrustTier.OWNER, TrustTier.VERIFIED, TrustTier.EXTERNAL)

    @property
    def requires_loop_detection(self) -> bool:
        return self in (TrustTier.VERIFIED, TrustTier.EXTERNAL)

    @property
    def can_delegate(self) -> bool:
        return self in (TrustTier.INTERNAL, TrustTier.OWNER, TrustTier.VERIFIED)


# Clock skew tolerance for cross-platform timestamp comparisons (Section 12.1).
# 60 seconds is intentional for cross-region deployments. Reduce to 10-30s for high-security contexts.
CLOCK_SKEW_SECONDS: int = 60


class TrustConfig(BaseModel):
    """Safety pipeline configuration derived from trust tier."""

    tier: TrustTier
    check_auth: bool = False
    check_rate_limit: bool = False
    check_content_filter: bool = False
    check_budget: bool = False
    check_loop_detection: bool = False
    check_kill_switch: bool = True  # Always checked, even for internal

    model_config = {"extra": "ignore"}

    @classmethod
    def from_tier(cls, tier: TrustTier) -> TrustConfig:
        return cls(
            tier=tier,
            check_auth=tier.requires_auth,
            check_rate_limit=tier.requires_rate_limit,
            check_content_filter=tier.requires_content_filter,
            check_budget=tier.requires_budget_check,
            check_loop_detection=tier.requires_loop_detection,
        )
