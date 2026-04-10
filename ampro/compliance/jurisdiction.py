"""
Agent Protocol — Jurisdiction.

Cross-border jurisdiction declaration and conflict detection.
Agents declare their jurisdiction via the Jurisdiction header
and can detect conflicts when sender and receiver operate under
incompatible regulatory frameworks.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field


class JurisdictionInfo(BaseModel):
    """Jurisdiction declaration for an agent."""

    primary: str = Field(description="ISO 3166-1 alpha-2 country code")
    additional: list[str] = Field(
        default_factory=list,
        description="Additional jurisdictions that apply",
    )
    frameworks: list[str] = Field(
        default_factory=list,
        description="Applicable regulatory frameworks (e.g. GDPR, CCPA, PIPL)",
    )

    model_config = {"extra": "ignore"}


def validate_jurisdiction_code(code: str) -> bool:
    """Validate that *code* is exactly two uppercase ASCII letters."""
    return re.fullmatch(r"[A-Z]{2}", code) is not None


def check_jurisdiction_conflict(
    sender: JurisdictionInfo,
    receiver: JurisdictionInfo,
) -> tuple[bool, str | None]:
    """Return ``(has_conflict, detail)`` for a sender/receiver pair.

    A conflict exists when the sender declares regulatory frameworks
    that the receiver does not share **and** they operate under
    different primary jurisdictions.  If either condition is not met
    the pair is considered compatible.
    """
    if sender.primary == receiver.primary:
        return False, None

    sender_frameworks = set(sender.frameworks)
    receiver_frameworks = set(receiver.frameworks)

    unmatched = sender_frameworks - receiver_frameworks
    if not unmatched:
        return False, None

    detail = (
        f"Jurisdiction conflict: sender ({sender.primary}) declares "
        f"frameworks {sorted(unmatched)} not recognised by receiver "
        f"({receiver.primary})"
    )
    return True, detail
