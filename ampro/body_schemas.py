"""
Agent Protocol — Body Type Schemas.

17 Pydantic models for all canonical body type payloads, as defined in the
Agent Mesh Protocol spec. Each model maps to a body.type string from the
message_types_registry.

Usage:
    from ampro.body_schemas import validate_body

    body = validate_body("task.create", {"description": "Find me a hotel"})
    # Returns TaskCreateBody instance

    body = validate_body("x-custom.type", {"foo": "bar"})
    # Returns raw dict — unknown types pass through

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST types — Creating work
# ---------------------------------------------------------------------------


class MessageBody(BaseModel):
    """body.type = 'message' — Free-form message with optional attachments."""

    text: str = Field(description="Message text content")
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional file or media attachments",
    )

    model_config = {"extra": "ignore"}


class TaskCreateBody(BaseModel):
    """body.type = 'task.create' — Create a new task."""

    description: str = Field(description="Human-readable task description")
    task_id: str | None = Field(default=None, description="Caller-supplied task ID")
    priority: Literal["low", "normal", "high", "urgent"] = Field(
        default="normal",
        description="Task priority level",
    )
    tools_required: list[str] | None = Field(
        default=None,
        description="Tools the assignee must support to execute this task",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary context data to pass to the assignee",
    )
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional file or media attachments",
    )
    timeout_seconds: int | None = Field(
        default=None,
        description="Maximum seconds to allow for task completion",
    )

    model_config = {"extra": "ignore"}


class TaskAssignBody(BaseModel):
    """body.type = 'task.assign' — Assign an existing task to an agent."""

    task_id: str = Field(description="ID of the task being assigned")
    assignee: str = Field(description="Agent address to assign the task to")
    reason: str | None = Field(default=None, description="Why this assignee was chosen")

    model_config = {"extra": "ignore"}


class TaskDelegateBody(BaseModel):
    """body.type = 'task.delegate' — Delegate a task with full chain context."""

    task_id: str = Field(description="ID of the task being delegated")
    description: str = Field(description="Description of the work to delegate")
    delegation_chain: list[dict[str, Any]] = Field(
        description="DelegationLink objects forming the authority chain",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary context to pass along with the delegation",
    )
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional file or media attachments",
    )

    model_config = {"extra": "ignore"}


class TaskSpawnBody(BaseModel):
    """body.type = 'task.spawn' — Spawn a child task from a parent."""

    parent_task_id: str = Field(description="ID of the parent task")
    task_id: str | None = Field(default=None, description="Optional child task ID")
    description: str = Field(description="Description of the child task")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Context inherited or injected for the child task",
    )

    model_config = {"extra": "ignore"}


class TaskQuoteBody(BaseModel):
    """body.type = 'task.quote' — Non-binding cost/time estimate for a task."""

    task_id: str = Field(description="ID of the task being quoted")
    expires_at: str = Field(description="ISO-8601 timestamp when this quote expires")
    estimated_cost_usd: float | None = Field(
        default=None,
        description="Estimated cost in USD",
    )
    estimated_tokens: int | None = Field(
        default=None,
        description="Estimated token usage",
    )
    estimated_duration_seconds: int | None = Field(
        default=None,
        description="Estimated duration in seconds",
    )
    breakdown: dict[str, Any] | None = Field(
        default=None,
        description="Itemized cost or time breakdown",
    )

    model_config = {"extra": "ignore"}


class NotificationBody(BaseModel):
    """body.type = 'notification' — Push a notification to an agent."""

    topic: str = Field(description="Notification topic or category")
    message: str = Field(description="Human-readable notification message")
    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured data payload",
    )
    expires_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when this notification expires",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# PATCH types — Lifecycle updates
# ---------------------------------------------------------------------------


class TaskProgressBody(BaseModel):
    """body.type = 'task.progress' — Report task progress."""

    task_id: str = Field(description="ID of the task being updated")
    percentage: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Completion percentage (0-100)",
    )
    message: str | None = Field(
        default=None,
        description="Human-readable progress message",
    )
    estimated_remaining_seconds: int | None = Field(
        default=None,
        description="Estimated seconds until task completion",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary progress metadata",
    )

    model_config = {"extra": "ignore"}


class TaskInputRequiredBody(BaseModel):
    """body.type = 'task.input_required' — Request additional input from sender."""

    task_id: str = Field(description="ID of the blocked task")
    reason: str = Field(description="Why input is required")
    prompt: str = Field(description="What to ask the user or calling agent")
    options: list[str] | None = Field(
        default=None,
        description="Optional list of valid response options",
    )
    consent_url: str | None = Field(
        default=None,
        description="URL for consent or authorization flow",
    )
    timeout_seconds: int | None = Field(
        default=None,
        description="How long to wait for a response before timing out",
    )

    model_config = {"extra": "ignore"}


class TaskEscalateBody(BaseModel):
    """body.type = 'task.escalate' — Escalate a task to a human or specific agent."""

    task_id: str = Field(description="ID of the task being escalated")
    escalate_to: Literal["sender_human", "local_human", "specific"] = Field(
        description="Who to escalate to",
    )
    target: str | None = Field(
        default=None,
        description="Target agent address when escalate_to='specific'",
    )
    reason: str = Field(description="Why escalation is needed")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Context to pass to the escalation target",
    )
    partial_result: Any | None = Field(
        default=None,
        description="Any partial work completed before escalation",
    )

    model_config = {"extra": "ignore"}


class TaskRerouteBody(BaseModel):
    """body.type = 'task.reroute' — Cancel or redirect a task."""

    task_id: str = Field(description="ID of the task to reroute")
    action: Literal["cancel", "redirect"] = Field(
        description="Reroute action to perform",
    )
    redirect_to: str | None = Field(
        default=None,
        description="Agent address to redirect to when action='redirect'",
    )
    reason: str = Field(description="Why the task is being rerouted")

    model_config = {"extra": "ignore"}


class TaskTransferBody(BaseModel):
    """body.type = 'task.transfer' — Transfer task ownership to another agent."""

    task_id: str = Field(description="ID of the task being transferred")
    transfer_to: str = Field(description="Agent address to transfer ownership to")
    reason: str = Field(description="Why the task is being transferred")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Context to pass to the new owner",
    )
    partial_result: Any | None = Field(
        default=None,
        description="Any partial work completed before transfer",
    )

    model_config = {"extra": "ignore"}


class TaskAcknowledgeBody(BaseModel):
    """body.type = 'task.acknowledge' — Acknowledge receipt and acceptance of a task."""

    task_id: str = Field(description="ID of the task being acknowledged")
    estimated_duration_seconds: int | None = Field(
        default=None,
        description="Estimated time to complete the task",
    )
    message: str | None = Field(
        default=None,
        description="Optional acknowledgement message",
    )
    upgraded_tier: str | None = Field(
        default=None,
        description="Upgraded trust tier granted for this task",
    )
    scopes: list[str] | None = Field(
        default=None,
        description="Scopes granted for task execution",
    )
    valid_for_session: str | None = Field(
        default=None,
        description="Session ID for which the trust upgrade is valid",
    )
    expires_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when granted permissions expire",
    )

    model_config = {"extra": "ignore"}


class TaskRejectBody(BaseModel):
    """body.type = 'task.reject' — Reject a task with reason."""

    task_id: str = Field(description="ID of the rejected task")
    reason: str = Field(description="Why the task was rejected")
    detail: str | None = Field(
        default=None,
        description="Additional detail about the rejection",
    )
    required_tier: str | None = Field(
        default=None,
        description="Trust tier required to accept this task",
    )
    required: list[str] | None = Field(
        default=None,
        description="Missing capabilities or permissions required",
    )
    supported: list[str] | None = Field(
        default=None,
        description="Capabilities the agent does support",
    )
    retry_eligible: bool = Field(
        default=False,
        description="Whether the sender can retry after meeting requirements",
    )
    retry_after_seconds: int | None = Field(
        default=None,
        description="How long to wait before retrying",
    )

    model_config = {"extra": "ignore"}


class TaskCompleteBody(BaseModel):
    """body.type = 'task.complete' — Signal successful task completion."""

    task_id: str = Field(description="ID of the completed task")
    result: Any = Field(description="The task result or output")
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional result attachments",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary completion metadata",
    )
    delegation_chain: list[dict[str, Any]] | None = Field(
        default=None,
        description="Full delegation chain for traceability",
    )
    cost_usd: float | None = Field(
        default=None,
        description="Actual cost incurred in USD",
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Actual wall-clock duration in seconds",
    )
    cost_receipt: dict[str, Any] | None = Field(
        default=None,
        description="Per-hop cost receipt for delegation chain cost attribution",
    )

    model_config = {"extra": "ignore"}


class TaskErrorBody(BaseModel):
    """body.type = 'task.error' — Report a terminal task error."""

    task_id: str | None = Field(
        default=None,
        description="ID of the failed task (may be absent for routing errors)",
    )
    reason: str = Field(description="Short machine-readable error reason")
    detail: str | None = Field(
        default=None,
        description="Human-readable error detail",
    )
    retry_eligible: bool = Field(
        description="Whether the caller can retry this task",
    )
    retry_after_seconds: int | None = Field(
        default=None,
        description="How long to wait before retrying",
    )
    partial_result: Any | None = Field(
        default=None,
        description="Any partial result produced before the error",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Diagnostic context for debugging",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# PUT types — Responding
# ---------------------------------------------------------------------------


class TaskResponseBody(BaseModel):
    """body.type = 'task.response' — Structured response to a task."""

    task_id: str | None = Field(
        default=None,
        description="ID of the task this response corresponds to",
    )
    text: str = Field(description="Human-readable response text")
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional response attachments",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured response data",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Compliance types (Section 9.4)
# ---------------------------------------------------------------------------


class DataConsentRequestBody(BaseModel):
    """body.type = 'data.consent_request' — Request consent for scoped access."""

    requester: str = Field(description="Agent ID requesting consent")
    target: str = Field(description="Agent ID whose consent is sought")
    scopes: list[str] = Field(description="Requested permission scopes")
    reason: str = Field(description="Human-readable reason")
    ttl_seconds: int = Field(default=86400, description="Grant lifetime")

    model_config = {"extra": "ignore"}


class DataConsentResponseBody(BaseModel):
    """body.type = 'data.consent_response' — Grant or deny consent."""

    grant_id: str = Field(default="", description="Unique grant ID if approved")
    requester: str = Field(description="Agent that requested consent")
    target: str = Field(description="Agent that responded")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")
    approved: bool = Field(description="Whether consent was granted")
    expires_at: str | None = Field(default=None, description="When grant expires")

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_BODY_TYPE_REGISTRY: dict[str, type[BaseModel]] = {
    # POST types
    "message": MessageBody,
    "task.create": TaskCreateBody,
    "task.assign": TaskAssignBody,
    "task.delegate": TaskDelegateBody,
    "task.spawn": TaskSpawnBody,
    "task.quote": TaskQuoteBody,
    "notification": NotificationBody,
    # PATCH types
    "task.progress": TaskProgressBody,
    "task.input_required": TaskInputRequiredBody,
    "task.escalate": TaskEscalateBody,
    "task.reroute": TaskRerouteBody,
    "task.transfer": TaskTransferBody,
    "task.acknowledge": TaskAcknowledgeBody,
    "task.reject": TaskRejectBody,
    "task.complete": TaskCompleteBody,
    "task.error": TaskErrorBody,
    # PUT types
    "task.response": TaskResponseBody,
    # Compliance types
    "data.consent_request": DataConsentRequestBody,
    "data.consent_response": DataConsentResponseBody,
    # Erasure & export use models from compliance_types (imported lazily)
    # Handshake types (imported lazily below)
}

# Register compliance_types models lazily to avoid circular imports
def _register_compliance_body_types() -> None:
    """Register erasure + export body types from compliance_types module."""
    try:
        from ampro.compliance_types import (
            ErasureRequest, ErasureResponse, ExportRequest, ExportResponse,
        )
        _BODY_TYPE_REGISTRY["data.erasure_request"] = ErasureRequest
        _BODY_TYPE_REGISTRY["data.erasure_response"] = ErasureResponse
        _BODY_TYPE_REGISTRY["data.export_request"] = ExportRequest
        _BODY_TYPE_REGISTRY["data.export_response"] = ExportResponse
    except ImportError:
        pass  # compliance_types not available — skip

_register_compliance_body_types()


def _register_handshake_body_types() -> None:
    """Register session handshake body types from handshake module."""
    try:
        from ampro.handshake import (
            SessionInitBody, SessionEstablishedBody, SessionConfirmBody,
            SessionPingBody, SessionPongBody,
            SessionPauseBody, SessionResumeBody, SessionCloseBody,
        )
        _BODY_TYPE_REGISTRY["session.init"] = SessionInitBody
        _BODY_TYPE_REGISTRY["session.established"] = SessionEstablishedBody
        _BODY_TYPE_REGISTRY["session.confirm"] = SessionConfirmBody
        _BODY_TYPE_REGISTRY["session.ping"] = SessionPingBody
        _BODY_TYPE_REGISTRY["session.pong"] = SessionPongBody
        _BODY_TYPE_REGISTRY["session.pause"] = SessionPauseBody
        _BODY_TYPE_REGISTRY["session.resume"] = SessionResumeBody
        _BODY_TYPE_REGISTRY["session.close"] = SessionCloseBody
    except ImportError:
        pass  # handshake module not available — skip

_register_handshake_body_types()


def _register_challenge_body_types() -> None:
    """Register anti-abuse challenge body types from challenge module."""
    try:
        from ampro.challenge import TaskChallengeBody, TaskChallengeResponseBody
        _BODY_TYPE_REGISTRY["task.challenge"] = TaskChallengeBody
        _BODY_TYPE_REGISTRY["task.challenge_response"] = TaskChallengeResponseBody
    except ImportError:
        pass  # challenge module not available — skip

_register_challenge_body_types()


def _register_v012_body_types() -> None:
    """Register v0.1.2 body types: key revocation, tool consent, trust upgrade."""
    try:
        from ampro.key_revocation import KeyRevocationBody
        _BODY_TYPE_REGISTRY["key.revocation"] = KeyRevocationBody
    except ImportError:
        pass
    try:
        from ampro.tool_consent import ToolConsentRequestBody, ToolConsentGrantBody
        _BODY_TYPE_REGISTRY["tool.consent_request"] = ToolConsentRequestBody
        _BODY_TYPE_REGISTRY["tool.consent_grant"] = ToolConsentGrantBody
    except ImportError:
        pass
    try:
        from ampro.trust_upgrade import TrustUpgradeRequestBody, TrustUpgradeResponseBody
        _BODY_TYPE_REGISTRY["trust.upgrade_request"] = TrustUpgradeRequestBody
        _BODY_TYPE_REGISTRY["trust.upgrade_response"] = TrustUpgradeResponseBody
    except ImportError:
        pass

_register_v012_body_types()


def _register_v013_body_types() -> None:
    """Register v0.1.3 body types: agent lifecycle."""
    try:
        from ampro.agent_lifecycle import AgentDeactivationNoticeBody
        _BODY_TYPE_REGISTRY["agent.deactivation_notice"] = AgentDeactivationNoticeBody
    except ImportError:
        pass

_register_v013_body_types()


def _register_v014_body_types() -> None:
    """Register v0.1.4 body types: task redirect."""
    try:
        from ampro.task_redirect import TaskRedirectBody
        _BODY_TYPE_REGISTRY["task.redirect"] = TaskRedirectBody
    except ImportError:
        pass

_register_v014_body_types()


def _register_v015_body_types() -> None:
    """Register v0.1.5 body types: task revoke."""
    try:
        from ampro.task_revoke import TaskRevokeBody
        _BODY_TYPE_REGISTRY["task.revoke"] = TaskRevokeBody
    except ImportError:
        pass

_register_v015_body_types()


def _register_v016_body_types() -> None:
    """Register v0.1.6 body types: erasure propagation, consent revoke."""
    try:
        from ampro.erasure_propagation import ErasurePropagationStatusBody
        _BODY_TYPE_REGISTRY["erasure.propagation_status"] = ErasurePropagationStatusBody
    except ImportError:
        pass
    try:
        from ampro.consent_revoke import DataConsentRevokeBody
        _BODY_TYPE_REGISTRY["data.consent_revoke"] = DataConsentRevokeBody
    except ImportError:
        pass

_register_v016_body_types()


def validate_body(body_type: str, body: dict[str, Any]) -> BaseModel | dict[str, Any]:
    """Validate a body dict against its body_type schema.

    For known canonical body types, returns a validated Pydantic model instance.
    For unknown/extension types (e.g., "x-custom.type"), returns the raw dict
    unchanged — allowing forward-compatible extension types to pass through.

    Args:
        body_type: The body.type string (e.g., "task.create", "message").
        body:      The raw body dict to validate.

    Returns:
        A validated Pydantic model for known types, or the raw dict for
        extension types.

    Raises:
        pydantic.ValidationError: If the body fails schema validation for a
                                  known body_type.
    """
    model_cls = _BODY_TYPE_REGISTRY.get(body_type)
    if model_cls is None:
        return body
    return model_cls.model_validate(body)
