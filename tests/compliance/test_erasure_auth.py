"""Tests for erasure authorization (C8).

6 tests covering the owner / platform / unauthorized matrix plus edge cases.
"""

from __future__ import annotations

import pytest

from ampro.compliance.erasure_auth import is_authorized_to_erase
from ampro.compliance.types import ErasureRequest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PLATFORM_IDENTITIES: frozenset[str] = frozenset({
    "runtime@platform.example.com",
    "admin@platform.example.com",
})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestErasureAuthorization:
    """C8 — owner-only erasure authorization."""

    def test_owner_can_erase_own_data(self) -> None:
        """sender == subject_id => authorized."""
        assert is_authorized_to_erase(
            sender="user-42",
            subject_id="user-42",
            platform_identities=PLATFORM_IDENTITIES,
        ) is True

    def test_platform_identity_can_erase(self) -> None:
        """sender in platform_identities => authorized (system-initiated erasure)."""
        assert is_authorized_to_erase(
            sender="runtime@platform.example.com",
            subject_id="user-42",
            platform_identities=PLATFORM_IDENTITIES,
        ) is True

    def test_unauthorized_third_party_denied(self) -> None:
        """sender != subject_id AND sender not in platform_identities => denied."""
        assert is_authorized_to_erase(
            sender="attacker@evil.example.com",
            subject_id="user-42",
            platform_identities=PLATFORM_IDENTITIES,
        ) is False

    def test_empty_platform_identities(self) -> None:
        """With no platform identities, only owner can erase."""
        # Owner still works
        assert is_authorized_to_erase(
            sender="user-42",
            subject_id="user-42",
            platform_identities=frozenset(),
        ) is True
        # Non-owner denied
        assert is_authorized_to_erase(
            sender="runtime@platform.example.com",
            subject_id="user-42",
            platform_identities=frozenset(),
        ) is False

    def test_subject_proof_field_reserved_for_v2(self) -> None:
        """ErasureRequest.subject_proof field exists and its description
        marks it as RESERVED for v2."""
        field_info = ErasureRequest.model_fields["subject_proof"]
        assert field_info is not None
        assert "RESERVED" in (field_info.description or "")
        assert "v2" in (field_info.description or "").lower()

    def test_keyword_only_arguments(self) -> None:
        """is_authorized_to_erase() requires keyword-only arguments —
        positional calls must raise TypeError."""
        with pytest.raises(TypeError):
            # All three args positional — should fail because of *
            is_authorized_to_erase(  # type: ignore[misc]
                "user-42",
                "user-42",
                frozenset({"runtime@platform.example.com"}),
            )
