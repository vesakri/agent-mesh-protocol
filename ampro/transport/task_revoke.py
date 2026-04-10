"""
Agent Protocol — Task Revoke.

Allows an agent (or delegator) to revoke a previously assigned or
delegated task, optionally cascading the revocation to child tasks.

body.type = 'task.revoke'
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TaskRevokeBody(BaseModel):
    """body.type = 'task.revoke' — Revoke a task."""

    task_id: str = Field(description="ID of the task being revoked")
    reason: str = Field(description="Human-readable reason for revocation")
    cascade: bool = Field(
        default=False,
        description="Whether to propagate revocation to downstream delegates",
    )
    revoke_children: bool = Field(
        default=False,
        description="Whether to revoke child (spawned) tasks as well",
    )

    model_config = {"extra": "ignore"}
