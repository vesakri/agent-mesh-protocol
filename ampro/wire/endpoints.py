"""
AMP Wire Binding -- Endpoint Definitions.

Formal HTTP endpoint definitions for the Agent Mesh Protocol.
These are the endpoints that any AMP-compliant server MUST or MAY implement,
organised into six conformance levels (0-5).

Level 0 (DISCOVERY) is MANDATORY for all AMP agents.
Higher levels are OPTIONAL and advertised via agent.json capabilities.

PURE -- zero platform-specific imports.  Only pydantic and stdlib.
"""

from __future__ import annotations

from enum import Enum, IntEnum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConformanceLevel(IntEnum):
    """AMP conformance levels.

    Level 0 is MANDATORY for all AMP-compliant agents.
    Higher levels are progressively more capable but OPTIONAL.
    """

    DISCOVERY = 0       # /.well-known/agent.json + /agent/health
    MESSAGING = 1       # POST /agent/message
    TOOLS = 2           # GET/POST /agent/tools
    TASK_LIFECYCLE = 3  # PATCH/GET /agent/tasks, SSE streaming
    IDENTITY = 4        # Sessions, consent, identity verification
    PLATFORM = 5        # Presence, audit, registry


class HttpMethod(str, Enum):
    """HTTP methods used by AMP endpoints."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


# ---------------------------------------------------------------------------
# EndpointSpec
# ---------------------------------------------------------------------------


class EndpointSpec(BaseModel):
    """Formal specification of an AMP HTTP endpoint.

    Each instance describes one REST endpoint that an AMP-compliant server
    exposes.  The ``level`` field determines whether the endpoint is mandatory
    (level 0) or optional.
    """

    path: str = Field(description="URL path template (e.g. /agent/message)")
    method: HttpMethod = Field(description="HTTP method")
    level: ConformanceLevel = Field(description="Minimum conformance level")
    description: str = Field(description="Human-readable purpose of this endpoint")
    request_content_type: str = Field(
        default="application/json",
        description="Expected Content-Type for requests",
    )
    response_content_types: list[str] = Field(
        default_factory=lambda: ["application/json"],
        description="Content-Type values the server may return",
    )
    auth_required: bool = Field(
        default=False,
        description="Whether the endpoint requires authentication",
    )
    rate_limited: bool = Field(
        default=False,
        description="Whether the endpoint is rate-limited",
    )
    idempotent: bool = Field(
        default=False,
        description="Whether repeated identical requests produce the same effect",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Level 0 -- DISCOVERY (MANDATORY)
# ---------------------------------------------------------------------------

AGENT_JSON = EndpointSpec(
    path="/.well-known/agent.json",
    method=HttpMethod.GET,
    level=ConformanceLevel.DISCOVERY,
    description="Agent identity and capability discovery",
    auth_required=False,
    idempotent=True,
)

HEALTH = EndpointSpec(
    path="/agent/health",
    method=HttpMethod.GET,
    level=ConformanceLevel.DISCOVERY,
    description="Agent health check",
    auth_required=False,
    idempotent=True,
)

JWKS = EndpointSpec(
    path="/.well-known/agent-keys.json",
    method=HttpMethod.GET,
    level=ConformanceLevel.DISCOVERY,
    description="JWKS endpoint for Ed25519 public keys and revocation",
    auth_required=False,
    rate_limited=True,
)


# ---------------------------------------------------------------------------
# Level 1 -- MESSAGING
# ---------------------------------------------------------------------------

MESSAGE = EndpointSpec(
    path="/agent/message",
    method=HttpMethod.POST,
    level=ConformanceLevel.MESSAGING,
    description="Send an agent message (all body types)",
    auth_required=False,  # Trust tier determines behaviour, not auth gate
    rate_limited=True,
)


# ---------------------------------------------------------------------------
# Level 2 -- TOOLS
# ---------------------------------------------------------------------------

TOOLS_LIST = EndpointSpec(
    path="/agent/tools",
    method=HttpMethod.GET,
    level=ConformanceLevel.TOOLS,
    description="List available tools",
    idempotent=True,
)

TOOL_INVOKE = EndpointSpec(
    path="/agent/tools/{tool_name}",
    method=HttpMethod.POST,
    level=ConformanceLevel.TOOLS,
    description="Invoke a specific tool",
    auth_required=True,
    rate_limited=True,
)


# ---------------------------------------------------------------------------
# Level 3 -- TASK LIFECYCLE
# ---------------------------------------------------------------------------

TASK_STATUS = EndpointSpec(
    path="/agent/tasks/{task_id}",
    method=HttpMethod.GET,
    level=ConformanceLevel.TASK_LIFECYCLE,
    description="Poll task status (fallback for streaming)",
    idempotent=True,
)

TASK_UPDATE = EndpointSpec(
    path="/agent/tasks/{task_id}",
    method=HttpMethod.PATCH,
    level=ConformanceLevel.TASK_LIFECYCLE,
    description="Update task state (progress, complete, error, etc.)",
    auth_required=True,
)

STREAM = EndpointSpec(
    path="/agent/stream",
    method=HttpMethod.GET,
    level=ConformanceLevel.TASK_LIFECYCLE,
    description="Server-Sent Events stream for real-time updates",
    response_content_types=["text/event-stream"],
    auth_required=True,
)


# ---------------------------------------------------------------------------
# Level 4 -- IDENTITY
# ---------------------------------------------------------------------------

SESSION_START = EndpointSpec(
    path="/agent/sessions",
    method=HttpMethod.POST,
    level=ConformanceLevel.IDENTITY,
    description="Start a new session (handshake init)",
    auth_required=True,
)

SESSION_GET = EndpointSpec(
    path="/agent/sessions/{session_id}",
    method=HttpMethod.GET,
    level=ConformanceLevel.IDENTITY,
    description="Get session state",
    auth_required=True,
    idempotent=True,
)

SESSION_UPDATE = EndpointSpec(
    path="/agent/sessions/{session_id}",
    method=HttpMethod.PATCH,
    level=ConformanceLevel.IDENTITY,
    description="Update session (pause, resume, inject context)",
    auth_required=True,
)

SESSION_CLOSE = EndpointSpec(
    path="/agent/sessions/{session_id}",
    method=HttpMethod.DELETE,
    level=ConformanceLevel.IDENTITY,
    description="Close and terminate a session",
    auth_required=True,
)

IDENTITY_VERIFY = EndpointSpec(
    path="/agent/identity/verify",
    method=HttpMethod.POST,
    level=ConformanceLevel.IDENTITY,
    description="Cross-verify agent identity (challenge-response)",
    auth_required=True,
)

CONSENT_REQUEST = EndpointSpec(
    path="/agent/consent",
    method=HttpMethod.POST,
    level=ConformanceLevel.IDENTITY,
    description="Request data consent from the agent",
    auth_required=True,
)

CONSENT_REVOKE = EndpointSpec(
    path="/agent/consent/{grant_id}",
    method=HttpMethod.DELETE,
    level=ConformanceLevel.IDENTITY,
    description="Revoke a previously granted consent",
    auth_required=True,
)


# ---------------------------------------------------------------------------
# Level 5 -- PLATFORM
# ---------------------------------------------------------------------------

PRESENCE = EndpointSpec(
    path="/agent/presence",
    method=HttpMethod.GET,
    level=ConformanceLevel.PLATFORM,
    description="Get agent presence and availability",
    auth_required=False,
    idempotent=True,
)

AUDIT_LOG = EndpointSpec(
    path="/agent/audit",
    method=HttpMethod.GET,
    level=ConformanceLevel.PLATFORM,
    description="Retrieve audit log entries",
    auth_required=True,
    idempotent=True,
)

REGISTRY_RESOLVE = EndpointSpec(
    path="/agent/registry/resolve",
    method=HttpMethod.POST,
    level=ConformanceLevel.PLATFORM,
    description="Resolve an agent address to connection details",
    auth_required=True,
)

REGISTRY_REGISTER = EndpointSpec(
    path="/agent/registry/register",
    method=HttpMethod.POST,
    level=ConformanceLevel.PLATFORM,
    description="Register or update agent entry in the registry",
    auth_required=True,
)

REGISTRY_SEARCH = EndpointSpec(
    path="/agent/registry/search",
    method=HttpMethod.POST,
    level=ConformanceLevel.PLATFORM,
    description="Search for agents by capability across registries",
    auth_required=True,
    rate_limited=True,
)


# ---------------------------------------------------------------------------
# Aggregate registry
# ---------------------------------------------------------------------------

ALL_ENDPOINTS: list[EndpointSpec] = [
    # Level 0 -- Discovery
    AGENT_JSON,
    HEALTH,
    JWKS,
    # Level 1 -- Messaging
    MESSAGE,
    # Level 2 -- Tools
    TOOLS_LIST,
    TOOL_INVOKE,
    # Level 3 -- Task lifecycle
    TASK_STATUS,
    TASK_UPDATE,
    STREAM,
    # Level 4 -- Identity
    SESSION_START,
    SESSION_GET,
    SESSION_UPDATE,
    SESSION_CLOSE,
    IDENTITY_VERIFY,
    CONSENT_REQUEST,
    CONSENT_REVOKE,
    # Level 5 -- Platform
    PRESENCE,
    AUDIT_LOG,
    REGISTRY_RESOLVE,
    REGISTRY_REGISTER,
    REGISTRY_SEARCH,
]


def endpoints_for_level(level: ConformanceLevel) -> list[EndpointSpec]:
    """Return all endpoints required for a given conformance level and below.

    Args:
        level: The maximum conformance level to include.

    Returns:
        A list of ``EndpointSpec`` instances whose level is ``<= level``.

    Example::

        mandatory = endpoints_for_level(ConformanceLevel.DISCOVERY)
        # Returns [AGENT_JSON, HEALTH]
    """
    return [e for e in ALL_ENDPOINTS if e.level.value <= level.value]


def endpoints_at_level(level: ConformanceLevel) -> list[EndpointSpec]:
    """Return only the endpoints defined at exactly the given level.

    Args:
        level: The exact conformance level to filter by.

    Returns:
        A list of ``EndpointSpec`` instances whose level equals ``level``.
    """
    return [e for e in ALL_ENDPOINTS if e.level == level]
