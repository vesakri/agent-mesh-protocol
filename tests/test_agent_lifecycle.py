"""Tests for v0.1.3 Agent Lifecycle feature."""

import pytest
from pydantic import ValidationError


class TestAgentLifecycleStatus:
    def test_three_values(self):
        from ampro import AgentLifecycleStatus
        assert len(AgentLifecycleStatus) == 3

    def test_active_value(self):
        from ampro import AgentLifecycleStatus
        assert AgentLifecycleStatus.ACTIVE == "active"

    def test_deactivating_value(self):
        from ampro import AgentLifecycleStatus
        assert AgentLifecycleStatus.DEACTIVATING == "deactivating"

    def test_decommissioned_value(self):
        from ampro import AgentLifecycleStatus
        assert AgentLifecycleStatus.DECOMMISSIONED == "decommissioned"


class TestAgentDeactivationNoticeBody:
    def test_all_required_fields(self):
        from ampro import AgentDeactivationNoticeBody
        body = AgentDeactivationNoticeBody(
            agent_id="agent://retiring.example.com",
            reason="Planned maintenance",
            deactivation_time="2026-04-09T12:00:00Z",
            active_sessions=3,
        )
        assert body.agent_id == "agent://retiring.example.com"
        assert body.reason == "Planned maintenance"
        assert body.deactivation_time == "2026-04-09T12:00:00Z"
        assert body.active_sessions == 3

    def test_optional_fields_default_none(self):
        from ampro import AgentDeactivationNoticeBody
        body = AgentDeactivationNoticeBody(
            agent_id="agent://test.example.com",
            reason="Shutdown",
            deactivation_time="2026-04-09T00:00:00Z",
            active_sessions=0,
        )
        assert body.migration_endpoint is None
        assert body.final_at is None
        assert body.metadata is None

    def test_optional_fields_populated(self):
        from ampro import AgentDeactivationNoticeBody
        body = AgentDeactivationNoticeBody(
            agent_id="agent://old.example.com",
            reason="Migrating to new version",
            deactivation_time="2026-04-09T10:00:00Z",
            active_sessions=5,
            migration_endpoint="https://new.example.com/agent/message",
            final_at="2026-04-10T10:00:00Z",
            metadata={"version": "2.0"},
        )
        assert body.migration_endpoint == "https://new.example.com/agent/message"
        assert body.final_at == "2026-04-10T10:00:00Z"
        assert body.metadata == {"version": "2.0"}

    def test_missing_required_fields_raises(self):
        from ampro import AgentDeactivationNoticeBody
        with pytest.raises(ValidationError):
            AgentDeactivationNoticeBody()

    def test_validate_body_deactivation_notice(self):
        from ampro import AgentDeactivationNoticeBody, validate_body
        body = validate_body("agent.deactivation_notice", {
            "agent_id": "agent://retiring.example.com",
            "reason": "End of life",
            "deactivation_time": "2026-04-09T12:00:00Z",
            "active_sessions": 1,
        })
        assert isinstance(body, AgentDeactivationNoticeBody)
        assert body.agent_id == "agent://retiring.example.com"


class TestAgentJsonLifecycle:
    def test_status_defaults_to_active(self):
        from ampro import AgentJson
        aj = AgentJson(
            protocol_version="1.0.0",
            identifiers=["agent://test.example.com"],
            endpoint="https://test.example.com/agent/message",
        )
        assert aj.status == "active"

    def test_status_deactivating(self):
        from ampro import AgentJson
        aj = AgentJson(
            protocol_version="1.0.0",
            identifiers=["agent://test.example.com"],
            endpoint="https://test.example.com/agent/message",
            status="deactivating",
        )
        assert aj.status == "deactivating"


class TestRegistryResolutionLifecycle:
    def test_gone_defaults_false(self):
        from ampro import RegistryResolution
        res = RegistryResolution(
            agent_uri="agent://test.example.com",
            endpoint="https://test.example.com/agent/message",
        )
        assert res.gone is False

    def test_gone_true_decommissioned(self):
        from ampro import RegistryResolution
        res = RegistryResolution(
            agent_uri="agent://old.example.com",
            endpoint="https://old.example.com/agent/message",
            gone=True,
            status="decommissioned",
        )
        assert res.gone is True
        assert res.status == "decommissioned"


class TestHopTimeoutHeader:
    def test_hop_timeout_in_standard_headers(self):
        from ampro import STANDARD_HEADERS
        assert "Hop-Timeout" in STANDARD_HEADERS
