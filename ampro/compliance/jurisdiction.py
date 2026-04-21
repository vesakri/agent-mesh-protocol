"""
Agent Protocol — Jurisdiction.

Cross-border jurisdiction declaration and conflict detection.

Jurisdiction MUST come from the agent's signed agent.json descriptor,
not from per-message headers.  Per-message ``Jurisdiction`` headers are
informational only and MUST NOT be treated as authoritative.  Platforms
must resolve the agent's agent.json and pass the verified jurisdiction
to these functions.
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
from typing import Any

from pydantic import BaseModel, Field

from ampro.core.envelope import AgentMessage


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


def validate_jurisdiction_source(
    msg: AgentMessage,
    agent_json: dict[str, Any] | None = None,
) -> str | None:
    """Return the *trusted* jurisdiction for the sender of *msg*.

    Jurisdiction MUST come from the agent's signed ``agent.json``
    descriptor, not from per-message headers.  The ``Jurisdiction``
    header in the message is informational only and is deliberately
    **ignored** by this function.

    Args:
        msg: The incoming :class:`AgentMessage`.  Its headers are NOT
            consulted — this is intentional.
        agent_json: The resolved agent descriptor (``agent.json``)
            for the sender.  If it contains a ``jurisdiction`` key the
            value is returned as the authoritative jurisdiction code.

    Returns:
        The jurisdiction code from *agent_json* if available, otherwise
        ``None`` (meaning the caller must apply its own policy, e.g.
        reject or default).
    """
    if agent_json is not None and "jurisdiction" in agent_json:
        return str(agent_json["jurisdiction"])
    return None


def check_jurisdiction_conflict(
    sender: JurisdictionInfo,
    receiver: JurisdictionInfo,
    *,
    trusted_jurisdiction: str | None = None,
) -> tuple[bool, str | None]:
    """Return ``(has_conflict, detail)`` for a sender/receiver pair.

    A conflict exists when the sender declares regulatory frameworks
    that the receiver does not share **and** they operate under
    different primary jurisdictions.  If either condition is not met
    the pair is considered compatible.

    Invalid jurisdiction codes are treated as conflicts (fail-closed).

    Args:
        sender: Jurisdiction info for the sending agent.
        receiver: Jurisdiction info for the receiving agent.
        trusted_jurisdiction: If provided, this cryptographically
            verified jurisdiction code (from the sender's signed
            ``agent.json``) overrides ``sender.primary``.  Platforms
            SHOULD always resolve the agent descriptor and pass the
            result here rather than relying on the ``sender`` model
            which may have been populated from an untrusted header.
    """
    sender_primary = trusted_jurisdiction if trusted_jurisdiction is not None else sender.primary

    if not validate_jurisdiction_code(sender_primary):
        return True, f"Invalid sender jurisdiction code: {sender_primary!r}"
    if not validate_jurisdiction_code(receiver.primary):
        return True, f"Invalid receiver jurisdiction code: {receiver.primary!r}"

    if sender_primary == receiver.primary:
        return False, None

    sender_frameworks = set(sender.frameworks)
    receiver_frameworks = set(receiver.frameworks)

    unmatched = sender_frameworks - receiver_frameworks
    if not unmatched:
        return False, None

    detail = (
        f"Jurisdiction conflict: sender ({sender_primary}) declares "
        f"frameworks {sorted(unmatched)} not recognised by receiver "
        f"({receiver.primary})"
    )
    return True, detail
