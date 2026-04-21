"""
Agent Protocol — Data Residency.

Declares where data must reside. Agents declare residency requirements
via the Data-Residency header. Tasks that would violate residency
constraints are rejected with reason 'residency_violation'.

PURE — zero platform-specific imports. Only pydantic, re, and stdlib.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

import re

from pydantic import BaseModel, Field

_REGION_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,28}[a-z0-9]")


class DataResidency(BaseModel):
    """Residency constraint attached to a message or agent."""

    region: str = Field(
        description="Data residency region identifier (e.g. eu-west-1, us-east-1)",
    )
    strict: bool = Field(
        default=True,
        description="When True, data MUST NOT leave the region",
    )
    allowed_regions: list[str] = Field(
        default_factory=list,
        description="Additional regions where data may be stored (when strict=False)",
    )

    model_config = {"extra": "ignore"}


def validate_residency_region(region: str) -> bool:
    """Return *True* if *region* is a valid residency region identifier.

    Format: lowercase alphanumeric + hyphens, 3-30 characters,
    must start and end with an alphanumeric character.
    """
    return _REGION_RE.fullmatch(region) is not None


def check_residency_violation(
    message_residency: DataResidency,
    agent_residency: DataResidency,
) -> tuple[bool, str | None]:
    """Check whether an agent may handle a message given residency constraints.

    Returns ``(has_violation, detail)``.  When *has_violation* is ``False``,
    *detail* is ``None``.
    """
    if agent_residency.region == message_residency.region:
        return False, None

    if message_residency.strict:
        return True, (
            f"strict residency: message requires '{message_residency.region}' "
            f"but agent is in '{agent_residency.region}'"
        )

    if agent_residency.region not in message_residency.allowed_regions:
        return True, (
            f"residency violation: agent region '{agent_residency.region}' "
            f"is not in allowed_regions {message_residency.allowed_regions} "
            f"for message region '{message_residency.region}'"
        )

    return False, None
