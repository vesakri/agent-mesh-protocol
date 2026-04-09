"""
Agent Protocol — Nonce Tracker.

Tracks seen nonces to prevent replay attacks on sensitive operations.
In-memory with 1-hour sliding window per spec Section 3.4.
"""

from __future__ import annotations

import time


class NonceTracker:
    """Track seen nonces with sliding window expiry."""

    def __init__(self, window_seconds: int = 3600):
        self._window = window_seconds
        self._seen: dict[str, float] = {}

    def _cleanup(self) -> None:
        now = time.monotonic()
        expired = [k for k, v in self._seen.items() if now - v > self._window]
        for k in expired:
            del self._seen[k]

    def is_replay(self, nonce: str) -> bool:
        """Check if nonce was already seen. Returns True if replay detected."""
        self._cleanup()
        if nonce in self._seen:
            return True
        self._seen[nonce] = time.monotonic()
        return False

    def seen_count(self) -> int:
        """Number of nonces currently tracked."""
        self._cleanup()
        return len(self._seen)
