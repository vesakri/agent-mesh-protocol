"""Agent Protocol — Rate limit header types. PURE."""

from __future__ import annotations
from pydantic import BaseModel, Field


class RateLimitInfo(BaseModel):
    """Rate limit state for response headers."""

    limit: int = Field(description="Requests allowed per window")
    remaining: int = Field(description="Requests remaining")
    reset: int = Field(description="Unix timestamp when window resets")

    model_config = {"extra": "ignore"}


def format_rate_limit_headers(info: RateLimitInfo) -> dict[str, str]:
    """Format rate limit info as HTTP response headers."""
    return {
        "X-RateLimit-Limit": str(info.limit),
        "X-RateLimit-Remaining": str(info.remaining),
        "X-RateLimit-Reset": str(info.reset),
    }
