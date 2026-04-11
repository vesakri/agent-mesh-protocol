"""
AMP Wire Binding -- HTTP transport contract for the Agent Mesh Protocol.

This subpackage formally defines the HTTP contract that any AMP-compliant
server MUST (or MAY) implement.  It covers:

  - Endpoint definitions with conformance levels
  - RFC 7807 error responses
  - Configurable defaults (rate limits, dedup windows, etc.)
  - Body-type to HTTP-semantics mapping

All types are pure Pydantic + stdlib.  Zero platform-specific references.
"""

from __future__ import annotations

from ampro.wire.endpoints import (
    ConformanceLevel,
    EndpointSpec,
    HttpMethod,
    ALL_ENDPOINTS,
    endpoints_for_level,
    endpoints_at_level,
    # Level 0
    AGENT_JSON,
    HEALTH,
    # Level 1
    MESSAGE,
    # Level 2
    TOOLS_LIST,
    TOOL_INVOKE,
    # Level 3
    TASK_STATUS,
    STREAM,
    TASK_UPDATE,
    # Level 4
    SESSION_START,
    SESSION_GET,
    SESSION_UPDATE,
    SESSION_CLOSE,
    IDENTITY_VERIFY,
    CONSENT_REQUEST,
    CONSENT_REVOKE,
    # Level 5
    PRESENCE,
    AUDIT_LOG,
    REGISTRY_RESOLVE,
    REGISTRY_REGISTER,
    REGISTRY_SEARCH,
    # Level 0 (JWKS)
    JWKS,
)
from ampro.wire.errors import (
    ProblemDetail,
    ErrorType,
    rate_limited,
    invalid_message,
    unauthorized,
    forbidden,
    not_found,
    version_mismatch,
    nonce_replay,
    session_expired,
    payload_too_large,
    internal_error,
    not_implemented,
    unavailable,
    capability_not_negotiated,
    contact_policy_violation,
    delegation_denied,
    jurisdiction_conflict,
    residency_violation,
    consent_denied,
    timeout,
    loop_detected,
    invalid_callback_url,
    delegation_validation_failed,
    stream_limit_exceeded,
    content_type_mismatch,
    header_injection,
)
from ampro.wire.config import WireConfig, DEFAULTS as WIRE_DEFAULTS
from ampro.wire.body_type_map import (
    ResponseMode,
    BodyTypeBinding,
    BODY_TYPE_BINDINGS,
    binding_for,
    is_canonical,
    streaming_body_types,
    idempotent_body_types,
)

__all__ = [
    # Endpoints
    "ConformanceLevel",
    "EndpointSpec",
    "HttpMethod",
    "ALL_ENDPOINTS",
    "endpoints_for_level",
    "endpoints_at_level",
    "AGENT_JSON",
    "HEALTH",
    "MESSAGE",
    "TOOLS_LIST",
    "TOOL_INVOKE",
    "TASK_STATUS",
    "STREAM",
    "TASK_UPDATE",
    "SESSION_START",
    "SESSION_GET",
    "SESSION_UPDATE",
    "SESSION_CLOSE",
    "IDENTITY_VERIFY",
    "CONSENT_REQUEST",
    "CONSENT_REVOKE",
    "PRESENCE",
    "AUDIT_LOG",
    "REGISTRY_RESOLVE",
    "REGISTRY_REGISTER",
    "REGISTRY_SEARCH",
    "JWKS",
    # Errors
    "ProblemDetail",
    "ErrorType",
    "rate_limited",
    "invalid_message",
    "unauthorized",
    "forbidden",
    "not_found",
    "version_mismatch",
    "nonce_replay",
    "session_expired",
    "payload_too_large",
    "internal_error",
    "not_implemented",
    "unavailable",
    "capability_not_negotiated",
    "contact_policy_violation",
    "delegation_denied",
    "jurisdiction_conflict",
    "residency_violation",
    "consent_denied",
    "timeout",
    "loop_detected",
    "invalid_callback_url",
    "delegation_validation_failed",
    "stream_limit_exceeded",
    "content_type_mismatch",
    "header_injection",
    # Config
    "WireConfig",
    "WIRE_DEFAULTS",
    # Body type map
    "ResponseMode",
    "BodyTypeBinding",
    "BODY_TYPE_BINDINGS",
    "binding_for",
    "is_canonical",
    "streaming_body_types",
    "idempotent_body_types",
]
