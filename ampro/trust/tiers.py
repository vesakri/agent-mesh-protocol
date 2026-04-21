"""
Agent Protocol — Trust Tiers.

4 trust tiers that determine which safety checks apply.
The same protocol handles internal AND external communication —
the pipeline adapts based on the relationship between sender and receiver.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


_TIER_ORDER: dict[str, int] = {
    "external": 0,
    "verified": 1,
    "owner": 2,
    "internal": 3,
}


class TrustTier(str, Enum):
    """
    Trust relationship between sender and receiver.

    INTERNAL:  Same organization (agent-to-agent within one domain)
    OWNER:     The agent's owner/operator
    VERIFIED:  JWT-authenticated agent (signature verified, not owner)
    EXTERNAL:  Any other interaction (unknown agents, unauthenticated)

    Ordered: EXTERNAL < VERIFIED < OWNER < INTERNAL.
    Comparison operators use ``_TIER_ORDER`` so callers can write
    ``if tier > TrustTier.EXTERNAL`` without a TypeError.
    """

    INTERNAL = "internal"
    OWNER = "owner"
    VERIFIED = "verified"
    EXTERNAL = "external"

    # -- Ordering operators ---------------------------------------------------

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TrustTier):
            return NotImplemented
        return _TIER_ORDER[self.value] < _TIER_ORDER[other.value]

    def __le__(self, other: object) -> bool:
        if not isinstance(other, TrustTier):
            return NotImplemented
        return _TIER_ORDER[self.value] <= _TIER_ORDER[other.value]

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, TrustTier):
            return NotImplemented
        return _TIER_ORDER[self.value] > _TIER_ORDER[other.value]

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, TrustTier):
            return NotImplemented
        return _TIER_ORDER[self.value] >= _TIER_ORDER[other.value]

    # -- Safety-check helpers -------------------------------------------------

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
# 30 seconds balances cross-region clock drift with security (narrower replay window).
CLOCK_SKEW_SECONDS: int = 30


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
