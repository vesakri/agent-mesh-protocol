"""
Agent Protocol — Stream Auth Refresh.

Mid-stream JWT renewal without reconnecting. The server sends a new
token before the current one expires.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StreamAuthRefreshEvent(BaseModel):
    """Server-sent event carrying a refreshed authentication token."""

    method: str = Field(description="Authentication method (e.g. jwt, api_key)")
    token: str = Field(description="The new authentication token")
    expires_at: str = Field(
        description="ISO-8601 timestamp when the new token expires",
    )

    model_config = {"extra": "ignore"}
