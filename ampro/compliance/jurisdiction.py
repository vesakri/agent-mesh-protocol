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
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from ampro.core.envelope import AgentMessage


class JurisdictionInfo(BaseModel):
    """Jurisdiction declaration for an agent.

    Field ordering rule: the ``primary`` jurisdiction's rules take
    precedence for all data the agent handles.  Jurisdictions listed
    in ``additional`` apply only to data that originated in, or is
    stored in, those regions.  Implementations SHOULD apply the
    strictest set of rules when operating in additional jurisdictions
    (see :func:`applicable_rules`).
    """

    primary: str = Field(description="ISO 3166-1 alpha-2 country code")
    additional: list[str] = Field(
        default_factory=list,
        description=(
            "Additional jurisdictions that apply only to data originated "
            "in or stored in those regions. Primary always takes precedence."
        ),
    )
    frameworks: list[str] = Field(
        default_factory=list,
        description="Applicable regulatory frameworks (e.g. GDPR, CCPA, PIPL)",
    )

    model_config = {"extra": "ignore"}


class TransferMechanism(str, Enum):
    """Legal basis for cross-border data transfers.

    Reflects the mechanisms recognised by GDPR Chapter V and
    analogous regulations (PIPL, LGPD, etc.).
    """

    ADEQUACY = "adequacy"      # e.g. GDPR adequacy decision
    BCR = "bcr"                # Binding Corporate Rules
    SCC = "scc"                # Standard Contractual Clauses
    DEROGATION = "derogation"  # Article 49 GDPR derogations
    NONE = "none"              # no mechanism -> block transfer


class AdequacyDecision(BaseModel):
    """A registered cross-border transfer mechanism between two jurisdictions."""

    from_jurisdiction: str = Field(description="ISO 3166-1 alpha-2 source country code")
    to_jurisdiction: str = Field(description="ISO 3166-1 alpha-2 destination country code")
    mechanism: TransferMechanism = Field(description="Legal basis for the transfer")
    expires_at: datetime | None = Field(
        default=None,
        description="UTC expiry timestamp; adequacy decisions commonly have a review date",
    )

    model_config = {"extra": "ignore"}


class TransferDecision(str, Enum):
    """Outcome of a cross-border transfer check."""

    ALLOWED = "allowed"
    WARNING = "warning"
    BLOCKED = "blocked"


@runtime_checkable
class AdequacyRegistry(Protocol):
    """Pluggable lookup for registered adequacy decisions / BCR / SCC entries."""

    def lookup(
        self, from_jurisdiction: str, to_jurisdiction: str
    ) -> AdequacyDecision | None: ...


class NoOpAdequacyRegistry:
    """Default registry that rejects all cross-border transfers.

    Host platforms SHOULD register a concrete implementation backed
    by a policy store (legal registry, contract database, etc.).
    """

    def lookup(
        self, from_jurisdiction: str, to_jurisdiction: str
    ) -> AdequacyDecision | None:
        return None


_adequacy_registry: AdequacyRegistry = NoOpAdequacyRegistry()


def register_adequacy_registry(registry: AdequacyRegistry) -> None:
    """Install a concrete :class:`AdequacyRegistry` implementation."""
    global _adequacy_registry
    _adequacy_registry = registry


def get_adequacy_registry() -> AdequacyRegistry:
    """Return the currently-registered :class:`AdequacyRegistry`."""
    return _adequacy_registry


def applicable_rules(
    jurisdiction_info: JurisdictionInfo,
    data_region: str,
) -> list[str]:
    """Return the ordered list of jurisdictions whose rules apply to *data_region*.

    Field ordering rule (see :class:`JurisdictionInfo`):

    * If ``data_region == primary`` -> ``[primary]``
    * Elif ``data_region in additional`` -> ``[data_region, primary]``
      (strictest applies; both listed so callers can compute the union)
    * Else -> ``[primary]``  (default to primary)

    This is a protocol-level guideline, not an enforcement mechanism.
    Implementations SHOULD apply the strictest set of rules when
    operating in additional jurisdictions.
    """
    if data_region == jurisdiction_info.primary:
        return [jurisdiction_info.primary]
    if data_region in jurisdiction_info.additional:
        return [data_region, jurisdiction_info.primary]
    return [jurisdiction_info.primary]


def check_cross_border_transfer(
    sender: JurisdictionInfo,
    receiver: JurisdictionInfo,
    adequacy_registry: AdequacyRegistry | None = None,
    *,
    now: datetime | None = None,
) -> tuple[TransferDecision, str | None]:
    """Evaluate a cross-border data transfer between two agents.

    Returns ``(decision, detail)`` where ``decision`` is one of:

    * :attr:`TransferDecision.ALLOWED` — same jurisdiction, or a valid
      non-expired :class:`AdequacyDecision` exists.
    * :attr:`TransferDecision.WARNING` — a mechanism exists but has
      expired; callers SHOULD surface this for renewal.
    * :attr:`TransferDecision.BLOCKED` — no mechanism registered, or
      the registered mechanism is explicitly
      :attr:`TransferMechanism.NONE`.

    Args:
        sender: Sending agent's jurisdiction info.
        receiver: Receiving agent's jurisdiction info.
        adequacy_registry: Optional registry override; defaults to the
            process-wide registry installed via
            :func:`register_adequacy_registry`.
        now: Optional clock override for testing.
    """
    if sender.primary == receiver.primary:
        return TransferDecision.ALLOWED, None

    registry = adequacy_registry if adequacy_registry is not None else _adequacy_registry
    decision = registry.lookup(sender.primary, receiver.primary)

    if decision is None:
        return TransferDecision.BLOCKED, (
            f"No adequacy decision registered for "
            f"{sender.primary} -> {receiver.primary}"
        )

    if decision.mechanism == TransferMechanism.NONE:
        return TransferDecision.BLOCKED, (
            f"Transfer mechanism explicitly NONE for "
            f"{sender.primary} -> {receiver.primary}"
        )

    if decision.expires_at is not None:
        current = now if now is not None else datetime.now(UTC)
        # Normalise naive expiries to UTC for comparison.
        expires = decision.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires <= current:
            return TransferDecision.WARNING, (
                f"Transfer mechanism '{decision.mechanism.value}' expired at "
                f"{expires.isoformat()} for {sender.primary} -> {receiver.primary}"
            )

    return TransferDecision.ALLOWED, None


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
