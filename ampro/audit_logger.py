"""
Agent Protocol — Audit Logger.

Per-PII-message audit logging with hash chain integrity.

Spec ref: Section 8.5
- Minimum record: message_id, timestamp, sender, recipient, body_type,
  classification, trust_tier, action_taken
- Append-only with hash-chain integrity
- 1-year minimum retention
"""

from __future__ import annotations

import hashlib
import json
import logging
import time

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditEntry(BaseModel):
    """A single audit log entry."""

    message_id: str
    timestamp: float = Field(default_factory=time.time)
    sender: str
    recipient: str
    body_type: str
    content_classification: str = "public"
    trust_tier: str = "external"
    session_id: str = ""
    action_taken: str = "processed"
    tools_invoked: list[str] = Field(default_factory=list)
    hash: str = ""
    previous_hash: str = ""

    model_config = {"extra": "ignore"}


class AuditLogger:
    """Append-only audit logger with hash chain."""

    def __init__(self):
        self._entries: list[AuditEntry] = []
        self._last_hash: str = "0" * 64

    def log(self, entry: AuditEntry) -> AuditEntry:
        """Append an entry with hash chain integrity."""
        entry.previous_hash = self._last_hash
        content = json.dumps({
            "message_id": entry.message_id,
            "timestamp": entry.timestamp,
            "sender": entry.sender,
            "recipient": entry.recipient,
            "body_type": entry.body_type,
            "content_classification": entry.content_classification,
            "trust_tier": entry.trust_tier,
            "action_taken": entry.action_taken,
            "previous_hash": entry.previous_hash,
        }, sort_keys=True)
        entry.hash = hashlib.sha256(content.encode()).hexdigest()
        self._last_hash = entry.hash
        self._entries.append(entry)
        logger.info("Audit: %s %s→%s [%s]", entry.message_id, entry.sender, entry.recipient, entry.action_taken)
        return entry

    def get_entries(self, message_id: str | None = None) -> list[AuditEntry]:
        """Query audit entries, optionally filtered by message_id."""
        if message_id:
            return [e for e in self._entries if e.message_id == message_id]
        return list(self._entries)

    def verify_chain(self) -> bool:
        """Verify hash chain integrity. Returns True if valid."""
        prev_hash = "0" * 64
        for entry in self._entries:
            if entry.previous_hash != prev_hash:
                return False
            content = json.dumps({
                "message_id": entry.message_id,
                "timestamp": entry.timestamp,
                "sender": entry.sender,
                "recipient": entry.recipient,
                "body_type": entry.body_type,
                "content_classification": entry.content_classification,
                "trust_tier": entry.trust_tier,
                "action_taken": entry.action_taken,
                "previous_hash": entry.previous_hash,
            }, sort_keys=True)
            expected = hashlib.sha256(content.encode()).hexdigest()
            if entry.hash != expected:
                return False
            prev_hash = entry.hash
        return True

    @property
    def count(self) -> int:
        return len(self._entries)
