"""
Agent Protocol — Trust Score.

Numeric reputation scoring (0-1000) built from five independent factors,
each contributing up to 200 points:

  AGE               — How long the agent has existed
  TRACK_RECORD      — Number of successful interactions
  CLEAN_HISTORY     — Absence of incidents (penalty-based)
  ENDORSEMENTS      — Peer endorsements received
  IDENTITY_STRENGTH — Cryptographic identity method strength

The total score maps to a trust tier that determines what
safety checks and rate limits apply.

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TrustFactor(str, Enum):
    """The five independent factors that contribute to a trust score."""

    AGE = "age"
    TRACK_RECORD = "track_record"
    CLEAN_HISTORY = "clean_history"
    ENDORSEMENTS = "endorsements"
    IDENTITY_STRENGTH = "identity_strength"


class TrustScore(BaseModel):
    """
    Computed trust score for an agent.

    The score is the sum of five factors (each 0-200), giving a
    range of 0-1000.  The tier is derived from the total score.
    """

    tier: str = Field(description="Trust tier: internal, owner, verified, or external")
    score: int = Field(ge=0, le=1000, description="Aggregate trust score (0-1000)")
    factors: dict[str, int] = Field(
        description="Per-factor scores keyed by TrustFactor value (each 0-200)",
    )

    model_config = {"extra": "ignore"}

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        valid = {"internal", "owner", "verified", "external"}
        if v not in valid:
            raise ValueError(f"tier must be one of {valid}, got {v!r}")
        return v

    @field_validator("factors")
    @classmethod
    def validate_factors(cls, v: dict[str, int]) -> dict[str, int]:
        for key, val in v.items():
            if val < 0 or val > 200:
                raise ValueError(f"Factor {key!r} must be 0-200, got {val}")
        return v


class TrustPolicy(BaseModel):
    """Rate-limit and content-filter policy derived from a trust score."""

    rate_limit_per_minute: int = Field(description="Maximum requests per minute")
    content_filter_enabled: bool = Field(description="Whether content filtering is active")

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Identity-method strength lookup
#
# Maps identity verification methods to their score contribution (0-200).
# Higher scores reflect stronger cryptographic guarantees.
# Override by subclassing TrustScore or providing a custom scoring function.
# ---------------------------------------------------------------------------

_IDENTITY_SCORES: dict[str, int] = {
    "did:key": 50,
    "did:web": 100,
    "jwt": 150,
    "mtls": 200,
}

# Fallback score for unrecognised identity methods.
_DEFAULT_IDENTITY_SCORE: int = 25


def calculate_trust_score(
    age_days: int,
    interactions: int,
    incidents: int,
    endorsements: int,
    identity_type: str,
) -> TrustScore:
    """
    Calculate a :class:`TrustScore` from five input signals.

    Each factor contributes 0-200 points toward a maximum of 1000.
    The resulting tier is derived from the total:

    * 800+ → ``"internal"``
    * 400-799 → ``"verified"``
    * 100-399 → ``"external"``
    * 0-99 → ``"external"``

    Note: This function never produces the ``"owner"`` tier.  Owner status
    is determined by the trust resolver (e.g. based on agent registration
    metadata), not by the numeric score.  The ``"owner"`` tier is still
    valid per :class:`TrustScore` and ``trust/tiers.py``.
    """

    factors: dict[str, int] = {
        TrustFactor.AGE.value: max(0, min(200, age_days * 200 // 365)),
        TrustFactor.TRACK_RECORD.value: max(0, min(200, interactions * 200 // 1000)),
        TrustFactor.CLEAN_HISTORY.value: max(0, 200 - incidents * 50),
        TrustFactor.ENDORSEMENTS.value: max(0, min(200, endorsements * 40)),
        TrustFactor.IDENTITY_STRENGTH.value: _IDENTITY_SCORES.get(
            identity_type, _DEFAULT_IDENTITY_SCORE,
        ),
    }

    total = sum(factors.values())

    if total >= 800:
        tier = "internal"
    elif total >= 400:
        tier = "verified"
    else:
        tier = "external"

    return TrustScore(tier=tier, score=total, factors=factors)


def score_to_policy(score: int) -> TrustPolicy:
    """
    Map a numeric trust score to a :class:`TrustPolicy`.

    Higher scores receive more generous rate limits and may
    bypass content filtering.
    """

    if score >= 800:
        return TrustPolicy(rate_limit_per_minute=1000, content_filter_enabled=False)
    if score >= 400:
        return TrustPolicy(rate_limit_per_minute=100, content_filter_enabled=False)
    if score >= 100:
        return TrustPolicy(rate_limit_per_minute=10, content_filter_enabled=True)
    return TrustPolicy(rate_limit_per_minute=1, content_filter_enabled=True)
