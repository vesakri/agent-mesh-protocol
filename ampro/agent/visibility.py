"""
Agent Protocol — Visibility & Contact Policies.

Controls how agents are discovered, listed, and contacted.

Four visibility levels govern what callers can see:
  - PUBLIC       → Full agent.json to everyone.
  - AUTHENTICATED → Full details to verified callers; stub to others.
  - PRIVATE      → Full details to internal/owner only; 401 to others.
  - HIDDEN       → Full details to internal/owner only; 404 to others.

Five contact policies govern who may initiate a conversation:
  - OPEN             → Anyone can send a message.
  - HANDSHAKE_REQUIRED → Anyone can start, but handshake must complete first.
  - VERIFIED_ONLY    → Only internal, owner, or verified senders.
  - DELEGATION_ONLY  → Only internal or owner (via delegation chain).
  - EXPLICIT_INVITE  → No unsolicited contact; must be on an allowlist.

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

import copy
from enum import Enum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class VisibilityLevel(str, Enum):
    """How much of an agent's metadata is exposed to callers."""

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    PRIVATE = "private"
    HIDDEN = "hidden"


class ContactPolicy(str, Enum):
    """Who is allowed to initiate contact with an agent."""

    OPEN = "open"
    HANDSHAKE_REQUIRED = "handshake_required"
    VERIFIED_ONLY = "verified_only"
    DELEGATION_ONLY = "delegation_only"
    EXPLICIT_INVITE = "explicit_invite"


# ---------------------------------------------------------------------------
# Config model
# ---------------------------------------------------------------------------


class VisibilityConfig(BaseModel):
    """Visibility and contact configuration for an agent."""

    level: VisibilityLevel = Field(
        default=VisibilityLevel.PUBLIC,
        description="How much of the agent's metadata is exposed to callers",
    )
    contact_policy: ContactPolicy = Field(
        default=ContactPolicy.OPEN,
        description="Who is allowed to initiate contact with this agent",
    )
    listed_in_registries: bool = Field(
        default=True,
        description="Whether the agent appears in registry listings",
    )
    searchable: bool = Field(
        default=True,
        description="Whether the agent is returned in search results",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Contact check
# ---------------------------------------------------------------------------

_VERIFIED_TIERS = frozenset({"internal", "owner", "verified"})
_INTERNAL_TIERS = frozenset({"internal", "owner"})


def check_contact_allowed(
    sender_tier: str,
    contact_policy: ContactPolicy,
) -> bool:
    """Return whether *sender_tier* is allowed to contact under *contact_policy*.

    This is a type-level gate.  Runtime concerns (e.g. whether a
    handshake was actually completed, or whether the sender is on an
    explicit invite list) are enforced elsewhere.

    Rules
    -----
    - OPEN              → always ``True``
    - HANDSHAKE_REQUIRED → always ``True`` (handshake enforcement is a
      runtime concern; the tier check alone does not block)
    - VERIFIED_ONLY     → ``True`` when *sender_tier* ∈ {internal, owner, verified}
    - DELEGATION_ONLY   → ``True`` when *sender_tier* ∈ {internal, owner}
    - EXPLICIT_INVITE   → always ``False`` (must be checked against an
      allowlist at runtime)
    """
    if contact_policy in (ContactPolicy.OPEN, ContactPolicy.HANDSHAKE_REQUIRED):
        return True
    if contact_policy is ContactPolicy.VERIFIED_ONLY:
        return sender_tier in _VERIFIED_TIERS
    if contact_policy is ContactPolicy.DELEGATION_ONLY:
        return sender_tier in _INTERNAL_TIERS
    # EXPLICIT_INVITE — never passes the generic tier check
    return False


# ---------------------------------------------------------------------------
# Agent JSON filtering
# ---------------------------------------------------------------------------

_PUBLIC_STUB_KEYS = frozenset({
    "protocol_version",
    "identifiers",
    "endpoint",
    "visibility",
})

_VALID_TIERS = frozenset({"internal", "owner", "verified", "external"})


def filter_agent_json(
    full_json: dict,
    caller_tier: str,
    visibility_level: VisibilityLevel,
) -> dict:
    """Return a filtered copy of an agent.json dict based on visibility.

    The original *full_json* is never mutated (deep copy).

    Behaviour
    ---------
    - **PUBLIC** → return the full dict (deep copy).
    - **AUTHENTICATED** → full dict for internal/owner/verified callers;
      otherwise only ``protocol_version``, ``identifiers``, ``endpoint``,
      and ``visibility`` keys.
    - **PRIVATE** → full dict for internal/owner; empty dict for everyone
      else (semantically a 401).
    - **HIDDEN** → full dict for internal/owner; empty dict for everyone
      else (semantically a 404).

    Unknown caller tiers receive an empty dict regardless of visibility level.
    """
    if caller_tier not in _VALID_TIERS:
        return {}  # Unknown tier gets nothing

    if visibility_level is VisibilityLevel.PUBLIC:
        return copy.deepcopy(full_json)

    if visibility_level is VisibilityLevel.AUTHENTICATED:
        if caller_tier in _VERIFIED_TIERS:
            return copy.deepcopy(full_json)
        return {k: copy.deepcopy(v) for k, v in full_json.items() if k in _PUBLIC_STUB_KEYS}

    # PRIVATE and HIDDEN — only internal/owner see anything
    if caller_tier in _INTERNAL_TIERS:
        return copy.deepcopy(full_json)
    return {}
