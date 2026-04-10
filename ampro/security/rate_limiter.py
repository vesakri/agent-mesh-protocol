"""
Agent Protocol — Per-Sender Rate Limiter.

In-memory sliding window rate limiter per spec Sections 3.13.1, 4.4.
Returns rate limit info for X-RateLimit-* response headers.
"""

from __future__ import annotations

import time
from ampro.security.rate_limit import RateLimitInfo


class RateLimiter:
    """Per-sender sliding window rate limiter."""

    def __init__(self, rpm: int = 60, window_seconds: int = 60):
        self._rpm = rpm
        self._window = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, sender: str) -> tuple[bool, RateLimitInfo]:
        """
        Check if sender is within rate limit.
        Returns (allowed, info). If not allowed, caller should return 429.
        """
        now = time.monotonic()
        requests = self._requests.setdefault(sender, [])
        # Prune old requests
        requests[:] = [t for t in requests if now - t < self._window]

        remaining = max(0, self._rpm - len(requests))
        reset_at = int(time.time()) + self._window

        info = RateLimitInfo(
            limit=self._rpm,
            remaining=remaining,
            reset=reset_at,
        )

        if len(requests) >= self._rpm:
            return False, info

        requests.append(now)
        info.remaining = max(0, self._rpm - len(requests))
        return True, info

    def sender_count(self) -> int:
        """Number of senders currently tracked."""
        return len(self._requests)
