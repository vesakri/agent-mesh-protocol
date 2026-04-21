"""
Agent Protocol — Identity Linking.

Cryptographic proof that two agent:// addresses belong to the same
entity. Used when an agent operates under multiple addresses and
needs to prove equivalence to other agents.

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field, model_validator

DEFAULT_LINK_PROOF_LIFETIME = timedelta(days=365)
"""Default lifetime for newly minted identity link proofs (1 year)."""


def _parse_any_ts(value: str | datetime) -> datetime:
    """Best-effort parse of an ISO-8601 / datetime into an aware ``datetime``."""
    if isinstance(value, datetime):
        dt = value
    else:
        # Accept trailing "Z" as UTC.
        raw = value.replace("Z", "+00:00") if value.endswith("Z") else value
        dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class IdentityLinkProofBody(BaseModel):
    """Payload proving two agent addresses share the same controlling entity."""

    source_id: str = Field(description="First agent:// URI")
    target_id: str = Field(description="Second agent:// URI to link")
    proof_type: str = Field(
        description="Proof method (e.g. ed25519_cross_sign)",
    )
    proof: str = Field(description="Cryptographic proof of shared control")
    timestamp: str = Field(
        description="ISO-8601 timestamp when proof was generated",
    )
    expires_at: datetime = Field(
        description="When the link proof is no longer valid",
    )

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def _expires_after_timestamp(self) -> IdentityLinkProofBody:
        """A freshly minted proof MUST NOT already be expired.

        ``expires_at`` is required to be strictly after ``timestamp``; if the
        ``timestamp`` field cannot be parsed we fall back to "not allowed to be
        in the past" so malformed timestamps can't bypass the check.
        """
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
            object.__setattr__(self, "expires_at", expires_at)

        try:
            issued_at = _parse_any_ts(self.timestamp)
        except (ValueError, TypeError):
            issued_at = datetime.now(tz=UTC)

        if expires_at <= issued_at:
            raise ValueError(
                "expires_at must be strictly after timestamp "
                f"(got expires_at={expires_at.isoformat()}, "
                f"timestamp={issued_at.isoformat()})"
            )
        return self


def is_link_proof_valid(
    body: IdentityLinkProofBody,
    now: datetime | None = None,
) -> bool:
    """Return ``True`` iff ``now`` is before ``body.expires_at``.

    Args:
        body: The link proof body to check.
        now:  Override for the current time (defaults to ``datetime.now(UTC)``).

    Returns:
        ``False`` once the proof has expired, ``True`` otherwise.
    """
    current = now if now is not None else datetime.now(tz=UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    expires = body.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    return current <= expires
