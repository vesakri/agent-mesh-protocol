"""
Agent Protocol — Zero-Knowledge Trust Proofs.

Prove that a trust score meets a threshold without revealing the
exact score. The claim is human-readable (e.g. 'score_above_500'),
the proof is opaque to the protocol.

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrustProofBody(BaseModel):
    """body.type = 'trust.proof' — ZK proof that trust meets a threshold."""

    agent_id: str = Field(
        description="Agent proving its trust level",
    )
    claim: str = Field(
        description="Human-readable threshold claim (e.g. score_above_500)",
    )
    proof_type: str = Field(
        description="Proof method (e.g. zkp)",
    )
    proof: str = Field(
        description="The cryptographic proof",
    )
    verifier_key_id: str = Field(
        description="Key ID of the verifier",
    )

    model_config = {"extra": "ignore"}
