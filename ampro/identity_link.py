"""
Agent Protocol — Identity Linking.

Cryptographic proof that two agent:// addresses belong to the same
entity. Used when an agent operates under multiple addresses and
needs to prove equivalence to other agents.

This module contains NO platform-specific imports.
It is designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


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

    model_config = {"extra": "ignore"}
