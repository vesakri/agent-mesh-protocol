"""
Agent Protocol — Capability Negotiation.

Computes the intersection of server and client capabilities,
filters tools by agreed capabilities, and produces a
NegotiationResult summarising what both sides support.

This module is PURE — no platform-specific imports (app.*, etc.).
Designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ampro.core.capabilities import CapabilityGroup, CapabilitySet


class NegotiationResult(BaseModel):
    """Outcome of a capability negotiation between server and client."""

    agreed_capabilities: CapabilitySet = Field(
        description="The capabilities both server and client support (intersection).",
    )
    filtered_tool_count: int = Field(
        default=0,
        description="Number of tools remaining after capability filtering.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable warnings about capability mismatches.",
    )

    model_config = {"extra": "ignore"}


class CapabilityNegotiator:
    """
    Negotiates capabilities between a server and a connecting client.

    The negotiation is a simple group intersection: only capabilities
    that *both* sides declare are included in the agreed set.
    """

    @staticmethod
    def negotiate(
        server_caps: CapabilitySet,
        client_caps: CapabilitySet,
    ) -> CapabilitySet:
        """
        Compute the intersection of server and client capability groups.

        Returns a CapabilitySet containing only groups supported by both sides.
        """
        agreed_groups = server_caps.groups & client_caps.groups
        return CapabilitySet(groups=agreed_groups)

    @staticmethod
    def filter_tools(
        tools: list[dict[str, Any]],
        client_caps: CapabilitySet,
    ) -> list[dict[str, Any]]:
        """
        Remove tools that require capabilities the client does not support.

        Each tool may declare a ``required_capabilities`` list of
        CapabilityGroup values.  If the list is absent or empty the
        tool is kept unconditionally.
        """
        if not client_caps.groups:
            # Client declared no capabilities — filter out everything
            # that has explicit requirements.
            return [
                t for t in tools
                if not t.get("required_capabilities")
            ]

        filtered: list[dict[str, Any]] = []
        for tool in tools:
            required = tool.get("required_capabilities", [])
            if not required:
                filtered.append(tool)
                continue
            # All required groups must be in the client's set
            if all(
                CapabilityGroup(r) in client_caps.groups
                for r in required
            ):
                filtered.append(tool)
        return filtered

    @classmethod
    def full_negotiation(
        cls,
        server_caps: CapabilitySet,
        client_caps: CapabilitySet,
        tools: list[dict[str, Any]] | None = None,
    ) -> NegotiationResult:
        """
        Run a complete negotiation: intersect capabilities, filter tools,
        and collect warnings.
        """
        agreed = cls.negotiate(server_caps, client_caps)

        warnings: list[str] = []
        # Warn about server capabilities the client does not support
        unsupported_by_client = server_caps.groups - client_caps.groups
        for grp in sorted(unsupported_by_client, key=lambda g: g.value):
            warnings.append(
                f"Server supports '{grp.value}' but client does not"
            )

        filtered_tools = cls.filter_tools(tools or [], agreed)

        return NegotiationResult(
            agreed_capabilities=agreed,
            filtered_tool_count=len(filtered_tools),
            warnings=warnings,
        )
