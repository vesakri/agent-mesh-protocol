"""Shared fixtures for compliance test suite."""
from __future__ import annotations

import time

import pytest

from ampro.compliance.registry import (
    NoOpMinorRegistry,
    set_minor_registry,
)


class MockMinorRegistry:
    """Test-only registry with injectable data."""

    def __init__(self, minors: dict[str, str | None] | None = None):
        self._minors = minors or {}

    def is_minor(self, user_id: str) -> bool:
        return user_id in self._minors

    def guardian_of(self, user_id: str) -> str | None:
        return self._minors.get(user_id)


@pytest.fixture
def mock_minor_registry():
    return MockMinorRegistry()


@pytest.fixture(autouse=True)
def reset_minor_registry():
    """Reset to NoOp after each test."""
    yield
    set_minor_registry(NoOpMinorRegistry())


@pytest.fixture(autouse=True)
def seed_trust_cache_for_compliance():
    """Pre-populate the public key cache so cost-receipt and bus tests
    can verify signatures without going through a live trust resolver.
    """
    from ampro.trust.resolver import _PUBLIC_KEY_CACHE, _reset_public_key_cache_for_tests

    import base64
    import json
    from pathlib import Path

    # Self-contained fixture — no dependency on the host platform's tree.
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "test-keypair.json"
    )

    if fixture_path.exists():
        data = json.loads(fixture_path.read_text())
        pad = lambda s: s + "=" * (-len(s) % 4)  # noqa: E731
        raw_pub = base64.urlsafe_b64decode(pad(data["public_key_b64url"]))
        _PUBLIC_KEY_CACHE[data["key_id"]] = (time.time() + 3600, raw_pub)

    yield
    _reset_public_key_cache_for_tests()
