"""Tests for ampro.erasure_propagation — v0.1.6 GDPR erasure tracking."""

import pytest

from ampro.erasure_propagation import (
    ErasurePropagationStatus,
    ErasurePropagationStatusBody,
)
from ampro.body_schemas import validate_body


class TestErasurePropagationStatusEnum:
    def test_status_enum_values(self):
        """Enum has exactly 3 members: pending, completed, failed."""
        assert len(ErasurePropagationStatus) == 3
        assert ErasurePropagationStatus.PENDING == "pending"
        assert ErasurePropagationStatus.COMPLETED == "completed"
        assert ErasurePropagationStatus.FAILED == "failed"


class TestErasurePropagationBody:
    def test_propagation_body_creation(self):
        """All fields are present and correct."""
        body = ErasurePropagationStatusBody(
            erasure_id="er-001",
            agent_id="agent://cleaner.example.com",
            status="completed",
            records_affected=42,
            timestamp="2026-04-09T12:00:00Z",
            detail="All records erased successfully",
            downstream_agents=["agent://sub1.example.com", "agent://sub2.example.com"],
        )
        assert body.erasure_id == "er-001"
        assert body.agent_id == "agent://cleaner.example.com"
        assert body.status == "completed"
        assert body.records_affected == 42
        assert body.timestamp == "2026-04-09T12:00:00Z"
        assert body.detail == "All records erased successfully"
        assert len(body.downstream_agents) == 2

    def test_propagation_pending(self):
        """Pending status with 0 records affected."""
        body = ErasurePropagationStatusBody(
            erasure_id="er-002",
            agent_id="agent://worker.example.com",
            status="pending",
            records_affected=0,
            timestamp="2026-04-09T10:00:00Z",
        )
        assert body.status == "pending"
        assert body.records_affected == 0

    def test_propagation_completed(self):
        """Completed status with records_affected > 0."""
        body = ErasurePropagationStatusBody(
            erasure_id="er-003",
            agent_id="agent://db-agent.example.com",
            status="completed",
            records_affected=150,
            timestamp="2026-04-09T11:00:00Z",
        )
        assert body.status == "completed"
        assert body.records_affected > 0

    def test_propagation_failed_with_detail(self):
        """Failed status includes a detail explaining the failure."""
        body = ErasurePropagationStatusBody(
            erasure_id="er-004",
            agent_id="agent://flaky.example.com",
            status="failed",
            records_affected=0,
            timestamp="2026-04-09T13:00:00Z",
            detail="Database timeout after 3 retries",
        )
        assert body.status == "failed"
        assert body.detail == "Database timeout after 3 retries"

    def test_downstream_agents(self):
        """downstream_agents list is populated correctly."""
        agents = ["agent://a.example.com", "agent://b.example.com", "agent://c.example.com"]
        body = ErasurePropagationStatusBody(
            erasure_id="er-005",
            agent_id="agent://hub.example.com",
            status="pending",
            records_affected=0,
            timestamp="2026-04-09T14:00:00Z",
            downstream_agents=agents,
        )
        assert body.downstream_agents == agents
        assert len(body.downstream_agents) == 3


class TestErasurePropagationBodyRegistry:
    def test_body_registry(self):
        """validate_body('erasure.propagation_status', ...) returns correct type."""
        body = validate_body("erasure.propagation_status", {
            "erasure_id": "er-100",
            "agent_id": "agent://test.example.com",
            "status": "completed",
            "records_affected": 10,
            "timestamp": "2026-04-09T00:00:00Z",
        })
        assert isinstance(body, ErasurePropagationStatusBody)
        assert body.erasure_id == "er-100"
        assert body.records_affected == 10
