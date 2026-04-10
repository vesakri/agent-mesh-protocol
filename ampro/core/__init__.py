"""Core envelope, addressing, body schemas, and versioning."""

from ampro.core.envelope import AgentMessage, STANDARD_HEADERS
from ampro.core.addressing import (
    AgentAddress, AddressType, parse_agent_uri, normalize_shorthand, SCHEME,
)
from ampro.core.body_schemas import validate_body
from ampro.core.status import AgentStatus
from ampro.core.capabilities import CapabilityGroup, CapabilityLevel, CapabilitySet
from ampro.core.priority import Priority
from ampro.core.versioning import (
    SUPPORTED_VERSIONS, CURRENT_VERSION, check_version,
    format_sunset_header, negotiate_version,
)
from ampro.core.message_types_registry import (
    CANONICAL_BODY_TYPES, POST_TYPES, PATCH_TYPES, PUT_TYPES,
)
from ampro.core.message_middleware import (
    validate_message_body, check_message_size,
    build_negotiation_headers, MessageSizeError,
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
