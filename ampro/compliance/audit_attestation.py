"""
Agent Protocol — Audit Attestation.

Signed proof that both parties agree on what happened during a session.
Creates a tamper-proof record without requiring a third-party auditor.

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuditAttestationBody(BaseModel):
    """body.type = 'audit.attestation' — mutual session attestation."""

    audit_id: str = Field(description="Unique attestation identifier")
    agents: list[str] = Field(
        description="agent:// URIs of all participating agents",
    )
    events_hash: str = Field(
        description="SHA-256 hash of all session events",
    )
    attestation_signatures: dict[str, str] = Field(
        description="Agent URI → Ed25519 signature mapping",
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp of attestation",
    )

    model_config = {"extra": "ignore"}
