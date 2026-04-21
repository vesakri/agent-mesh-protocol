"""
Agent Protocol — Per-Sender Concurrency Limiter.

Tracks active tasks per sender. Single sender cannot consume
more than 50% of max_concurrent_tasks per spec Section 3.13.1.
"""

from __future__ import annotations

import threading


class ConcurrencyLimiter:
    """Per-sender concurrent task limiter."""

    def __init__(self, max_total: int = 50, per_sender_pct: float = 0.5):
        self._max_total = max_total
        self._per_sender_max = int(max_total * per_sender_pct)
        self._active: dict[str, int] = {}
        self._lock = threading.Lock()

    @property
    def total_active(self) -> int:
        with self._lock:
            return sum(self._active.values())

    def can_accept(self, sender: str) -> bool:
        """Check if sender can start a new task."""
        with self._lock:
            if sum(self._active.values()) >= self._max_total:
                return False
            sender_count = self._active.get(sender, 0)
            if sender_count >= self._per_sender_max:
                return False
            return True

    def acquire(self, sender: str) -> bool:
        """Try to acquire a task slot. Returns False if at limit."""
        with self._lock:
            if sum(self._active.values()) >= self._max_total:
                return False
            sender_count = self._active.get(sender, 0)
            if sender_count >= self._per_sender_max:
                return False
            self._active[sender] = sender_count + 1
            return True

    def release(self, sender: str) -> None:
        """Release a task slot when task completes.

        WARNING: release() must be called after task completion. Consider using
        a context manager or timeout mechanism to prevent leaked slots.
        """
        with self._lock:
            count = self._active.get(sender, 0)
            if count <= 1:
                self._active.pop(sender, None)
            else:
                self._active[sender] = count - 1

    def sender_active(self, sender: str) -> int:
        """Number of active tasks for a sender."""
        with self._lock:
            return self._active.get(sender, 0)
