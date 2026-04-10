"""
Agent Protocol — Identity Migration.

When an agent moves to a new address, it publishes a migration proof.
The old address serves a moved_to pointer in agent.json so callers
can follow the redirect.

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IdentityMigrationBody(BaseModel):
    """body.type = 'identity.migration' — Announce address migration."""

    old_id: str = Field(description="Previous agent:// URI")
    new_id: str = Field(description="New agent:// URI")
    migration_proof: str = Field(
        description="Signed by both old and new keys",
    )
    effective_at: str = Field(
        description="ISO-8601 timestamp when migration takes effect",
    )

    model_config = {"extra": "ignore"}
