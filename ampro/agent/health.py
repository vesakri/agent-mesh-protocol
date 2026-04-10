"""Agent Protocol — Health endpoint types. PURE."""

from __future__ import annotations
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response for GET /agent/health."""

    status: str = Field(description="healthy or unhealthy")
    protocol_version: str = Field(description="Semantic version of the agent protocol in use (e.g. 0.1.0)")
    uptime_seconds: int = Field(default=0, description="Seconds since the agent process started")
    current_tasks: int = Field(default=0, description="Number of tasks currently being processed")
    max_tasks: int | None = Field(default=None, description="Maximum concurrent tasks the agent supports, if limited")

    model_config = {"extra": "ignore"}
