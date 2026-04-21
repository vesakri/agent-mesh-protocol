"""Tests for issue #36 + #43: agent.json migration chain depth limit and
cache-invalidation push body."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ampro.agent.schema import (
    MAX_MIGRATION_HOPS,
    AgentJson,
    AgentMetadataInvalidateBody,
    follow_migration_chain,
)
from ampro.errors import AmpError, MigrationChainTooLongError, TransportError


def _agent(identifier: str, moved_to: str | None = None) -> AgentJson:
    return AgentJson(
        protocol_version="1.0.0",
        identifiers=[identifier],
        endpoint=f"https://{identifier.removeprefix('agent://')}/agent/message",
        moved_to=moved_to,
    )


class TestFollowMigrationChain:
    def test_returns_terminal_agent_when_no_migration(self):
        agent = _agent("agent://a.example.com")
        result = follow_migration_chain(agent, resolver=lambda _: None)
        assert result is agent

    def test_follows_single_hop(self):
        old = _agent("agent://old.example.com", moved_to="agent://new.example.com")
        new = _agent("agent://new.example.com")
        resolver = lambda uri: {"agent://new.example.com": new}.get(uri)
        result = follow_migration_chain(old, resolver)
        assert result is new

    def test_returns_last_known_when_target_unresolvable(self):
        old = _agent("agent://old.example.com", moved_to="agent://gone.example.com")
        result = follow_migration_chain(old, resolver=lambda _: None)
        # Resolver returns None → return the record we have.
        assert result is old

    def test_migration_chain_depth_limit_enforced(self):
        chain = [
            _agent(
                f"agent://a{i}.example.com",
                moved_to=f"agent://a{i+1}.example.com",
            )
            for i in range(10)
        ]

        def resolver(uri: str) -> AgentJson | None:
            for a in chain:
                if a.identifiers[0] == uri:
                    return a
            return None

        with pytest.raises(MigrationChainTooLongError):
            follow_migration_chain(chain[0], resolver, max_hops=MAX_MIGRATION_HOPS)

    def test_default_max_is_five(self):
        assert MAX_MIGRATION_HOPS == 5

    def test_cycle_in_chain_detected(self):
        a = _agent("agent://a.example.com", moved_to="agent://b.example.com")
        b = _agent("agent://b.example.com", moved_to="agent://a.example.com")
        resolver = lambda uri: {
            "agent://a.example.com": a,
            "agent://b.example.com": b,
        }.get(uri)
        with pytest.raises(MigrationChainTooLongError):
            follow_migration_chain(a, resolver)

    def test_error_is_transport_error(self):
        assert issubclass(MigrationChainTooLongError, TransportError)
        assert issubclass(MigrationChainTooLongError, AmpError)


class TestAgentMetadataInvalidateBody:
    """Issue #43 — push body telling caches to drop a cached agent.json."""

    def test_all_fields(self):
        body = AgentMetadataInvalidateBody(
            agent_id="agent://x.example.com",
            changed_at=datetime(2026, 4, 9, 12, 0, 0, tzinfo=UTC),
            reason="migration",
        )
        assert body.agent_id == "agent://x.example.com"
        assert body.reason == "migration"

    @pytest.mark.parametrize(
        "reason",
        ["visibility_change", "endpoint_change", "migration", "revocation"],
    )
    def test_allowed_reasons(self, reason):
        body = AgentMetadataInvalidateBody(
            agent_id="agent://y.example.com",
            changed_at=datetime.now(tz=UTC),
            reason=reason,
        )
        assert body.reason == reason

    def test_rejects_unknown_reason(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AgentMetadataInvalidateBody(
                agent_id="agent://y.example.com",
                changed_at=datetime.now(tz=UTC),
                reason="pineapple",
            )

    def test_registered_in_body_schemas(self):
        from ampro import validate_body

        body = validate_body(
            "agent.metadata_invalidate",
            {
                "agent_id": "agent://x.example.com",
                "changed_at": "2026-04-09T12:00:00+00:00",
                "reason": "revocation",
            },
        )
        assert isinstance(body, AgentMetadataInvalidateBody)
