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
        """Evict entries to prevent unbounded growth.

        Phase 1: Remove expired entries (outside TTL window — useless anyway).
        Phase 2: If still over limit, remove oldest by timestamp using heapq
                 for O(n) instead of O(n log n).
        """
        if len(self._seen) <= self._max_size:
            return
        # Phase 1: Remove expired entries
        now = time.monotonic()
        expired = [k for k, v in self._seen.items() if now - v > self._window]
        for k in expired:
            del self._seen[k]
        # Phase 2: If still over limit, remove oldest by timestamp
        if len(self._seen) > self._max_size:
            import heapq

            target = int(self._max_size * 0.9)
            oldest = heapq.nsmallest(
                len(self._seen) - target, self._seen.items(), key=lambda x: x[1]
            )
            for k, _ in oldest:
                del self._seen[k]

    async def is_duplicate(self, message_id: str) -> bool:
        self._cleanup()
        if message_id in self._seen:
            return True
        self._seen[message_id] = time.monotonic()
        self._evict_oldest()
        return False

    async def mark_seen(self, message_id: str) -> None:
        self._seen[message_id] = time.monotonic()
