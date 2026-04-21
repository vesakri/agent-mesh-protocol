"""Tests for identity migration body type and agent.json moved_to field."""
import pytest
from pydantic import ValidationError


class TestMigrationBody:
    def test_all_fields(self):
        from ampro import IdentityMigrationBody

        body = IdentityMigrationBody(
            old_id="agent://alice.old-domain.example.com",
            new_id="agent://alice.new-domain.example.com",
            migration_proof="dual-signed-proof-data",
            effective_at="2026-04-10T00:00:00Z",
        )
        assert body.old_id == "agent://alice.old-domain.example.com"
        assert body.new_id == "agent://alice.new-domain.example.com"
        assert body.migration_proof == "dual-signed-proof-data"
        assert body.effective_at == "2026-04-10T00:00:00Z"

    def test_missing_required_raises(self):
        from ampro import IdentityMigrationBody

        with pytest.raises(ValidationError):
            IdentityMigrationBody(
                old_id="agent://old.example.com",
                # missing new_id, migration_proof, effective_at
            )

    def test_extra_fields_ignored(self):
        from ampro import IdentityMigrationBody

        body = IdentityMigrationBody(
            old_id="agent://old.example.com",
            new_id="agent://new.example.com",
            migration_proof="proof",
            effective_at="2026-04-10T00:00:00Z",
            unknown="ignored",
        )
        assert not hasattr(body, "unknown")


class TestBodyRegistry:
    def test_validate_body(self):
        from ampro import IdentityMigrationBody, validate_body

        body = validate_body("identity.migration", {
            "old_id": "agent://old.example.com",
            "new_id": "agent://new.example.com",
            "migration_proof": "signed-by-both-keys",
            "effective_at": "2026-04-10T00:00:00Z",
        })
        assert isinstance(body, IdentityMigrationBody)
        assert body.old_id == "agent://old.example.com"
        assert body.new_id == "agent://new.example.com"

    def test_validate_body_invalid(self):
        from ampro import validate_body

        with pytest.raises(ValidationError):
            validate_body("identity.migration", {})


class TestAgentJsonMovedTo:
    def test_moved_to_field(self):
        from ampro import AgentJson

        aj = AgentJson(
            protocol_version="0.1.8",
            identifiers=["agent://old.example.com"],
            endpoint="https://old.example.com/agent/message",
            moved_to="agent://new.example.com",
        )
        assert aj.moved_to == "agent://new.example.com"

    def test_moved_to_default_none(self):
        from ampro import AgentJson

        aj = AgentJson(
            protocol_version="0.1.8",
            identifiers=["agent://active.example.com"],
            endpoint="https://active.example.com/agent/message",
        )
        assert aj.moved_to is None
