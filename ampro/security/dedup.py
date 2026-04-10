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
    def __init__(self, window_seconds: int = 300, max_size: int = 100_000):
        self._window = window_seconds
        self._max_size = max_size
        self._seen: dict[str, float] = {}

    def _cleanup(self) -> None:
        now = time.monotonic()
        expired = [k for k, v in self._seen.items() if now - v > self._window]
        for k in expired:
            del self._seen[k]

    def _evict_oldest(self) -> None:
        """Evict oldest entries down to 90% of max_size to prevent unbounded growth."""
        if len(self._seen) <= self._max_size:
            return
        target = int(self._max_size * 0.9)
        # Sort by timestamp (oldest first) and keep only the newest `target` entries
        sorted_entries = sorted(self._seen.items(), key=lambda x: x[1])
        to_remove = len(sorted_entries) - target
        for key, _ in sorted_entries[:to_remove]:
            del self._seen[key]

    async def is_duplicate(self, message_id: str) -> bool:
        self._cleanup()
        if message_id in self._seen:
            return True
        self._seen[message_id] = time.monotonic()
        self._evict_oldest()
        return False

    async def mark_seen(self, message_id: str) -> None:
        self._seen[message_id] = time.monotonic()
