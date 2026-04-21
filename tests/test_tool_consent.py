"""Tests for per-tool consent body types and ToolDefinition."""
import pytest
from pydantic import ValidationError


class TestToolConsentRequestBody:
    def test_all_fields(self):
        from ampro import ToolConsentRequestBody
        body = ToolConsentRequestBody(
            tool_name="web_search",
            scopes=["read:web", "execute:search"],
            reason="Need to search the web for the user's query",
            session_id="sess-42",
            ttl_seconds=1800,
        )
        assert body.tool_name == "web_search"
        assert body.scopes == ["read:web", "execute:search"]
        assert body.reason == "Need to search the web for the user's query"
        assert body.session_id == "sess-42"
        assert body.ttl_seconds == 1800

    def test_ttl_seconds_default(self):
        from ampro import ToolConsentRequestBody
        body = ToolConsentRequestBody(
            tool_name="file_read",
            scopes=["read:file"],
            reason="Read config file",
            session_id="sess-1",
        )
        assert body.ttl_seconds == 3600

    def test_missing_required_raises(self):
        from ampro import ToolConsentRequestBody
        with pytest.raises(ValidationError):
            ToolConsentRequestBody(tool_name="tool1")


class TestToolConsentGrantBody:
    def test_all_fields(self):
        from ampro import ToolConsentGrantBody
        body = ToolConsentGrantBody(
            tool_name="web_search",
            scopes=["read:web"],
            grant_id="grant-abc",
            valid_for_session="sess-42",
            expires_at="2026-04-09T13:00:00Z",
            restrictions={"max_invocations": 10, "allowed_params": ["query"]},
        )
        assert body.tool_name == "web_search"
        assert body.scopes == ["read:web"]
        assert body.grant_id == "grant-abc"
        assert body.valid_for_session == "sess-42"
        assert body.expires_at == "2026-04-09T13:00:00Z"
        assert body.restrictions == {"max_invocations": 10, "allowed_params": ["query"]}

    def test_restrictions_default_empty(self):
        from ampro import ToolConsentGrantBody
        body = ToolConsentGrantBody(
            tool_name="file_read",
            scopes=["read:file"],
            grant_id="grant-1",
            valid_for_session="sess-1",
            expires_at="2026-04-09T14:00:00Z",
        )
        assert body.restrictions == {}

    def test_missing_required_raises(self):
        from ampro import ToolConsentGrantBody
        with pytest.raises(ValidationError):
            ToolConsentGrantBody(tool_name="tool1")


class TestToolDefinition:
    def test_all_fields(self):
        from ampro import ToolDefinition
        td = ToolDefinition(
            name="web_search",
            description="Search the web",
            consent_required=True,
            consent_scopes=["read:web", "execute:search"],
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            category="search",
            tags=["web", "search", "external"],
        )
        assert td.name == "web_search"
        assert td.description == "Search the web"
        assert td.consent_required is True
        assert td.consent_scopes == ["read:web", "execute:search"]
        assert "query" in td.parameters["properties"]
        assert td.category == "search"
        assert td.tags == ["web", "search", "external"]

    def test_consent_required_default_false(self):
        from ampro import ToolDefinition
        td = ToolDefinition(name="echo", description="Echo input")
        assert td.consent_required is False

    def test_consent_scopes_default_empty(self):
        from ampro import ToolDefinition
        td = ToolDefinition(name="echo", description="Echo input")
        assert td.consent_scopes == []

    def test_parameters_default_empty(self):
        from ampro import ToolDefinition
        td = ToolDefinition(name="noop", description="Do nothing")
        assert td.parameters == {}

    def test_category_default_none(self):
        from ampro import ToolDefinition
        td = ToolDefinition(name="noop", description="Do nothing")
        assert td.category is None

    def test_tags_default_empty(self):
        from ampro import ToolDefinition
        td = ToolDefinition(name="noop", description="Do nothing")
        assert td.tags == []


class TestToolConsentRegistry:
    def test_validate_body_consent_request(self):
        from ampro import ToolConsentRequestBody, validate_body
        body = validate_body("tool.consent_request", {
            "tool_name": "web_search",
            "scopes": ["read:web"],
            "reason": "Search needed",
            "session_id": "sess-1",
        })
        assert isinstance(body, ToolConsentRequestBody)
        assert body.tool_name == "web_search"

    def test_validate_body_consent_grant(self):
        from ampro import ToolConsentGrantBody, validate_body
        body = validate_body("tool.consent_grant", {
            "tool_name": "web_search",
            "scopes": ["read:web"],
            "grant_id": "g-1",
            "valid_for_session": "sess-1",
            "expires_at": "2026-04-09T13:00:00Z",
        })
        assert isinstance(body, ToolConsentGrantBody)
        assert body.grant_id == "g-1"

    def test_validate_body_consent_grant_with_restrictions(self):
        from ampro import ToolConsentGrantBody, validate_body
        body = validate_body("tool.consent_grant", {
            "tool_name": "web_search",
            "scopes": ["read:web"],
            "grant_id": "g-2",
            "valid_for_session": "sess-1",
            "expires_at": "2026-04-09T14:00:00Z",
            "restrictions": {"max_invocations": 5},
        })
        assert isinstance(body, ToolConsentGrantBody)
        assert body.restrictions["max_invocations"] == 5
