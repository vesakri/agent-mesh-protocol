"""
Tests for visited-agents URI normalization (Task 3.5).

Verifies that ``parse_visited_agents`` and ``check_visited_agents_loop``
normalize URIs (strip + lowercase) so that case and whitespace variations
cannot bypass loop detection.
"""

from __future__ import annotations

from ampro.delegation.chain import (
    check_visited_agents_loop,
    normalize_agent_uri,
    parse_visited_agents,
)


# ---------------------------------------------------------------------------
# normalize_agent_uri
# ---------------------------------------------------------------------------


class TestNormalizeAgentUri:
    """Unit tests for the URI normalizer."""

    def test_lowercase(self) -> None:
        assert normalize_agent_uri("agent://A") == "agent://a"

    def test_strip_trailing(self) -> None:
        assert normalize_agent_uri("agent://a ") == "agent://a"

    def test_strip_leading(self) -> None:
        assert normalize_agent_uri("  agent://a") == "agent://a"

    def test_strip_and_lowercase(self) -> None:
        assert normalize_agent_uri("  Agent://FOO  ") == "agent://foo"

    def test_already_normalized(self) -> None:
        assert normalize_agent_uri("agent://x") == "agent://x"

    def test_empty_string(self) -> None:
        assert normalize_agent_uri("") == ""


# ---------------------------------------------------------------------------
# parse_visited_agents
# ---------------------------------------------------------------------------


class TestParseVisitedAgents:
    """Tests for header parsing with normalization."""

    def test_empty_header(self) -> None:
        result = parse_visited_agents("")
        assert result == set()

    def test_single_agent(self) -> None:
        result = parse_visited_agents("agent://a")
        assert result == {"agent://a"}

    def test_multiple_agents(self) -> None:
        result = parse_visited_agents("agent://a, agent://b, agent://c")
        assert result == {"agent://a", "agent://b", "agent://c"}

    def test_mixed_case_normalized(self) -> None:
        result = parse_visited_agents("Agent://A, AGENT://B, agent://c")
        assert result == {"agent://a", "agent://b", "agent://c"}

    def test_whitespace_stripped(self) -> None:
        result = parse_visited_agents("  agent://a , agent://b  ")
        assert result == {"agent://a", "agent://b"}

    def test_empty_entries_filtered(self) -> None:
        result = parse_visited_agents("agent://a,,, ,agent://b")
        assert result == {"agent://a", "agent://b"}

    def test_duplicates_with_case_difference_collapsed(self) -> None:
        result = parse_visited_agents("agent://A, agent://a, AGENT://A")
        assert result == {"agent://a"}
        assert len(result) == 1

    def test_returns_set(self) -> None:
        result = parse_visited_agents("agent://x")
        assert isinstance(result, set)


# ---------------------------------------------------------------------------
# check_visited_agents_loop
# ---------------------------------------------------------------------------


class TestCheckVisitedAgentsLoop:
    """Tests for loop detection with URI normalization."""

    def test_same_uri_different_case_detected(self) -> None:
        """agent://A in header, checking agent://a → loop."""
        assert check_visited_agents_loop("agent://A", "agent://a") is True

    def test_uri_with_trailing_whitespace_detected(self) -> None:
        """agent://a in header, checking 'agent://a ' → loop."""
        assert check_visited_agents_loop("agent://a", "agent://a ") is True

    def test_uri_with_leading_whitespace_detected(self) -> None:
        """agent://a in header, checking ' agent://a' → loop."""
        assert check_visited_agents_loop("agent://a", " agent://a") is True

    def test_different_uris_no_loop(self) -> None:
        assert check_visited_agents_loop("agent://a", "agent://b") is False

    def test_empty_header_no_loop(self) -> None:
        assert check_visited_agents_loop("", "agent://a") is False

    def test_mixed_case_header_and_self(self) -> None:
        """Both header and self_uri have mixed case → still detected."""
        assert check_visited_agents_loop(
            "Agent://Foo, agent://BAR",
            "AGENT://foo",
        ) is True

    def test_self_uri_not_in_list(self) -> None:
        assert check_visited_agents_loop(
            "agent://x, agent://y",
            "agent://z",
        ) is False

    def test_case_insensitive_across_comma_list(self) -> None:
        header = "agent://Alpha, agent://BETA, agent://gamma"
        assert check_visited_agents_loop(header, "agent://beta") is True
        assert check_visited_agents_loop(header, "AGENT://ALPHA") is True
        assert check_visited_agents_loop(header, "Agent://Gamma") is True
        assert check_visited_agents_loop(header, "agent://delta") is False
