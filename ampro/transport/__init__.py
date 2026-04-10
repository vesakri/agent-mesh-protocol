"""Attachments, callbacks, negotiation, and transport primitives."""

from ampro.transport.attachment import Attachment, validate_attachment_url
from ampro.transport.callback import validate_callback_url, deliver_callback
from ampro.transport.negotiation import NegotiationResult, CapabilityNegotiator
from ampro.transport.events import EventType, EventSubscription, EventNotification
from ampro.transport.heartbeat import HeartbeatEmitter
from ampro.transport.task_redirect import TaskRedirectBody
from ampro.transport.task_revoke import TaskRevokeBody
from ampro.transport.jwks_cache import JWKSCache
from ampro.transport.api_key_store import ApiKeyStore

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
