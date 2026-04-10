"""Agent schema, visibility, lifecycle, and tools."""

from ampro.agent.schema import AgentJson
from ampro.agent.visibility import (
    VisibilityLevel, ContactPolicy, VisibilityConfig,
    check_contact_allowed, filter_agent_json,
)
from ampro.agent.lifecycle import AgentLifecycleStatus, AgentDeactivationNoticeBody
from ampro.agent.tool_consent import (
    ToolConsentRequestBody, ToolConsentGrantBody, ToolDefinition,
)
from ampro.agent.health import HealthResponse
from ampro.agent.context_schema import (
    ContextSchemaInfo, parse_schema_urn, check_schema_supported,
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
