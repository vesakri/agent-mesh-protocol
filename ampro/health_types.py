"""Agent Protocol — Health endpoint types. PURE."""

from __future__ import annotations
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response for GET /agent/health."""

    status: str = Field(description="healthy or unhealthy")
    protocol_version: str
    uptime_seconds: int = 0
    current_tasks: int = 0
    max_tasks: int | None = None

    model_config = {"extra": "ignore"}
