"""
Agent Protocol — Identity Types.

Pure data models for cryptographic identity verification and consent management.
Used by the IDENTITY capability group (Level 4+).

NOTE: This file must NOT import any app.* modules — it is protocol-pure.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ConsentScope(str, Enum):
    """Scopes that an agent can request consent for."""

    READ_PROFILE = "read_profile"
    SEND_MESSAGES = "send_messages"
    ACCESS_TOOLS = "access_tools"
    DELEGATE_TASKS = "delegate_tasks"
    READ_DATA = "read_data"


class IdentityProof(BaseModel):
    """
    Proof of identity via Ed25519 challenge-response.

    The agent signs a server-issued nonce with their Ed25519 private key.
    The server verifies the signature against the agent's known public key.
    """

    agent_id: str = Field(description="Agent identifier (e.g. @slug or DID)")
    public_key: str = Field(description="Base64-encoded Ed25519 public key (32 bytes)")
    signature: str = Field(description="Base64-encoded Ed25519 signature of the nonce")
    nonce: str = Field(description="The challenge nonce that was signed")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the proof was created",
    )
    algorithm: str = Field(default="Ed25519", description="Signature algorithm")

    model_config = {"extra": "ignore"}


class ConsentRequest(BaseModel):
    """
    A request from one agent to another for scoped consent.

    The requester asks the target for permission to perform
    specific actions (scopes) for a limited time.
    """

    requester: str = Field(description="Agent ID requesting consent")
    target: str = Field(description="Agent ID whose consent is sought")
    scopes: list[ConsentScope] = Field(description="Requested permission scopes")
    reason: str = Field(description="Human-readable reason for the request")
    ttl_seconds: int = Field(default=86400, description="Grant lifetime in seconds")

    model_config = {"extra": "ignore"}


class ConsentGrant(BaseModel):
    """
    A granted consent record.

    Created when a consent request is approved. Stored with
    an expiry and can be revoked at any time.
    """

    grant_id: str = Field(description="Unique grant identifier")
    requester: str = Field(description="Agent ID that requested consent")
    target: str = Field(description="Agent ID that granted consent")
    scopes: list[ConsentScope] = Field(description="Granted permission scopes")
    granted_at: datetime = Field(description="When consent was granted")
    expires_at: datetime = Field(description="When consent expires")
    revocable: bool = Field(default=True, description="Whether this grant can be revoked")

    model_config = {"extra": "ignore"}
