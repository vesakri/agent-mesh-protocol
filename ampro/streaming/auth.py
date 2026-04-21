"""
Agent Protocol — Stream Auth Refresh.

Mid-stream JWT renewal without reconnecting. The server sends a new
token before the current one expires.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StreamAuthRefreshEvent(BaseModel):
    """Server-sent event carrying a refreshed authentication token."""

    method: Literal["bearer", "refresh", "jwks-kid", "jwt", "api_key"] = Field(
        description="Authentication refresh method",
    )
    token: str = Field(
        min_length=16,
        max_length=4096,
        pattern=r"^[A-Za-z0-9._-]+$",
        description=(
            "The new authentication token. Must be 16-4096 chars and use "
            "only the URL-safe / JWT charset [A-Za-z0-9._-]."
        ),
    )
    expires_at: str = Field(
        description="ISO-8601 timestamp when the new token expires",
    )

    model_config = {"extra": "ignore"}
