"""
agent-protocol — Universal agent-to-agent communication protocol.

The protocol answers four questions:
  - Can I reach you?   → agent:// addressing
  - Can I trust you?   → 4-tier trust (internal/owner/verified/external)
  - What can you do?   → 8 capability groups, 6 progressive levels
  - How do we talk?    → POST /agent/message with typed body schemas

Install: pip install agent-protocol
"""

# --- Core envelope ---
from ampro.core.envelope import AgentMessage, STANDARD_HEADERS
from ampro.core.status import AgentStatus
from ampro.core.capabilities import CapabilityGroup, CapabilityLevel, CapabilitySet
from ampro.streaming.events import StreamingEvent, StreamingEventType
from ampro.trust.tiers import TrustTier, TrustConfig, CLOCK_SKEW_SECONDS

# --- Addressing ---
from ampro.core.addressing import AgentAddress, AddressType, parse_agent_uri, normalize_shorthand

# --- Identity & auth ---
from ampro.identity.types import IdentityProof, ConsentScope, ConsentRequest, ConsentGrant
from ampro.identity.auth_methods import AuthMethod, ParsedAuth, parse_authorization

# --- Body type schemas ---
from ampro.core.body_schemas import (
    MessageBody, TaskCreateBody, TaskAssignBody, TaskDelegateBody,
    TaskSpawnBody, TaskQuoteBody, NotificationBody,
    TaskProgressBody, TaskInputRequiredBody, TaskEscalateBody,
    TaskRerouteBody, TaskTransferBody, TaskAcknowledgeBody,
    TaskRejectBody, TaskCompleteBody, TaskErrorBody,
    TaskResponseBody, validate_body,
    DataConsentRequestBody, DataConsentResponseBody,
)

# --- Delegation ---
from ampro.delegation.chain import (
    DelegationLink, DelegationChain,
    validate_chain, validate_scope_narrowing, sign_delegation,
    parse_chain_budget, parse_visited_agents,
    check_visited_agents_loop, check_visited_agents_limit,
)

# --- Events & sessions ---
from ampro.transport.events import EventType, EventSubscription, EventNotification
from ampro.session.types import SessionState, SessionConfig, SessionContext
from ampro.session.presence import PresenceState, PresenceUpdate

# --- Attachments ---
from ampro.transport.attachment import Attachment, validate_attachment_url

# --- Compliance ---
from ampro.compliance.types import (
    ContentClassification, RetentionPolicy,
    ErasureRequest, ErasureResponse, ExportRequest, ExportResponse,
)
from ampro.compliance.middleware import (
    check_content_classification, check_minor_protection,
    requires_audit, ComplianceCheckResult,
)
from ampro.compliance.audit_logger import AuditLogger, AuditEntry
from ampro.compliance.erasure import ErasureProcessor

# --- Security modules ---
from ampro.security.dedup import InMemoryDedupStore, DedupStore
from ampro.security.nonce_tracker import NonceTracker
from ampro.security.rate_limiter import RateLimiter
from ampro.security.rate_limit import RateLimitInfo, format_rate_limit_headers
from ampro.security.concurrency_limiter import ConcurrencyLimiter
from ampro.security.sender_tracker import SenderTracker, SenderState
from ampro.transport.jwks_cache import JWKSCache
from ampro.transport.api_key_store import ApiKeyStore

# --- Operational types ---
from ampro.agent.health import HealthResponse
from ampro.security.circuit_breaker import CircuitState, CircuitBreakerInfo
from ampro.transport.heartbeat import HeartbeatEmitter
from ampro.transport.callback import validate_callback_url, deliver_callback
from ampro.core.message_middleware import (
    validate_message_body, build_negotiation_headers,
    check_message_size, MessageSizeError,
)

# --- Registry & discovery ---
from ampro.registry.types import RegistryResolution, RegistryRegistration
from ampro.registry.search import RegistrySearchRequest, RegistrySearchMatch, RegistrySearchResult
from ampro.agent.schema import AgentJson

# --- Cross-verification ---
from ampro.identity.cross_verification import (
    cross_verify_identifiers, check_all_verified,
    get_failed_identifiers, VerificationResult,
)

# --- Trust scoring ---
from ampro.trust.score import (
    TrustFactor, TrustScore, TrustPolicy,
    calculate_trust_score, score_to_policy,
)

# --- Trust resolution ---
from ampro.trust.resolver import resolve_trust_tier

# --- Trust upgrade ---
from ampro.trust.upgrade import TrustUpgradeRequestBody, TrustUpgradeResponseBody

# --- Handshake ---
from ampro.session.handshake import (
    HandshakeState, HandshakeStateMachine,
    SessionInitBody, SessionEstablishedBody, SessionConfirmBody,
    SessionPingBody, SessionPongBody,
    SessionPauseBody, SessionResumeBody, SessionCloseBody,
)

# --- Visibility & contact policies ---
from ampro.agent.visibility import (
    VisibilityLevel, ContactPolicy, VisibilityConfig,
    check_contact_allowed, filter_agent_json,
)

# --- Session binding ---
from ampro.session.binding import (
    SessionBinding, derive_binding_token,
    create_message_binding, verify_message_binding,
)

# --- Context schemas ---
from ampro.agent.context_schema import ContextSchemaInfo, parse_schema_urn, check_schema_supported

# --- Challenge (anti-abuse) ---
from ampro.security.challenge import ChallengeReason, TaskChallengeBody, TaskChallengeResponseBody

# --- Key revocation ---
from ampro.security.key_revocation import RevocationReason, KeyRevocationBody, is_revocation_authentic

# --- Tool consent ---
from ampro.agent.tool_consent import ToolConsentRequestBody, ToolConsentGrantBody, ToolDefinition

# --- Backpressure ---
from ampro.streaming.backpressure import StreamAckEvent, StreamPauseEvent, StreamResumeEvent

# --- Agent lifecycle ---
from ampro.agent.lifecycle import AgentLifecycleStatus, AgentDeactivationNoticeBody

# --- Cost receipts ---
from ampro.delegation.cost_receipt import CostReceipt, CostReceiptChain

# --- Task redirect ---
from ampro.transport.task_redirect import TaskRedirectBody

# --- Tracing ---
from ampro.delegation.tracing import (
    TraceContext, generate_trace_id, generate_span_id,
    inject_trace_headers, extract_trace_context,
)

# --- Task revoke ---
from ampro.transport.task_revoke import TaskRevokeBody

# --- Priority ---
from ampro.core.priority import Priority

# --- Jurisdiction ---
from ampro.compliance.jurisdiction import JurisdictionInfo, validate_jurisdiction_code, check_jurisdiction_conflict

# --- Erasure propagation ---
from ampro.compliance.erasure_propagation import ErasurePropagationStatus, ErasurePropagationStatusBody

# --- Consent revocation ---
from ampro.compliance.consent_revoke import DataConsentRevokeBody

# --- Data residency ---
from ampro.compliance.data_residency import DataResidency, validate_residency_region, check_residency_violation

# --- Stream channels ---
from ampro.streaming.channel import StreamChannel, StreamChannelOpenEvent, StreamChannelCloseEvent

# --- Stream checkpoints ---
from ampro.streaming.checkpoint import StreamCheckpointEvent

# --- Stream auth ---
from ampro.streaming.auth import StreamAuthRefreshEvent

# --- Identity linking ---
from ampro.identity.link import IdentityLinkProofBody

# --- Registry federation ---
from ampro.registry.federation import RegistryFederationRequest, RegistryFederationResponse

# --- Identity migration ---
from ampro.identity.migration import IdentityMigrationBody

# --- Audit attestation ---
from ampro.compliance.audit_attestation import AuditAttestationBody

# --- Encryption ---
from ampro.security.encryption import EncryptedBody, CONTENT_ENCRYPTION_HEADER

# --- Trust proof ---
from ampro.trust.proof import TrustProofBody

# --- Certifications ---
from ampro.compliance.certifications import CertificationLink

# --- Negotiation & versioning ---
from ampro.transport.negotiation import NegotiationResult, CapabilityNegotiator
from ampro.core.versioning import SUPPORTED_VERSIONS, CURRENT_VERSION, check_version, negotiate_version

# --- Wire binding (HTTP transport contract) ---
from ampro.wire.endpoints import ConformanceLevel, EndpointSpec, ALL_ENDPOINTS, endpoints_for_level
from ampro.wire.errors import ProblemDetail, ErrorType
from ampro.wire.config import WireConfig, DEFAULTS as WIRE_DEFAULTS
from ampro.wire.body_type_map import ResponseMode, BodyTypeBinding, BODY_TYPE_BINDINGS, binding_for

__version__ = "0.2.1"

__all__ = [
    # Core
    "AgentMessage", "STANDARD_HEADERS", "AgentStatus",
    "CapabilityGroup", "CapabilityLevel", "CapabilitySet",
    "StreamingEvent", "StreamingEventType",
    "TrustTier", "TrustConfig", "CLOCK_SKEW_SECONDS",
    # Addressing
    "AgentAddress", "AddressType", "parse_agent_uri", "normalize_shorthand",
    # Identity & auth
    "IdentityProof", "ConsentScope", "ConsentRequest", "ConsentGrant",
    "AuthMethod", "ParsedAuth", "parse_authorization",
    # Body schemas
    "MessageBody", "TaskCreateBody", "TaskAssignBody", "TaskDelegateBody",
    "TaskSpawnBody", "TaskQuoteBody", "NotificationBody",
    "TaskProgressBody", "TaskInputRequiredBody", "TaskEscalateBody",
    "TaskRerouteBody", "TaskTransferBody", "TaskAcknowledgeBody",
    "TaskRejectBody", "TaskCompleteBody", "TaskErrorBody",
    "TaskResponseBody", "validate_body",
    "DataConsentRequestBody", "DataConsentResponseBody",
    # Delegation
    "DelegationLink", "DelegationChain",
    "validate_chain", "validate_scope_narrowing", "sign_delegation",
    "parse_chain_budget", "parse_visited_agents",
    "check_visited_agents_loop", "check_visited_agents_limit",
    # Events & sessions
    "EventType", "EventSubscription", "EventNotification",
    "SessionState", "SessionConfig", "SessionContext",
    "PresenceState", "PresenceUpdate",
    # Attachments
    "Attachment", "validate_attachment_url",
    # Compliance
    "ContentClassification", "RetentionPolicy",
    "ErasureRequest", "ErasureResponse", "ExportRequest", "ExportResponse",
    "check_content_classification", "check_minor_protection",
    "requires_audit", "ComplianceCheckResult",
    "AuditLogger", "AuditEntry", "ErasureProcessor",
    # Security
    "InMemoryDedupStore", "DedupStore", "NonceTracker",
    "RateLimiter", "RateLimitInfo", "format_rate_limit_headers",
    "ConcurrencyLimiter", "SenderTracker", "SenderState",
    "JWKSCache", "ApiKeyStore",
    # Operational
    "HealthResponse", "CircuitState", "CircuitBreakerInfo",
    "HeartbeatEmitter", "validate_callback_url", "deliver_callback",
    "validate_message_body", "build_negotiation_headers",
    "check_message_size", "MessageSizeError",
    # Registry & discovery
    "RegistryResolution", "RegistryRegistration",
    "RegistrySearchRequest", "RegistrySearchMatch", "RegistrySearchResult",
    "AgentJson",
    # Cross-verification
    "cross_verify_identifiers", "check_all_verified",
    "get_failed_identifiers", "VerificationResult",
    # Trust scoring
    "TrustFactor", "TrustScore", "TrustPolicy",
    "calculate_trust_score", "score_to_policy",
    # Trust resolution
    "resolve_trust_tier",
    # Trust upgrade
    "TrustUpgradeRequestBody", "TrustUpgradeResponseBody",
    # Handshake
    "HandshakeState", "HandshakeStateMachine",
    "SessionInitBody", "SessionEstablishedBody", "SessionConfirmBody",
    "SessionPingBody", "SessionPongBody",
    "SessionPauseBody", "SessionResumeBody", "SessionCloseBody",
    # Visibility & contact policies
    "VisibilityLevel", "ContactPolicy", "VisibilityConfig",
    "check_contact_allowed", "filter_agent_json",
    # Session binding
    "SessionBinding", "derive_binding_token",
    "create_message_binding", "verify_message_binding",
    # Context schemas
    "ContextSchemaInfo", "parse_schema_urn", "check_schema_supported",
    # Challenge (anti-abuse)
    "ChallengeReason", "TaskChallengeBody", "TaskChallengeResponseBody",
    # Key revocation
    "RevocationReason", "KeyRevocationBody", "is_revocation_authentic",
    # Tool consent
    "ToolConsentRequestBody", "ToolConsentGrantBody", "ToolDefinition",
    # Backpressure
    "StreamAckEvent", "StreamPauseEvent", "StreamResumeEvent",
    # Agent lifecycle
    "AgentLifecycleStatus", "AgentDeactivationNoticeBody",
    # Cost receipts
    "CostReceipt", "CostReceiptChain",
    # Task redirect
    "TaskRedirectBody",
    # Tracing
    "TraceContext", "generate_trace_id", "generate_span_id",
    "inject_trace_headers", "extract_trace_context",
    # Task revoke
    "TaskRevokeBody",
    # Priority
    "Priority",
    # Jurisdiction
    "JurisdictionInfo", "validate_jurisdiction_code", "check_jurisdiction_conflict",
    # Erasure propagation
    "ErasurePropagationStatus", "ErasurePropagationStatusBody",
    # Consent revocation
    "DataConsentRevokeBody",
    # Data residency
    "DataResidency", "validate_residency_region", "check_residency_violation",
    # Stream channels
    "StreamChannel", "StreamChannelOpenEvent", "StreamChannelCloseEvent",
    # Stream checkpoints
    "StreamCheckpointEvent",
    # Stream auth
    "StreamAuthRefreshEvent",
    # Identity linking
    "IdentityLinkProofBody",
    # Registry federation
    "RegistryFederationRequest", "RegistryFederationResponse",
    # Identity migration
    "IdentityMigrationBody",
    # Audit attestation
    "AuditAttestationBody",
    # Encryption
    "EncryptedBody", "CONTENT_ENCRYPTION_HEADER",
    # Trust proof
    "TrustProofBody",
    # Certifications
    "CertificationLink",
    # Negotiation & versioning
    "NegotiationResult", "CapabilityNegotiator",
    "SUPPORTED_VERSIONS", "CURRENT_VERSION", "check_version", "negotiate_version",
    # Wire binding (HTTP transport contract)
    "ConformanceLevel", "EndpointSpec", "ALL_ENDPOINTS", "endpoints_for_level",
    "ProblemDetail", "ErrorType",
    "WireConfig", "WIRE_DEFAULTS",
    "ResponseMode", "BodyTypeBinding", "BODY_TYPE_BINDINGS", "binding_for",
]
