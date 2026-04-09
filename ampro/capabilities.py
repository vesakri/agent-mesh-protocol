"""
Agent Protocol — Capability Groups and Progressive Levels.

8 capability groups that agents can declare support for.
6 progressive levels auto-computed from active capabilities.
Capabilities are advertised in agent.json and negotiated during handshake.
"""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any

from pydantic import BaseModel, Field


class CapabilityGroup(str, Enum):
    """The 8 protocol capability groups."""

    MESSAGING = "messaging"      # Send and respond to messages
    STREAMING = "streaming"      # Real-time processing events (SSE)
    TOOLS = "tools"              # Discover and invoke tools (MCP-compatible)
    IDENTITY = "identity"        # Handshake, verify, consent, revoke
    SESSION = "session"          # Start, resume, end, inject context
    DELEGATION = "delegation"    # Delegate, progress, escalate, complete, abort
    PRESENCE = "presence"        # Ping, status, capabilities
    EVENTS = "events"            # Notify, subscribe, unsubscribe, publish


class CapabilityLevel(IntEnum):
    """Progressive capability levels (0-5)."""

    LEVEL_0 = 0  # Static agent.json only (discoverable but not interactive)
    LEVEL_1 = 1  # + /agent/message (can receive and respond)
    LEVEL_2 = 2  # + /agent/tools (exposes callable tools)
    LEVEL_3 = 3  # + /agent/stream (real-time streaming events)
    LEVEL_4 = 4  # + identity, sessions, delegation, events
    LEVEL_5 = 5  # Full protocol (all 8 capability groups)


# Which groups are required for each level
_LEVEL_REQUIREMENTS: dict[CapabilityLevel, set[CapabilityGroup]] = {
    CapabilityLevel.LEVEL_0: set(),
    CapabilityLevel.LEVEL_1: {CapabilityGroup.MESSAGING},
    CapabilityLevel.LEVEL_2: {CapabilityGroup.MESSAGING, CapabilityGroup.TOOLS},
    CapabilityLevel.LEVEL_3: {
        CapabilityGroup.MESSAGING, CapabilityGroup.TOOLS, CapabilityGroup.STREAMING,
    },
    CapabilityLevel.LEVEL_4: {
        CapabilityGroup.MESSAGING, CapabilityGroup.TOOLS, CapabilityGroup.STREAMING,
        CapabilityGroup.IDENTITY, CapabilityGroup.SESSION,
        CapabilityGroup.DELEGATION, CapabilityGroup.EVENTS,
    },
    CapabilityLevel.LEVEL_5: set(CapabilityGroup),
}


class CapabilitySet(BaseModel):
    """Declares which capability groups an agent supports."""

    groups: set[CapabilityGroup] = Field(default_factory=set)

    @property
    def level(self) -> CapabilityLevel:
        """Auto-compute the highest protocol level from active capabilities."""
        for lvl in reversed(CapabilityLevel):
            required = _LEVEL_REQUIREMENTS[lvl]
            if required.issubset(self.groups):
                return lvl
        return CapabilityLevel.LEVEL_0

    def supports(self, group: CapabilityGroup) -> bool:
        return group in self.groups

    def to_agent_json(self) -> dict[str, Any]:
        """Serialize for agent.json capabilities field."""
        return {
            "groups": sorted(g.value for g in self.groups),
            "level": self.level.value,
        }

    model_config = {"extra": "ignore"}
