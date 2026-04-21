"""
Agent Protocol — Delegation Chain Validation.

Supports multi-hop delegation where agent A delegates authority to agent B,
who may further delegate to agent C, with cryptographically verified scope
narrowing at each hop.

This module is PURE — only stdlib + pydantic + cryptography.
No platform-specific imports (app.*, etc.).
Designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, Field

# Clock skew tolerance — imported from canonical constant in trust.tiers.
from ampro.trust.tiers import CLOCK_SKEW_SECONDS

_SKEW = timedelta(seconds=CLOCK_SKEW_SECONDS)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DelegationLink(BaseModel):
    """A single hop in a delegation chain."""

    delegator: str = Field(description="Agent ID of the delegating agent")
    delegate: str = Field(description="Agent ID receiving the delegation")
    scopes: list[str] = Field(
        description="Scopes granted (e.g. ['tool:read', 'tool:execute'])"
    )
    max_depth: int = Field(
        default=3,
        description="Maximum remaining delegation depth from this link onward",
    )
    created_at: datetime = Field(description="When this link was created")
    expires_at: datetime = Field(description="When this link expires")
    signature: str = Field(
        default="",
        description="Base64-encoded Ed25519 signature by the delegator",
    )
    max_fan_out: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum parallel sub-delegations from this link",
    )
    trust_tier: str = Field(
        default="external",
        description="Effective trust tier at this link",
    )
    jwks_url: str = Field(
        default="",
        description="JWKS endpoint for the delegator's public key",
    )
    chain_budget: str = Field(
        default="",
        description="Chain budget string, e.g. 'remaining=3.50USD;max=5.00USD'",
    )

    model_config = {"extra": "ignore"}


class DelegationChain(BaseModel):
    """An ordered sequence of delegation links forming a chain of trust."""

    links: list[DelegationLink] = Field(
        default_factory=list,
        description="Ordered delegation links (root first)",
    )

    @property
    def depth(self) -> int:
        """Number of hops in the chain."""
        return len(self.links)

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Canonical serialization (for signing)
# ---------------------------------------------------------------------------


def _canonical_link_bytes(
    link: DelegationLink,
    parent_delegate: str | None = None,
) -> bytes:
    """
    Produce deterministic JSON bytes for a delegation link,
    excluding the ``signature`` field.

    Keys are sorted and no extra whitespace is used so that
    any compliant implementation can reproduce the same bytes.

    Args:
        link: The delegation link to serialize.
        parent_delegate: The ``delegate`` field of the parent link (or
            ``None`` for the root link).  Including this value in the
            canonical payload binds the signature to a specific position
            in a specific chain, preventing cross-chain transplant attacks.
    """
    data = {
        "created_at": link.created_at.isoformat(),
        "delegate": link.delegate,
        "delegator": link.delegator,
        "expires_at": link.expires_at.isoformat(),
        "max_depth": link.max_depth,
        "parent_delegate": parent_delegate,
        "scopes": sorted(link.scopes),
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_dict_bytes(link_data: dict) -> bytes:
    """
    Produce deterministic JSON bytes from a raw dict,
    excluding the ``signature`` key if present.
    """
    cleaned = {k: v for k, v in link_data.items() if k != "signature"}
    # Normalise scopes to sorted list for determinism
    if "scopes" in cleaned and isinstance(cleaned["scopes"], list):
        cleaned["scopes"] = sorted(cleaned["scopes"])
    return json.dumps(cleaned, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Scope helpers
# ---------------------------------------------------------------------------


def validate_scope_narrowing(
    parent_scopes: list[str], child_scopes: list[str]
) -> bool:
    """
    Check that *child_scopes* is a subset of *parent_scopes*.

    Supports wildcard matching with strict prefix hierarchy:

    - ``*`` (universal wildcard) in the parent allows any child scope.
    - ``tool:*`` in the parent allows ``tool:read``, ``tool:execute``,
      ``tool:sub:read``, and ``tool:*`` (any scope starting with ``tool:``).
    - ``tool:*`` does NOT permit ``admin:*``, ``data:read``, or any scope
      whose prefix differs from ``tool``.
    - An explicit scope like ``tool:read`` only permits ``tool:read``
      (exact match).

    An empty child scope list is considered invalid (useless delegation).

    Returns True if the child scopes are a valid narrowing.
    """
    MAX_SCOPES = 100
    if len(child_scopes) > MAX_SCOPES or len(parent_scopes) > MAX_SCOPES:
        return False

    if not child_scopes:
        return False

    parent_set = set(parent_scopes)

    # Universal wildcard — parent grants everything.
    has_universal = "*" in parent_set

    # Pre-compute wildcard prefixes for efficient matching.
    # "tool:*" → prefix "tool:" so that "tool:read", "tool:sub:x" all match.
    wildcard_prefixes: list[str] = []
    for ps in parent_scopes:
        if ps.endswith(":*"):
            wildcard_prefixes.append(ps[:-1])  # "tool:*" → "tool:"

    for scope in child_scopes:
        # Universal wildcard in parent → everything allowed
        if has_universal:
            continue

        # Direct / exact match
        if scope in parent_set:
            continue

        # Wildcard prefix match: child scope must start with one of the
        # parent's wildcard prefixes (e.g. parent "tool:*" → prefix
        # "tool:" covers child "tool:read", "tool:sub:read", "tool:*").
        if any(scope.startswith(wp) for wp in wildcard_prefixes):
            continue

        # No match found
        return False

    return True


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def sign_delegation(
    private_key_bytes: bytes,
    link_data: dict,
    parent_delegate: str | None = None,
) -> str:
    """
    Sign canonical JSON of *link_data* (excluding signature) with Ed25519.

    The ``parent_delegate`` is injected into the canonical payload before
    signing so that the resulting signature is bound to a specific chain
    position, preventing cross-chain transplant attacks.

    Args:
        private_key_bytes: Raw 32-byte Ed25519 private key seed.
        link_data: Dict representing the delegation link fields.
        parent_delegate: The ``delegate`` of the parent link, or ``None``
            for the root link.

    Returns:
        Base64-encoded signature string.
    """
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    # Inject parent_delegate into the dict before canonical serialization
    augmented = {**link_data, "parent_delegate": parent_delegate}
    payload = _canonical_dict_bytes(augmented)
    signature = private_key.sign(payload)
    return base64.b64encode(signature).decode("ascii")


# ---------------------------------------------------------------------------
# Chain validation
# ---------------------------------------------------------------------------


def validate_chain(
    chain: DelegationChain,
    public_keys: dict[str, bytes],
) -> tuple[bool, str]:
    """
    Validate every link in a delegation chain.

    Checks performed for each link (in order):
      1. Delegator's public key is available.
      2. Ed25519 signature is valid.
      3. Link has not expired.
      4. Depth does not exceed the max_depth of the *parent* link
         (or the link's own max_depth for the root).
      5. Scopes are a valid narrowing of the parent link's scopes.
      6. Chain continuity: each link's delegator equals the previous
         link's delegate.
      7. Temporal nesting: each link's validity window is within
         its parent's.

    Args:
        chain: The delegation chain to validate.
        public_keys: Mapping of agent_id -> raw 32-byte Ed25519 public key.

    Returns:
        ``(True, "valid")`` on success, or ``(False, reason)`` on failure.
    """
    if not chain.links:
        return False, "empty chain"

    now = datetime.now(UTC)

    for i, link in enumerate(chain.links):
        # --- 0. Self-delegation check ---
        if link.delegator == link.delegate:
            return False, f"link {i}: self-delegation not allowed ({link.delegator})"

        # --- 1. Public key lookup ---
        pub_bytes = public_keys.get(link.delegator)
        if pub_bytes is None:
            return False, f"link {i}: unknown delegator '{link.delegator}'"

        # --- 2. Signature verification (context-bound) ---
        parent_delegate = chain.links[i - 1].delegate if i > 0 else None
        try:
            pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
            payload = _canonical_link_bytes(link, parent_delegate=parent_delegate)
            sig_bytes = base64.b64decode(link.signature)
            pub_key.verify(sig_bytes, payload)
        except Exception as exc:
            return False, f"link {i}: invalid signature ({exc})"

        # --- 3. Expiry check (with clock skew tolerance) ---
        if link.expires_at <= now - _SKEW:
            return False, f"link {i}: expired (expires_at={link.expires_at.isoformat()})"

        if link.created_at > now + _SKEW:
            return False, f"link {i}: created_at is in the future"

        # --- 4. Depth check ---
        if i > 0:
            parent = chain.links[i - 1]
            # The current hop index (1-based) must not exceed the parent's max_depth
            if i >= parent.max_depth:
                return (
                    False,
                    f"link {i}: depth {i} exceeds parent max_depth {parent.max_depth}",
                )

        # --- 5. Scope narrowing ---
        if i > 0:
            parent = chain.links[i - 1]
            if not validate_scope_narrowing(parent.scopes, link.scopes):
                return (
                    False,
                    f"link {i}: scopes {link.scopes} not subset of parent {parent.scopes}",
                )

        # --- 6. Chain continuity ---
        if i > 0:
            parent = chain.links[i - 1]
            if link.delegator != parent.delegate:
                return (
                    False,
                    f"link {i}: delegator '{link.delegator}' != "
                    f"previous delegate '{parent.delegate}'",
                )

        # --- 7. Temporal nesting ---
        if i > 0:
            parent = chain.links[i - 1]
            if link.created_at < parent.created_at - _SKEW:
                return (
                    False,
                    f"link {i}: created_at precedes parent's created_at",
                )
            if link.expires_at > parent.expires_at + _SKEW:
                return (
                    False,
                    f"link {i}: expires_at exceeds parent's expires_at",
                )

        # --- 8. Fan-out check ---
        if hasattr(link, 'max_fan_out') and i > 0:
            # max_fan_out limits how many sub-delegations at each level
            if link.max_fan_out <= 0:
                return False, f"link {i}: max_fan_out is {link.max_fan_out} (must be > 0)"

        # --- 9. Budget check (fail-closed) ---
        if hasattr(link, 'chain_budget') and link.chain_budget:
            try:
                remaining, max_b = parse_chain_budget(link.chain_budget)
            except ValueError as e:
                return False, f"link {i}: invalid chain_budget ({e})"
            if remaining < 0:
                return False, f"link {i}: negative budget (remaining={remaining})"
            if remaining <= 0:
                return False, f"link {i}: chain budget exhausted (remaining={remaining})"
            # Child budget must not exceed parent budget
            if i > 0:
                parent = chain.links[i - 1]
                if hasattr(parent, 'chain_budget') and parent.chain_budget:
                    try:
                        parent_remaining, _ = parse_chain_budget(parent.chain_budget)
                        if remaining > parent_remaining:
                            return (
                                False,
                                f"link {i}: child budget ({remaining}) "
                                f"exceeds parent budget ({parent_remaining})",
                            )
                    except ValueError:
                        # Parent already validated; should not happen
                        pass

    return True, "valid"


# ---------------------------------------------------------------------------
# Chain budget + visited agents helpers
# ---------------------------------------------------------------------------

# Pre-compiled regex for chain budget parsing (non-backtracking pattern)
_BUDGET_RE = re.compile(r"remaining=(\d+(?:\.\d+)?)USD;max=(\d+(?:\.\d+)?)USD")


def parse_chain_budget(budget: str) -> tuple[float, float]:
    """Parse a Chain-Budget header value into (remaining, max) floats."""
    match = _BUDGET_RE.match(budget)
    if not match:
        raise ValueError(f"Invalid chain budget format: {budget!r}")
    return float(match.group(1)), float(match.group(2))


def normalize_agent_uri(uri: str) -> str:
    """
    Normalize an agent URI for consistent comparison.

    Strips leading/trailing whitespace and lowercases the URI so that
    ``agent://A`` and ``agent://a `` are treated as the same agent.
    """
    return uri.strip().lower()


def parse_visited_agents(header: str) -> set[str]:
    """
    Parse Visited-Agents header into a set of **normalized** agent URIs.

    Each URI is stripped and lowercased so that case/whitespace variations
    are collapsed into a single canonical form.
    """
    if not header:
        return set()
    return {normalize_agent_uri(a) for a in header.split(",") if a.strip()}


def check_visited_agents_loop(header: str, self_uri: str) -> bool:
    """
    Check if *self_uri* is already in the Visited-Agents list.

    Both the header entries and *self_uri* are normalized before comparison
    so that case and whitespace differences do not bypass loop detection.

    Returns True if a loop is detected.
    """
    agents = parse_visited_agents(header)
    return normalize_agent_uri(self_uri) in agents


def check_visited_agents_limit(header: str, max_agents: int = 20) -> bool:
    """Check if the Visited-Agents count is within limits. Returns True if within limit."""
    agents = parse_visited_agents(header)
    return len(agents) <= max_agents
