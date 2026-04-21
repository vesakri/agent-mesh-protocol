"""Tests for MinorRegistry protocol + set/get + NoOp default."""
from __future__ import annotations

from ampro.compliance.registry import (
    MinorRegistry,
    NoOpMinorRegistry,
    get_minor_registry,
    set_minor_registry,
)


def test_protocol_satisfiable_by_mock(mock_minor_registry):
    assert isinstance(mock_minor_registry, MinorRegistry) or hasattr(mock_minor_registry, "is_minor")


def test_set_get_roundtrip(mock_minor_registry):
    set_minor_registry(mock_minor_registry)
    assert get_minor_registry() is mock_minor_registry


def test_default_is_noop():
    reg = get_minor_registry()
    assert isinstance(reg, NoOpMinorRegistry)
    assert reg.is_minor("any-user") is False
    assert reg.guardian_of("any-user") is None


def test_register_twice_last_wins():
    r1 = NoOpMinorRegistry()
    r2 = NoOpMinorRegistry()
    set_minor_registry(r1)
    set_minor_registry(r2)
    assert get_minor_registry() is r2


def test_mock_registry_returns_seeded_data():
    from tests.compliance.conftest import MockMinorRegistry
    reg = MockMinorRegistry(minors={"kid-1": "guardian-1", "kid-2": None})
    assert reg.is_minor("kid-1") is True
    assert reg.guardian_of("kid-1") == "guardian-1"
    assert reg.is_minor("kid-2") is True
    assert reg.guardian_of("kid-2") is None
    assert reg.is_minor("adult-1") is False
