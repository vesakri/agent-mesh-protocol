"""
Agent Protocol — Message Pre-Processing Middleware.

Cross-cutting concerns for POST /agent/message:
  - Body validation against body_type schemas
  - Message size enforcement
  - Capability negotiation header building
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from ampro.core.envelope import AgentMessage
from ampro.core.body_schemas import validate_body
from ampro.core.capabilities import CapabilityGroup, CapabilitySet
from ampro.security.encryption import EncryptionDowngradeError
from ampro.transport.negotiation import CapabilityNegotiator

logger = logging.getLogger(__name__)


class MessageSizeError(Exception):
    def __init__(self, max_bytes: int, received_bytes: int):
        self.max_bytes = max_bytes
        self.received_bytes = received_bytes
        super().__init__(f"Message size {received_bytes} exceeds limit {max_bytes}")


def validate_message_body(msg: AgentMessage) -> BaseModel | dict[str, Any]:
    if isinstance(msg.body, dict):
        body = msg.body
    elif isinstance(msg.body, str):
        # Convenience: a bare string body for body_type "message" wraps as {"text": body}
        body = {"text": msg.body}
    elif msg.body is None:
        # No body provided — skip schema validation (body is optional for
        # the base "message" type and extension types)
        return {}
    else:
        raise TypeError(
            f"body must be dict, str, or None; got {type(msg.body).__name__}"
        )
    return validate_body(msg.body_type, body)


def check_message_size(raw_body: bytes, max_bytes: int = 10_485_760) -> None:
    if len(raw_body) > max_bytes:
        raise MessageSizeError(max_bytes=max_bytes, received_bytes=len(raw_body))


def enforce_encryption_requirement(
    msg: AgentMessage,
    session_requires_encryption: bool,
) -> None:
    """Reject plaintext bodies on a session that pinned required_encryption.

    Call this at the message ingress path. ``session_requires_encryption``
    is the flag pinned on the session state in ``session/types.py`` when
    the initial message carried ``EncryptedBody(required_encryption=True)``.

    Raises:
        EncryptionDowngradeError: If the session requires encryption and
            the incoming message body is not an EncryptedBody.
    """
    if not session_requires_encryption:
        return
    # A body is considered encrypted when its body_type is the encrypted
    # sentinel OR its payload matches the EncryptedBody shape (has
    # ciphertext + recipient_key_id). Everything else is plaintext.
    if msg.body_type == "encrypted":
        return
    body = msg.body
    if isinstance(body, dict) and "ciphertext" in body and "recipient_key_id" in body:
        return
    raise EncryptionDowngradeError(
        "Session requires encryption; plaintext body rejected (downgrade prevention)"
    )


def build_negotiation_headers(
    server_caps: CapabilitySet,
    client_caps_str: str,
) -> dict[str, str]:
    MAX_CAPABILITIES = 50
    client_groups: set[CapabilityGroup] = set()
    if client_caps_str:
        parts = [p.strip() for p in client_caps_str.split(",")]
        if len(parts) > MAX_CAPABILITIES:
            logger.warning(
                "Capability list truncated from %d to %d", len(parts), MAX_CAPABILITIES
            )
            parts = parts[:MAX_CAPABILITIES]
        for cap in parts:
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
