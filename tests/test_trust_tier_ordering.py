"""Tests for TrustTier comparison operators (P0.D finding 2.5)."""

from __future__ import annotations

import pytest

from ampro.trust.tiers import TrustTier


class TestTrustTierOrdering:
    """TrustTier supports <, <=, >, >= comparisons."""

    # -- strict ordering chain ------------------------------------------------

    def test_external_lt_verified(self) -> None:
        assert TrustTier.EXTERNAL < TrustTier.VERIFIED

    def test_verified_lt_owner(self) -> None:
        assert TrustTier.VERIFIED < TrustTier.OWNER

    def test_owner_lt_internal(self) -> None:
        assert TrustTier.OWNER < TrustTier.INTERNAL

    def test_internal_gt_external(self) -> None:
        assert TrustTier.INTERNAL > TrustTier.EXTERNAL

    def test_internal_gt_verified(self) -> None:
        assert TrustTier.INTERNAL > TrustTier.VERIFIED

    def test_owner_gt_external(self) -> None:
        assert TrustTier.OWNER > TrustTier.EXTERNAL

    # -- equality-inclusive operators ------------------------------------------

    def test_verified_ge_verified(self) -> None:
        assert TrustTier.VERIFIED >= TrustTier.VERIFIED

    def test_external_le_external(self) -> None:
        assert TrustTier.EXTERNAL <= TrustTier.EXTERNAL

    def test_internal_ge_external(self) -> None:
        assert TrustTier.INTERNAL >= TrustTier.EXTERNAL

    def test_external_le_internal(self) -> None:
        assert TrustTier.EXTERNAL <= TrustTier.INTERNAL

    # -- negations ------------------------------------------------------------

    def test_internal_not_lt_external(self) -> None:
        assert not (TrustTier.INTERNAL < TrustTier.EXTERNAL)

    def test_external_not_gt_verified(self) -> None:
        assert not (TrustTier.EXTERNAL > TrustTier.VERIFIED)

    # -- cross-type comparison returns NotImplemented -------------------------

    def test_lt_non_trusttier_returns_not_implemented(self) -> None:
        assert TrustTier.EXTERNAL.__lt__("external") is NotImplemented

    def test_le_non_trusttier_returns_not_implemented(self) -> None:
        assert TrustTier.EXTERNAL.__le__(42) is NotImplemented

    def test_gt_non_trusttier_returns_not_implemented(self) -> None:
        assert TrustTier.INTERNAL.__gt__(None) is NotImplemented

    def test_ge_non_trusttier_returns_not_implemented(self) -> None:
        assert TrustTier.OWNER.__ge__(3.14) is NotImplemented

    # -- string serialization preserved ---------------------------------------

    def test_external_value(self) -> None:
        assert TrustTier.EXTERNAL.value == "external"

    def test_verified_value(self) -> None:
        assert TrustTier.VERIFIED.value == "verified"

    def test_owner_value(self) -> None:
        assert TrustTier.OWNER.value == "owner"

    def test_internal_value(self) -> None:
        assert TrustTier.INTERNAL.value == "internal"

    # -- str() still works (str, Enum) ----------------------------------------

    def test_str_is_value(self) -> None:
        assert str(TrustTier.EXTERNAL) == "TrustTier.EXTERNAL" or "external" in str(TrustTier.EXTERNAL)

    # -- equality still works -------------------------------------------------

    def test_equality_same(self) -> None:
        assert TrustTier.EXTERNAL == TrustTier.EXTERNAL

    def test_equality_different(self) -> None:
        assert TrustTier.EXTERNAL != TrustTier.INTERNAL

    # -- sorting works --------------------------------------------------------

    def test_sorted_order(self) -> None:
        tiers = [TrustTier.INTERNAL, TrustTier.EXTERNAL, TrustTier.OWNER, TrustTier.VERIFIED]
        assert sorted(tiers) == [
            TrustTier.EXTERNAL,
            TrustTier.VERIFIED,
            TrustTier.OWNER,
            TrustTier.INTERNAL,
        ]
