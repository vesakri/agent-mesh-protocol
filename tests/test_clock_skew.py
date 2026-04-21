"""Tests for clock skew tightening (Task 2.6).

Verifies that CLOCK_SKEW_SECONDS is 30 and that chain.py uses the
canonical constant from trust.tiers rather than a hardcoded value.
"""

from __future__ import annotations

from datetime import timedelta


class TestClockSkewConstant:
    """CLOCK_SKEW_SECONDS should be 30 seconds."""

    def test_value_is_30(self) -> None:
        from ampro.trust.tiers import CLOCK_SKEW_SECONDS

        assert CLOCK_SKEW_SECONDS == 30

    def test_exported_from_top_level(self) -> None:
        from ampro import CLOCK_SKEW_SECONDS

        assert CLOCK_SKEW_SECONDS == 30

    def test_chain_skew_uses_canonical_constant(self) -> None:
        """chain._SKEW must derive from CLOCK_SKEW_SECONDS, not a hardcoded value."""
        from ampro.delegation.chain import _SKEW
        from ampro.trust.tiers import CLOCK_SKEW_SECONDS

        assert _SKEW == timedelta(seconds=CLOCK_SKEW_SECONDS)
        assert _SKEW == timedelta(seconds=30)

    def test_trust_init_re_exports(self) -> None:
        from ampro.trust import CLOCK_SKEW_SECONDS

        assert CLOCK_SKEW_SECONDS == 30
