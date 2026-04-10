"""
Agent Protocol — Nonce Tracker.

Tracks seen nonces to prevent replay attacks on sensitive operations.
In-memory with 1-hour sliding window per spec Section 3.4.
"""

from __future__ import annotations

import time


class NonceTracker:
    """Track seen nonces with sliding window expiry."""

    def __init__(self, window_seconds: int = 3600, max_size: int = 100_000):
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
        sorted_entries = sorted(self._seen.items(), key=lambda x: x[1])
        to_remove = len(sorted_entries) - target
        for key, _ in sorted_entries[:to_remove]:
            del self._seen[key]

    def is_replay(self, nonce: str) -> bool:
        """Check if nonce was already seen. Returns True if replay detected."""
        self._cleanup()
        if nonce in self._seen:
            return True
        self._seen[nonce] = time.monotonic()
        self._evict_oldest()
        return False

    def seen_count(self) -> int:
        """Number of nonces currently tracked."""
        self._cleanup()
        return len(self._seen)
