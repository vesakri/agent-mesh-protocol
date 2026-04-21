"""MinorRegistry Protocol for compliance middleware.

The protocol package stays host-agnostic. A host platform registers a
concrete implementation at runtime startup. The default is a no-op that
returns is_minor=False for everyone (AM-2 from the spec amendment).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MinorRegistry(Protocol):
    def is_minor(self, user_id: str) -> bool: ...
    def guardian_of(self, user_id: str) -> str | None: ...


class NoOpMinorRegistry:
    """Default no-op registry. Returns is_minor=False for everyone.

    The host platform supplies a concrete implementation (backed by
    its user database or IdP) when minor-protection semantics are
    required for its deployment.
    """

    def is_minor(self, user_id: str) -> bool:
        return False

    def guardian_of(self, user_id: str) -> str | None:
        return None


_registry: MinorRegistry = NoOpMinorRegistry()


def set_minor_registry(reg: MinorRegistry) -> None:
    global _registry
    _registry = reg


def get_minor_registry() -> MinorRegistry:
    return _registry
