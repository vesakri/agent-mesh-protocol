"""Tests for C11 — RegistryRegistration.slug validation.

The slug field MUST enforce:
- 3-30 characters
- Lowercase alphanumeric + hyphens only
- No consecutive hyphens
- Cannot start or end with a hyphen
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from ampro.registry.types import RegistryRegistration


def _make_registration(**overrides) -> RegistryRegistration:
    """Helper to build a valid RegistryRegistration with optional overrides."""
    defaults = {
        "slug": "my-agent",
        "endpoint": "https://agent.example.com/message",
        "public_key": "dGVzdC1rZXk=",
        "proof": "dGVzdC1wcm9vZg==",
    }
    defaults.update(overrides)
    return RegistryRegistration(**defaults)


class TestSlugValidCases:
    """Slugs that MUST be accepted."""

    def test_simple_slug(self):
        reg = _make_registration(slug="my-agent")
        assert reg.slug == "my-agent"

    def test_all_lowercase_alpha(self):
        reg = _make_registration(slug="myagent")
        assert reg.slug == "myagent"

    def test_all_digits(self):
        reg = _make_registration(slug="123")
        assert reg.slug == "123"

    def test_min_length_boundary(self):
        reg = _make_registration(slug="abc")
        assert reg.slug == "abc"

    def test_max_length_boundary(self):
        slug = "a" * 30
        reg = _make_registration(slug=slug)
        assert reg.slug == slug

    def test_mixed_alphanumeric_with_hyphens(self):
        reg = _make_registration(slug="agent-v2-beta")
        assert reg.slug == "agent-v2-beta"


class TestSlugTooShort:
    """Slugs shorter than 3 chars MUST be rejected."""

    def test_two_chars(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="ab")

    def test_one_char(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="a")

    def test_empty_string(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="")


class TestSlugTooLong:
    """Slugs longer than 30 chars MUST be rejected."""

    def test_31_chars(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="a" * 31)

    def test_50_chars(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="x" * 50)


class TestSlugUppercase:
    """Uppercase characters MUST be rejected."""

    def test_all_uppercase(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="MYAGENT")

    def test_mixed_case(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="MyAgent")

    def test_single_uppercase(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="myAgent")


class TestSlugSpecialChars:
    """Non-alphanumeric non-hyphen characters MUST be rejected."""

    def test_underscore(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="my_agent")

    def test_exclamation(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="my-agent!")

    def test_space(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="my agent")

    def test_dot(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="my.agent")

    def test_at_sign(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="my@agent")


class TestSlugConsecutiveHyphens:
    """Consecutive hyphens MUST be rejected."""

    def test_double_hyphen(self):
        with pytest.raises(ValidationError, match="consecutive hyphens"):
            _make_registration(slug="my--agent")

    def test_triple_hyphen(self):
        with pytest.raises(ValidationError, match="consecutive hyphens"):
            _make_registration(slug="my---agent")


class TestSlugHyphenPosition:
    """Slugs starting or ending with a hyphen MUST be rejected."""

    def test_starts_with_hyphen(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="-my-agent")

    def test_ends_with_hyphen(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="my-agent-")

    def test_only_hyphens(self):
        with pytest.raises(ValidationError, match="slug"):
            _make_registration(slug="---")
