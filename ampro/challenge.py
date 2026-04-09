"""
Agent Protocol — Anti-Abuse Challenge.

Challenge-response mechanism for public-facing agents. When a sender
appears suspicious or is making first contact, the receiver can issue
a challenge that must be solved before the conversation proceeds.

The protocol defines the challenge flow (body types). The specific
challenge algorithms (proof-of-work, CAPTCHA, etc.) are implementation
guidance, not protocol.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChallengeReason(str, Enum):
    """Why a challenge was issued."""

    FIRST_CONTACT = "first_contact"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    TRUST_UPGRADE = "trust_upgrade"


class TaskChallengeBody(BaseModel):
    """body.type = 'task.challenge' — Issue a challenge to the sender."""

    challenge_id: str = Field(description="Unique challenge identifier")
    challenge_type: str = Field(
        description="Challenge type (extensible, e.g. 'proof_of_work', 'captcha')",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Challenge-type-specific parameters",
    )
    expires_at: str = Field(description="ISO-8601 expiration timestamp")
    reason: str = Field(description="Why this challenge was issued")

    model_config = {"extra": "ignore"}


class TaskChallengeResponseBody(BaseModel):
    """body.type = 'task.challenge_response' — Respond to a challenge."""

    challenge_id: str = Field(description="Challenge ID being responded to")
    solution: str = Field(description="The computed answer to the challenge")

    model_config = {"extra": "ignore"}
