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
from ampro.envelope import AgentMessage, STANDARD_HEADERS
from ampro.status import AgentStatus
from ampro.capabilities import CapabilityGroup, CapabilityLevel, CapabilitySet
from ampro.streaming import StreamingEvent, StreamingEventType
from ampro.trust import TrustTier, TrustConfig, CLOCK_SKEW_SECONDS

# --- Addressing ---
from ampro.addressing import AgentAddress, AddressType, parse_agent_uri, normalize_shorthand

# --- Identity & auth ---
from ampro.identity_types import IdentityProof, ConsentScope, ConsentRequest, ConsentGrant
from ampro.auth_methods import AuthMethod, ParsedAuth, parse_authorization

# --- Body type schemas ---
from ampro.body_schemas import (
    MessageBody, TaskCreateBody, TaskAssignBody, TaskDelegateBody,
    TaskSpawnBody, TaskQuoteBody, NotificationBody,
    TaskProgressBody, TaskInputRequiredBody, TaskEscalateBody,
    TaskRerouteBody, TaskTransferBody, TaskAcknowledgeBody,
    TaskRejectBody, TaskCompleteBody, TaskErrorBody,
    TaskResponseBody, validate_body,
)

# --- Delegation ---
from ampro.delegation_chain import (
    DelegationLink, DelegationChain,
    validate_chain, validate_scope_narrowing, sign_delegation,
    parse_chain_budget, parse_visited_agents,
    check_visited_agents_loop, check_visited_agents_limit,
)

# --- Events & sessions ---
from ampro.events_types import EventType, EventSubscription, EventNotification
from ampro.session_types import SessionState, SessionConfig, SessionContext
from ampro.presence_types import PresenceState, PresenceUpdate

# --- Attachments ---
from ampro.attachment_types import Attachment, validate_attachment_url

# --- Compliance ---
from ampro.compliance_types import (
    ContentClassification, JurisdictionInfo, RetentionPolicy,
    ErasureRequest, ErasureResponse, ExportRequest, ExportResponse,
)
from ampro.compliance_middleware import (
    check_content_classification, check_minor_protection,
    requires_audit, ComplianceCheckResult,
)
from ampro.audit_logger import AuditLogger, AuditEntry
from ampro.erasure_processor import ErasureProcessor

# --- Security modules ---
from ampro.dedup import InMemoryDedupStore, DedupStore
from ampro.nonce_tracker import NonceTracker
from ampro.rate_limiter import RateLimiter
from ampro.rate_limit import RateLimitInfo, format_rate_limit_headers
from ampro.concurrency_limiter import ConcurrencyLimiter
from ampro.sender_tracker import SenderTracker, SenderState
from ampro.jwks_cache import JWKSCache
from ampro.api_key_store import ApiKeyStore

# --- Operational types ---
from ampro.health_types import HealthResponse
from ampro.circuit_breaker_types import CircuitState, CircuitBreakerInfo
from ampro.heartbeat import HeartbeatEmitter
from ampro.callback_delivery import validate_callback_url, deliver_callback
from ampro.message_middleware import (
    validate_message_body, build_negotiation_headers,
    check_message_size, MessageSizeError,
)

# --- Registry & discovery ---
from ampro.registry_types import RegistryResolution, RegistryRegistration
from ampro.agent_json_schema import AgentJson

# --- Cross-verification ---
from ampro.cross_verification import (
    cross_verify_identifiers, check_all_verified,
    get_failed_identifiers, VerificationResult,
)

# --- Trust scoring ---
from ampro.trust_score import (
    TrustFactor, TrustScore, TrustPolicy,
    calculate_trust_score, score_to_policy,
)

# --- Trust resolution ---
from ampro.trust_resolver import resolve_trust_tier

# --- Trust upgrade ---
from ampro.trust_upgrade import TrustUpgradeRequestBody, TrustUpgradeResponseBody

# --- Handshake ---
from ampro.handshake import (
    HandshakeState, HandshakeStateMachine,
    SessionInitBody, SessionEstablishedBody, SessionConfirmBody,
    SessionPingBody, SessionPongBody,
    SessionPauseBody, SessionResumeBody, SessionCloseBody,
)

# --- Visibility & contact policies ---
from ampro.visibility import (
    VisibilityLevel, ContactPolicy, VisibilityConfig,
    check_contact_allowed, filter_agent_json,
)

# --- Session binding ---
from ampro.session_binding import (
    SessionBinding, derive_binding_token,
    create_message_binding, verify_message_binding,
)

# --- Context schemas ---
from ampro.context_schema import ContextSchemaInfo, parse_schema_urn, check_schema_supported

# --- Challenge (anti-abuse) ---
from ampro.challenge import ChallengeReason, TaskChallengeBody, TaskChallengeResponseBody

# --- Key revocation ---
from ampro.key_revocation import RevocationReason, KeyRevocationBody

# --- Tool consent ---
from ampro.tool_consent import ToolConsentRequestBody, ToolConsentGrantBody, ToolDefinition

# --- Backpressure ---
from ampro.backpressure import StreamAckEvent, StreamPauseEvent, StreamResumeEvent

# --- Agent lifecycle ---
from ampro.agent_lifecycle import AgentLifecycleStatus, AgentDeactivationNoticeBody

# --- Cost receipts ---
from ampro.cost_receipt import CostReceipt, CostReceiptChain

# --- Negotiation & versioning ---
from ampro.negotiation import NegotiationResult, CapabilityNegotiator
from ampro.versioning import SUPPORTED_VERSIONS, CURRENT_VERSION, check_version, negotiate_version

__version__ = "0.1.3"

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
    "ContentClassification", "JurisdictionInfo", "RetentionPolicy",
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
    "RegistryResolution", "RegistryRegistration", "AgentJson",
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
    "RevocationReason", "KeyRevocationBody",
    # Tool consent
    "ToolConsentRequestBody", "ToolConsentGrantBody", "ToolDefinition",
    # Backpressure
    "StreamAckEvent", "StreamPauseEvent", "StreamResumeEvent",
    # Agent lifecycle
    "AgentLifecycleStatus", "AgentDeactivationNoticeBody",
    # Cost receipts
    "CostReceipt", "CostReceiptChain",
    # Negotiation & versioning
    "NegotiationResult", "CapabilityNegotiator",
    "SUPPORTED_VERSIONS", "CURRENT_VERSION", "check_version", "negotiate_version",
]
