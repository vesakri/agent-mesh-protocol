"""Core envelope, addressing, body schemas, and versioning."""

from ampro.core.addressing import (
    SCHEME,
    AddressType,
    AgentAddress,
    normalize_shorthand,
    parse_agent_uri,
)
from ampro.core.body_schemas import validate_body
from ampro.core.capabilities import CapabilityGroup, CapabilityLevel, CapabilitySet
from ampro.core.envelope import STANDARD_HEADERS, AgentMessage
from ampro.core.message_middleware import (
    MessageSizeError,
    build_negotiation_headers,
    check_message_size,
    validate_message_body,
)
from ampro.core.message_types_registry import (
    CANONICAL_BODY_TYPES,
    PATCH_TYPES,
    POST_TYPES,
    PUT_TYPES,
)
from ampro.core.priority import Priority
from ampro.core.status import AgentStatus
from ampro.core.versioning import (
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    check_version,
    format_sunset_header,
    negotiate_version,
)

__all__ = [
    # Envelope
    "AgentMessage", "STANDARD_HEADERS",
    # Addressing
    "AgentAddress", "AddressType", "parse_agent_uri", "normalize_shorthand", "SCHEME",
    # Body schemas
    "validate_body",
    # Status
    "AgentStatus",
    # Capabilities
    "CapabilityGroup", "CapabilityLevel", "CapabilitySet",
    # Priority
    "Priority",
    # Versioning
    "SUPPORTED_VERSIONS", "CURRENT_VERSION", "check_version",
    "format_sunset_header", "negotiate_version",
    # Message type registry
    "CANONICAL_BODY_TYPES", "POST_TYPES", "PATCH_TYPES", "PUT_TYPES",
    # Middleware
    "validate_message_body", "check_message_size",
    "build_negotiation_headers", "MessageSizeError",
]
