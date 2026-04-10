"""
Agent Protocol — Message Priority.

Five-level priority enum for message and task ordering.

Values ordered from lowest to highest:
  batch < normal < priority < urgent < critical

PURE — zero platform-specific imports.
"""

from __future__ import annotations

from enum import Enum


class Priority(str, Enum):
    """Message / task priority levels."""

    BATCH = "batch"
    NORMAL = "normal"
    PRIORITY = "priority"
    URGENT = "urgent"
    CRITICAL = "critical"
