"""
Agent Protocol — Message Deduplication Store.

In-memory dedup with TTL-based expiry. A persistent-store-backed version
can be swapped in via the DedupStore protocol.
"""

from __future__ import annotations

import time
from typing import Protocol


class DedupStore(Protocol):
    async def is_duplicate(self, message_id: str) -> bool: ...
    async def mark_seen(self, message_id: str) -> None: ...


class InMemoryDedupStore:
    def __init__(self, window_seconds: int = 300):
        self._window = window_seconds
        self._seen: dict[str, float] = {}

    def _cleanup(self) -> None:
        now = time.monotonic()
        expired = [k for k, v in self._seen.items() if now - v > self._window]
        for k in expired:
            del self._seen[k]

    async def is_duplicate(self, message_id: str) -> bool:
        self._cleanup()
        if message_id in self._seen:
            return True
        self._seen[message_id] = time.monotonic()
        return False

    async def mark_seen(self, message_id: str) -> None:
        self._seen[message_id] = time.monotonic()
