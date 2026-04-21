"""Agent schema, visibility, lifecycle, and tools."""

from ampro.agent.context_schema import (
    ContextSchemaInfo,
    check_schema_supported,
    parse_schema_urn,
)
from ampro.agent.health import HealthResponse
from ampro.agent.lifecycle import AgentDeactivationNoticeBody, AgentLifecycleStatus
from ampro.agent.schema import AgentJson
from ampro.agent.tool_consent import (
    ToolConsentGrantBody,
    ToolConsentRequestBody,
    ToolDefinition,
)
from ampro.agent.visibility import (
    ContactPolicy,
    VisibilityConfig,
    VisibilityLevel,
    check_contact_allowed,
    filter_agent_json,
)

__all__ = [
    # Schema
    "AgentJson",
    # Visibility
    "VisibilityLevel", "ContactPolicy", "VisibilityConfig",
    "check_contact_allowed", "filter_agent_json",
    # Lifecycle
    "AgentLifecycleStatus", "AgentDeactivationNoticeBody",
    # Tool consent
    "ToolConsentRequestBody", "ToolConsentGrantBody", "ToolDefinition",
    # Health
    "HealthResponse",
    # Context schema
    "ContextSchemaInfo", "parse_schema_urn", "check_schema_supported",
]
