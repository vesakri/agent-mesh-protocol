"""Attachments, callbacks, negotiation, and transport primitives."""

from ampro.transport.api_key_store import ApiKeyStore
from ampro.transport.attachment import Attachment, validate_attachment_url
from ampro.transport.callback import deliver_callback, validate_callback_url
from ampro.transport.events import EventNotification, EventSubscription, EventType
from ampro.transport.heartbeat import HeartbeatEmitter
from ampro.transport.jwks_cache import JWKSCache
from ampro.transport.negotiation import CapabilityNegotiator, NegotiationResult
from ampro.transport.task_redirect import TaskRedirectBody
from ampro.transport.task_revoke import TaskRevokeBody

__all__ = [
    # Attachment
    "Attachment", "validate_attachment_url",
    # Callback
    "validate_callback_url", "deliver_callback",
    # Negotiation
    "NegotiationResult", "CapabilityNegotiator",
    # Events
    "EventType", "EventSubscription", "EventNotification",
    # Heartbeat
    "HeartbeatEmitter",
    # Task redirect / revoke
    "TaskRedirectBody", "TaskRevokeBody",
    # JWKS
    "JWKSCache",
    # API keys
    "ApiKeyStore",
]
