"""
Tests for scope-narrowing wildcard hierarchy (Task 3.6).

Verifies that ``validate_scope_narrowing`` enforces strict prefix matching
so that a parent wildcard like ``tool:*`` cannot grant cross-prefix scopes
such as ``admin:*``.
"""

from __future__ import annotations

from ampro.delegation.chain import validate_scope_narrowing

# ---------------------------------------------------------------------------
# Basic wildcard prefix — allowed cases
# ---------------------------------------------------------------------------


class TestWildcardAllowed:
    """Child scopes that SHOULD be permitted by parent wildcards."""

    def test_wildcard_allows_child_under_same_prefix(self) -> None:
        """tool:* → tool:read ✅"""
        assert validate_scope_narrowing(["tool:*"], ["tool:read"]) is True

    def test_wildcard_allows_multiple_children(self) -> None:
        """tool:* → tool:read, tool:execute ✅"""
        assert validate_scope_narrowing(
            ["tool:*"], ["tool:read", "tool:execute"]
        ) is True

    def test_wildcard_allows_same_wildcard(self) -> None:
        """tool:* → tool:* ✅ (same scope)"""
        assert validate_scope_narrowing(["tool:*"], ["tool:*"]) is True

    def test_wildcard_allows_nested_scope(self) -> None:
        """tool:* → tool:sub:read ✅ (prefix match covers nesting)"""
        assert validate_scope_narrowing(["tool:*"], ["tool:sub:read"]) is True

    def test_wildcard_allows_nested_wildcard(self) -> None:
        """tool:* → tool:sub:* ✅ (still under tool: prefix)"""
        assert validate_scope_narrowing(["tool:*"], ["tool:sub:*"]) is True

    def test_exact_match_same_scope(self) -> None:
        """tool:read → tool:read ✅"""
        assert validate_scope_narrowing(["tool:read"], ["tool:read"]) is True

    def test_universal_wildcard_allows_anything(self) -> None:
        """* → tool:read ✅"""
        assert validate_scope_narrowing(["*"], ["tool:read"]) is True

    def test_universal_wildcard_allows_admin(self) -> None:
        """* → admin:* ✅"""
        assert validate_scope_narrowing(["*"], ["admin:*"]) is True

    def test_universal_wildcard_allows_nested(self) -> None:
        """* → tool:sub:deep:scope ✅"""
        assert validate_scope_narrowing(["*"], ["tool:sub:deep:scope"]) is True

    def test_multiple_parent_wildcards(self) -> None:
        """tool:*, data:* → tool:read, data:write ✅"""
        assert validate_scope_narrowing(
            ["tool:*", "data:*"], ["tool:read", "data:write"]
        ) is True


# ---------------------------------------------------------------------------
# Wildcard prefix — rejected cases
# ---------------------------------------------------------------------------


class TestWildcardRejected:
    """Child scopes that MUST be rejected by parent wildcards."""

    def test_different_prefix_rejected(self) -> None:
        """tool:* → admin:read ✗"""
        assert validate_scope_narrowing(["tool:*"], ["admin:read"]) is False

    def test_wildcard_cross_prefix_rejected(self) -> None:
        """tool:* → admin:* ✗"""
        assert validate_scope_narrowing(["tool:*"], ["admin:*"]) is False

    def test_wildcard_data_prefix_rejected(self) -> None:
        """tool:* → data:* ✗"""
        assert validate_scope_narrowing(["tool:*"], ["data:*"]) is False

    def test_exact_scope_rejects_different_value(self) -> None:
        """tool:read → tool:write ✗"""
        assert validate_scope_narrowing(["tool:read"], ["tool:write"]) is False

    def test_exact_scope_rejects_wildcard_escalation(self) -> None:
        """tool:read → tool:* ✗ (cannot escalate to wildcard)"""
        assert validate_scope_narrowing(["tool:read"], ["tool:*"]) is False

    def test_no_parent_scopes_rejects_everything(self) -> None:
        """(empty parent) → tool:read ✗ (but child non-empty is checked)"""
        # Empty child is also invalid, tested separately
        assert validate_scope_narrowing(["tool:read"], []) is False

    def test_partial_prefix_mismatch(self) -> None:
        """tool:* → toolbox:read ✗ (toolbox != tool)"""
        assert validate_scope_narrowing(["tool:*"], ["toolbox:read"]) is False

    def test_child_has_scope_not_in_parent(self) -> None:
        """tool:read → tool:read, admin:write ✗ (admin:write not covered)"""
        assert validate_scope_narrowing(
            ["tool:read"], ["tool:read", "admin:write"]
        ) is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestScopeEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_child_rejected(self) -> None:
        assert validate_scope_narrowing(["tool:*"], []) is False

    def test_single_star_is_universal(self) -> None:
        """A bare '*' grants everything."""
        assert validate_scope_narrowing(["*"], ["anything"]) is True

    def test_scope_without_colon_requires_exact(self) -> None:
        """'admin' (no colon) requires exact match."""
        assert validate_scope_narrowing(["admin"], ["admin"]) is True
        assert validate_scope_narrowing(["admin"], ["admin:read"]) is False

    def test_too_many_scopes_rejected(self) -> None:
        """More than MAX_SCOPES (100) is rejected."""
        big = [f"s:{i}" for i in range(101)]
        assert validate_scope_narrowing(big, ["s:0"]) is False
        assert validate_scope_narrowing(["s:*"], big) is False

    def test_direct_match_takes_precedence(self) -> None:
        """Even without wildcard, exact match works."""
        assert validate_scope_narrowing(
            ["tool:read", "admin:write"], ["tool:read"]
        ) is True

    def test_mixed_wildcard_and_exact(self) -> None:
        """Parent has wildcard + exact; child uses both."""
        assert validate_scope_narrowing(
            ["tool:*", "admin:write"],
            ["tool:execute", "admin:write"],
        ) is True

    def test_mixed_wildcard_and_exact_partial_fail(self) -> None:
        """Parent has tool:* + admin:write; child wants admin:read → fail."""
        assert validate_scope_narrowing(
            ["tool:*", "admin:write"],
            ["tool:execute", "admin:read"],
        ) is False
