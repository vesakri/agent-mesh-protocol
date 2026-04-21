"""Tests for audit log append-only storage (Task 1.4).

Validates:
- AuditStorage protocol & InMemoryAuditStorage implementation
- Sequence number assignment
- Chain verification detects gaps, tampering, and removal
"""
from __future__ import annotations

import pytest

from ampro.compliance.audit_logger import (
    AuditEntry,
    AuditLogger,
    AuditStorage,
    InMemoryAuditStorage,
)


def _make_entry(i: int) -> AuditEntry:
    """Helper: build a minimal AuditEntry for test ``i``."""
    return AuditEntry(
        message_id=f"msg-{i:03d}",
        sender=f"agent://sender-{i}.example.com",
        recipient=f"agent://recipient-{i}.example.com",
        body_type="message.send",
    )


# ── InMemoryAuditStorage unit tests ─────────────────────────────────────

class TestInMemoryAuditStorage:
    """Tests for the default in-memory storage backend."""

    def test_stores_and_retrieves_in_order(self):
        storage = InMemoryAuditStorage()
        entries = [_make_entry(i) for i in range(4)]
        for e in entries:
            storage.append(e)
        retrieved = storage.entries()
        assert len(retrieved) == 4
        for idx, e in enumerate(retrieved):
            assert e.message_id == f"msg-{idx:03d}"

    def test_tail_returns_last_entry(self):
        storage = InMemoryAuditStorage()
        storage.append(_make_entry(0))
        storage.append(_make_entry(1))
        tail = storage.tail()
        assert tail is not None
        assert tail.message_id == "msg-001"

    def test_tail_returns_none_when_empty(self):
        storage = InMemoryAuditStorage()
        assert storage.tail() is None

    def test_count_tracks_insertions(self):
        storage = InMemoryAuditStorage()
        assert storage.count() == 0
        storage.append(_make_entry(0))
        assert storage.count() == 1
        storage.append(_make_entry(1))
        assert storage.count() == 2

    def test_entries_are_deep_copied(self):
        """Mutating the original entry after append MUST NOT affect stored copy."""
        storage = InMemoryAuditStorage()
        entry = _make_entry(0)
        storage.append(entry)
        entry.message_id = "TAMPERED"
        assert storage.entries()[0].message_id == "msg-000"

    def test_satisfies_audit_storage_protocol(self):
        """InMemoryAuditStorage MUST satisfy the AuditStorage Protocol."""
        assert isinstance(InMemoryAuditStorage(), AuditStorage)


# ── AuditLogger chain integrity tests ───────────────────────────────────

class TestChainIntegrity:
    """Verify hash chain and sequence number integrity."""

    def test_valid_chain_after_five_entries(self):
        al = AuditLogger()
        for i in range(5):
            al.log(_make_entry(i))
        assert al.verify_chain() is True

    def test_sequence_numbers_assigned_monotonically(self):
        al = AuditLogger()
        logged = [al.log(_make_entry(i)) for i in range(5)]
        for idx, entry in enumerate(logged):
            assert entry.sequence == idx

    def test_detects_gap_when_entry_removed(self):
        """Removing an entry from the middle must break verification."""
        storage = InMemoryAuditStorage()
        al = AuditLogger(storage=storage)
        for i in range(5):
            al.log(_make_entry(i))
        # Tamper: remove entry at index 2 by rebuilding the tuple
        original = list(storage._store)
        del original[2]
        storage._store = tuple(original)
        assert al.verify_chain() is False

    def test_detects_hash_mismatch_when_tampered(self):
        """Modifying an entry's field after logging must break verification."""
        storage = InMemoryAuditStorage()
        al = AuditLogger(storage=storage)
        for i in range(3):
            al.log(_make_entry(i))
        # Tamper: change sender on the stored copy
        tampered = list(storage._store)
        modified = tampered[1].model_copy(update={"sender": "agent://evil.example.com"})
        tampered[1] = modified
        storage._store = tuple(tampered)
        assert al.verify_chain() is False

    def test_empty_chain_is_valid(self):
        al = AuditLogger()
        assert al.verify_chain() is True

    def test_count_property(self):
        al = AuditLogger()
        assert al.count == 0
        al.log(_make_entry(0))
        assert al.count == 1

    def test_custom_storage_backend(self):
        """AuditLogger should accept any AuditStorage implementation."""
        storage = InMemoryAuditStorage()
        al = AuditLogger(storage=storage)
        al.log(_make_entry(0))
        assert storage.count() == 1
        assert al.verify_chain() is True

    def test_get_entries_filters_by_message_id(self):
        al = AuditLogger()
        al.log(_make_entry(0))
        al.log(_make_entry(1))
        al.log(_make_entry(0))  # duplicate message_id
        filtered = al.get_entries(message_id="msg-000")
        assert len(filtered) == 2
        assert all(e.message_id == "msg-000" for e in filtered)

    def test_get_entries_returns_all_when_no_filter(self):
        al = AuditLogger()
        for i in range(3):
            al.log(_make_entry(i))
        assert len(al.get_entries()) == 3
