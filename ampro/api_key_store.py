"""
Agent Protocol — API Key Store.

In-memory API key allowlist with brute force protection.

Spec ref: Sections 2.3, 3.6
"""

from __future__ import annotations

import time


class ApiKeyStore:
    def __init__(self, max_failures: int = 10, block_seconds: int = 900):
        self._keys: dict[str, str] = {}
        self._failures: dict[str, list[float]] = {}
        self._blocked: dict[str, float] = {}
        self._max_failures = max_failures
        self._block_seconds = block_seconds

    def add_key(self, key: str, agent_id: str) -> None:
        self._keys[key] = agent_id

    def remove_key(self, key: str) -> None:
        self._keys.pop(key, None)

    def validate(self, key: str) -> str | None:
        return self._keys.get(key)

    def is_blocked(self, ip: str) -> bool:
        blocked_until = self._blocked.get(ip)
        if blocked_until is None:
            return False
        if time.monotonic() > blocked_until:
            del self._blocked[ip]
            self._failures.pop(ip, None)
            return False
        return True

    def record_failure(self, ip: str) -> None:
        now = time.monotonic()
        failures = self._failures.setdefault(ip, [])
        failures[:] = [t for t in failures if now - t < 60]
        failures.append(now)
        if len(failures) >= self._max_failures:
            self._blocked[ip] = now + self._block_seconds

    def reset_failures(self, ip: str) -> None:
        self._failures.pop(ip, None)
        self._blocked.pop(ip, None)
