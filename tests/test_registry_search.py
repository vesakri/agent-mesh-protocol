"""Tests for ampro.registry_search — v0.1.4 structured service discovery."""

import json

import pytest
from pydantic import ValidationError

from ampro.registry.search import (
    RegistrySearchMatch,
    RegistrySearchRequest,
    RegistrySearchResult,
)


class TestRegistrySearchRequestDefaults:
    """Test RegistrySearchRequest default values."""

    def test_max_results_defaults_to_10(self):
        req = RegistrySearchRequest(capability="messaging")
        assert req.max_results == 10

    def test_filters_defaults_to_none(self):
        req = RegistrySearchRequest(capability="messaging")
        assert req.filters is None

    def test_include_load_level_defaults_to_true(self):
        req = RegistrySearchRequest(capability="messaging")
        assert req.include_load_level is True

    def test_min_trust_score_defaults_to_none(self):
        req = RegistrySearchRequest(capability="messaging")
        assert req.min_trust_score is None

    def test_capability_is_required(self):
        with pytest.raises(ValidationError):
            RegistrySearchRequest()


class TestRegistrySearchRequestWithFilters:
    """Test RegistrySearchRequest with explicit filter criteria."""

    def test_with_filters_dict(self):
        req = RegistrySearchRequest(
            capability="tools",
            filters={"region": "us-east", "min_uptime": 0.99},
        )
        assert req.filters == {"region": "us-east", "min_uptime": 0.99}

    def test_with_custom_max_results(self):
        req = RegistrySearchRequest(capability="tools", max_results=50)
        assert req.max_results == 50

    def test_max_results_lower_bound(self):
        with pytest.raises(ValidationError):
            RegistrySearchRequest(capability="tools", max_results=0)

    def test_max_results_upper_bound(self):
        with pytest.raises(ValidationError):
            RegistrySearchRequest(capability="tools", max_results=101)

    def test_with_min_trust_score(self):
        req = RegistrySearchRequest(capability="tools", min_trust_score=500)
        assert req.min_trust_score == 500

    def test_include_load_level_false(self):
        req = RegistrySearchRequest(capability="tools", include_load_level=False)
        assert req.include_load_level is False


class TestRegistrySearchMatchRequired:
    """Test RegistrySearchMatch required fields."""

    def test_required_fields_present(self):
        match = RegistrySearchMatch(
            agent_id="agent://search.example.com",
            endpoint="https://search.example.com/agent/message",
            capabilities=["messaging", "tools"],
            trust_score=750,
            trust_tier="verified",
        )
        assert match.agent_id == "agent://search.example.com"
        assert match.endpoint == "https://search.example.com/agent/message"
        assert match.capabilities == ["messaging", "tools"]
        assert match.trust_score == 750
        assert match.trust_tier == "verified"

    def test_missing_agent_id_raises(self):
        with pytest.raises(ValidationError):
            RegistrySearchMatch(
                endpoint="https://x.example.com/agent/message",
                capabilities=["messaging"],
                trust_score=500,
                trust_tier="external",
            )

    def test_missing_endpoint_raises(self):
        with pytest.raises(ValidationError):
            RegistrySearchMatch(
                agent_id="agent://x.example.com",
                capabilities=["messaging"],
                trust_score=500,
                trust_tier="external",
            )

    def test_missing_trust_score_raises(self):
        with pytest.raises(ValidationError):
            RegistrySearchMatch(
                agent_id="agent://x.example.com",
                endpoint="https://x.example.com/agent/message",
                capabilities=["messaging"],
                trust_tier="external",
            )


class TestRegistrySearchMatchOptional:
    """Test RegistrySearchMatch optional fields and defaults."""

    def test_load_level_defaults_to_none(self):
        match = RegistrySearchMatch(
            agent_id="agent://a.example.com",
            endpoint="https://a.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=500,
            trust_tier="external",
        )
        assert match.load_level is None

    def test_metadata_defaults_to_none(self):
        match = RegistrySearchMatch(
            agent_id="agent://a.example.com",
            endpoint="https://a.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=500,
            trust_tier="external",
        )
        assert match.metadata is None

    def test_status_defaults_to_active(self):
        match = RegistrySearchMatch(
            agent_id="agent://a.example.com",
            endpoint="https://a.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=500,
            trust_tier="external",
        )
        assert match.status == "active"

    def test_with_load_level(self):
        match = RegistrySearchMatch(
            agent_id="agent://a.example.com",
            endpoint="https://a.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=500,
            trust_tier="external",
            load_level=75,
        )
        assert match.load_level == 75

    def test_with_metadata(self):
        match = RegistrySearchMatch(
            agent_id="agent://a.example.com",
            endpoint="https://a.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=500,
            trust_tier="external",
            metadata={"version": "2.0", "region": "us-west"},
        )
        assert match.metadata == {"version": "2.0", "region": "us-west"}


class TestRegistrySearchResultEmpty:
    """Test RegistrySearchResult with empty matches."""

    def test_empty_matches_list(self):
        result = RegistrySearchResult()
        assert result.matches == []

    def test_total_available_default(self):
        result = RegistrySearchResult()
        assert result.total_available == 0

    def test_search_time_ms_default(self):
        result = RegistrySearchResult()
        assert result.search_time_ms == 0.0


class TestRegistrySearchResultPopulated:
    """Test RegistrySearchResult with populated matches."""

    def test_with_matches(self):
        match1 = RegistrySearchMatch(
            agent_id="agent://a.example.com",
            endpoint="https://a.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=800,
            trust_tier="verified",
            load_level=20,
        )
        match2 = RegistrySearchMatch(
            agent_id="agent://b.example.com",
            endpoint="https://b.example.com/agent/message",
            capabilities=["tools", "messaging"],
            trust_score=600,
            trust_tier="owner",
            load_level=55,
        )
        result = RegistrySearchResult(
            matches=[match1, match2],
            total_available=42,
            search_time_ms=12.5,
        )
        assert len(result.matches) == 2
        assert result.total_available == 42
        assert result.search_time_ms == 12.5
        assert result.matches[0].agent_id == "agent://a.example.com"
        assert result.matches[1].trust_tier == "owner"


class TestRegistrySearchJsonRoundTrip:
    """Test JSON serialization round-trip for all registry search types."""

    def test_request_round_trip(self):
        req = RegistrySearchRequest(
            capability="tools",
            min_trust_score=300,
            max_results=25,
            filters={"region": "eu"},
            include_load_level=False,
        )
        json_str = req.model_dump_json()
        restored = RegistrySearchRequest.model_validate_json(json_str)
        assert restored.capability == req.capability
        assert restored.min_trust_score == req.min_trust_score
        assert restored.max_results == req.max_results
        assert restored.filters == req.filters
        assert restored.include_load_level == req.include_load_level

    def test_match_round_trip(self):
        match = RegistrySearchMatch(
            agent_id="agent://roundtrip.example.com",
            endpoint="https://roundtrip.example.com/agent/message",
            capabilities=["messaging", "tools", "streaming"],
            trust_score=900,
            trust_tier="internal",
            load_level=10,
            status="active",
            metadata={"owner": "test-org"},
        )
        json_str = match.model_dump_json()
        restored = RegistrySearchMatch.model_validate_json(json_str)
        assert restored.agent_id == match.agent_id
        assert restored.load_level == match.load_level
        assert restored.metadata == match.metadata

    def test_result_round_trip(self):
        match = RegistrySearchMatch(
            agent_id="agent://rt.example.com",
            endpoint="https://rt.example.com/agent/message",
            capabilities=["messaging"],
            trust_score=500,
            trust_tier="external",
        )
        result = RegistrySearchResult(
            matches=[match],
            total_available=100,
            search_time_ms=3.14,
        )
        json_str = result.model_dump_json()
        restored = RegistrySearchResult.model_validate_json(json_str)
        assert len(restored.matches) == 1
        assert restored.total_available == 100
        assert restored.search_time_ms == pytest.approx(3.14)

    def test_result_via_json_stdlib(self):
        """Ensure model_dump produces stdlib-JSON-serializable dicts."""
        result = RegistrySearchResult(
            matches=[
                RegistrySearchMatch(
                    agent_id="agent://a.example.com",
                    endpoint="https://a.example.com/agent/message",
                    capabilities=["messaging"],
                    trust_score=500,
                    trust_tier="external",
                ),
            ],
            total_available=1,
            search_time_ms=1.0,
        )
        dumped = result.model_dump()
        json_str = json.dumps(dumped)
        loaded = json.loads(json_str)
        assert loaded["total_available"] == 1
        assert loaded["matches"][0]["agent_id"] == "agent://a.example.com"


class TestRegistrySearchCursorPagination:
    """Issue #42 — cursor-based pagination with back-compat max_results alias."""

    def test_registry_search_cursor_pagination(self):
        # Client page 1
        req1 = RegistrySearchRequest(capability="tools", limit=2)
        assert req1.limit == 2
        assert req1.cursor is None

        # Server replies with a cursor + has_more
        resp1 = RegistrySearchResult(
            matches=[
                RegistrySearchMatch(
                    agent_id=f"agent://{i}.example.com",
                    endpoint=f"https://{i}.example.com/agent/message",
                    capabilities=["tools"],
                    trust_score=500,
                    trust_tier="external",
                )
                for i in range(2)
            ],
            total_available=5,
            next_cursor="opaque-page-2",
            has_more=True,
        )
        assert resp1.has_more is True
        assert resp1.next_cursor == "opaque-page-2"

        # Client page 2 — passes the cursor back in
        req2 = RegistrySearchRequest(
            capability="tools",
            limit=2,
            cursor=resp1.next_cursor,
        )
        assert req2.cursor == "opaque-page-2"

        # Final page: server ran out
        resp2 = RegistrySearchResult(
            matches=[], next_cursor=None, has_more=False,
        )
        assert resp2.has_more is False
        assert resp2.next_cursor is None

    def test_max_results_alias_copies_into_limit(self):
        req = RegistrySearchRequest(capability="tools", max_results=42)
        assert req.limit == 42
        # ``max_results`` property reads from ``limit``
        assert req.max_results == 42

    def test_limit_takes_precedence_when_both_given(self):
        req = RegistrySearchRequest(capability="tools", limit=7, max_results=99)
        assert req.limit == 7

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            RegistrySearchRequest(capability="tools", limit=0)
        with pytest.raises(ValidationError):
            RegistrySearchRequest(capability="tools", limit=101)
