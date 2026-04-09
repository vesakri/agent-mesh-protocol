"""Tests for visibility levels and contact policies."""
import pytest


class TestVisibilityConfig:
    def test_defaults(self):
        from ampro import VisibilityConfig, VisibilityLevel, ContactPolicy
        vc = VisibilityConfig()
        assert vc.level == VisibilityLevel.PUBLIC
        assert vc.contact_policy == ContactPolicy.OPEN
        assert vc.listed_in_registries is True
        assert vc.searchable is True

    def test_custom(self):
        from ampro import VisibilityConfig, VisibilityLevel, ContactPolicy
        vc = VisibilityConfig(
            level=VisibilityLevel.PRIVATE,
            contact_policy=ContactPolicy.DELEGATION_ONLY,
            listed_in_registries=False,
            searchable=False,
        )
        assert vc.level == VisibilityLevel.PRIVATE
        assert vc.contact_policy == ContactPolicy.DELEGATION_ONLY


class TestCheckContactAllowed:
    def test_open_always_allowed(self):
        from ampro import check_contact_allowed, ContactPolicy
        for tier in ["external", "verified", "owner", "internal"]:
            assert check_contact_allowed(tier, ContactPolicy.OPEN) is True

    def test_handshake_always_passes_tier_check(self):
        from ampro import check_contact_allowed, ContactPolicy
        for tier in ["external", "verified", "owner", "internal"]:
            assert check_contact_allowed(tier, ContactPolicy.HANDSHAKE_REQUIRED) is True

    def test_verified_only(self):
        from ampro import check_contact_allowed, ContactPolicy
        assert check_contact_allowed("internal", ContactPolicy.VERIFIED_ONLY) is True
        assert check_contact_allowed("owner", ContactPolicy.VERIFIED_ONLY) is True
        assert check_contact_allowed("verified", ContactPolicy.VERIFIED_ONLY) is True
        assert check_contact_allowed("external", ContactPolicy.VERIFIED_ONLY) is False

    def test_delegation_only(self):
        from ampro import check_contact_allowed, ContactPolicy
        assert check_contact_allowed("internal", ContactPolicy.DELEGATION_ONLY) is True
        assert check_contact_allowed("owner", ContactPolicy.DELEGATION_ONLY) is True
        assert check_contact_allowed("verified", ContactPolicy.DELEGATION_ONLY) is False
        assert check_contact_allowed("external", ContactPolicy.DELEGATION_ONLY) is False

    def test_explicit_invite_always_false(self):
        from ampro import check_contact_allowed, ContactPolicy
        for tier in ["external", "verified", "owner", "internal"]:
            assert check_contact_allowed(tier, ContactPolicy.EXPLICIT_INVITE) is False


class TestFilterAgentJson:
    FULL_JSON = {
        "protocol_version": "1.0.0",
        "identifiers": ["agent://test.com"],
        "endpoint": "https://test.com/agent/message",
        "visibility": {"level": "authenticated"},
        "capabilities": {"groups": ["messaging"]},
        "constraints": {"max_tokens": 1000},
        "security": {"auth_methods": ["jwt"]},
    }

    def test_public_returns_full(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "external", VisibilityLevel.PUBLIC)
        assert "capabilities" in result
        assert "security" in result

    def test_public_does_not_mutate(self):
        from ampro import filter_agent_json, VisibilityLevel
        original = dict(self.FULL_JSON)
        filter_agent_json(self.FULL_JSON, "external", VisibilityLevel.PUBLIC)
        assert self.FULL_JSON == original

    def test_authenticated_verified_gets_full(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "verified", VisibilityLevel.AUTHENTICATED)
        assert "capabilities" in result

    def test_authenticated_external_gets_stub(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "external", VisibilityLevel.AUTHENTICATED)
        assert "protocol_version" in result
        assert "identifiers" in result
        assert "endpoint" in result
        assert "visibility" in result
        assert "capabilities" not in result
        assert "security" not in result

    def test_private_owner_gets_full(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "owner", VisibilityLevel.PRIVATE)
        assert "capabilities" in result

    def test_private_external_gets_empty(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "external", VisibilityLevel.PRIVATE)
        assert result == {}

    def test_private_verified_gets_empty(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "verified", VisibilityLevel.PRIVATE)
        assert result == {}

    def test_hidden_owner_gets_full(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "internal", VisibilityLevel.HIDDEN)
        assert "capabilities" in result

    def test_hidden_external_gets_empty(self):
        from ampro import filter_agent_json, VisibilityLevel
        result = filter_agent_json(self.FULL_JSON, "external", VisibilityLevel.HIDDEN)
        assert result == {}
