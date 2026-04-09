"""
Agent Protocol — Message Pre-Processing Middleware.

Cross-cutting concerns for POST /agent/message:
  - Body validation against body_type schemas
  - Message size enforcement
  - Capability negotiation header building
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ampro.envelope import AgentMessage
from ampro.body_schemas import validate_body
from ampro.capabilities import CapabilityGroup, CapabilitySet
from ampro.negotiation import CapabilityNegotiator


class MessageSizeError(Exception):
    def __init__(self, max_bytes: int, received_bytes: int):
        self.max_bytes = max_bytes
        self.received_bytes = received_bytes
        super().__init__(f"Message size {received_bytes} exceeds limit {max_bytes}")


def validate_message_body(msg: AgentMessage) -> BaseModel | dict[str, Any]:
    body = msg.body if isinstance(msg.body, dict) else {}
    return validate_body(msg.body_type, body)


def check_message_size(raw_body: bytes, max_bytes: int = 10_485_760) -> None:
    if len(raw_body) > max_bytes:
        raise MessageSizeError(max_bytes=max_bytes, received_bytes=len(raw_body))


def build_negotiation_headers(
    server_caps: CapabilitySet,
    client_caps_str: str,
) -> dict[str, str]:
    client_groups: set[CapabilityGroup] = set()
    if client_caps_str:
        for cap in client_caps_str.split(","):
            cap = cap.strip()
            try:
                client_groups.add(CapabilityGroup(cap))
            except ValueError:
                pass

    client_caps = CapabilitySet(groups=client_groups)
    result = CapabilityNegotiator.full_negotiation(
        server_caps=server_caps,
        client_caps=client_caps,
    )
    agreed = result.agreed_capabilities

    headers: dict[str, str] = {
        "Negotiated-Capabilities": ",".join(sorted(g.value for g in agreed.groups)),
        "Negotiated-Level": str(agreed.level.value),
    }
    if result.warnings:
        headers["Downgrade-Warning"] = "; ".join(result.warnings)
    return headers
