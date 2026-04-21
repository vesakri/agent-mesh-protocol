"""Tests for C16 — RateLimiter._evict_stale_senders memory bounds."""

from __future__ import annotations

import time

from ampro.security.rate_limiter import RateLimiter


class TestEvictStaleSenders:
    """Verify that _evict_stale_senders enforces max_senders."""

    def test_oldest_sender_evicted_when_over_max(self):
        """After max_senders unique senders, the oldest is evicted."""
        max_s = 5
        limiter = RateLimiter(rpm=100, window_seconds=60, max_senders=max_s)

        # Fill up to max_senders + 1 so eviction fires
        for i in range(max_s + 1):
            allowed, _ = limiter.check(f"sender-{i}")
            assert allowed

        # The dict should be capped at max_senders
        assert limiter.sender_count() <= max_s

        # sender-0 was the oldest (first inserted, smallest most-recent
        # timestamp) and should have been evicted.
        assert "sender-0" not in limiter._requests

    def test_stale_senders_cleaned_up(self):
        """Senders whose entire request list is older than the window
        are removed even if we are under max_senders."""
        window = 2  # seconds
        limiter = RateLimiter(rpm=100, window_seconds=window, max_senders=100)

        # Inject a sender with timestamps far in the past
        ancient_time = time.monotonic() - window - 10
        limiter._requests["stale-sender"] = [ancient_time]

        # Add a fresh sender to trigger eviction
        # We need to go over max_senders for phase-2, but phase-1 triggers
        # regardless — let's trigger it by calling check which invokes
        # _evict_stale_senders at the end.
        limiter.check("fresh-sender")

        # The stale sender should have been cleaned up (phase 1)
        assert "stale-sender" not in limiter._requests
        # The fresh sender should remain
        assert "fresh-sender" in limiter._requests

    def test_active_senders_not_evicted(self):
        """Senders with recent requests survive eviction."""
        max_s = 3
        limiter = RateLimiter(rpm=100, window_seconds=60, max_senders=max_s)

        # Create max_senders active senders
        for i in range(max_s):
            limiter.check(f"active-{i}")

        # All should be present — we're at max, not over
        assert limiter.sender_count() == max_s
        for i in range(max_s):
            assert f"active-{i}" in limiter._requests

        # Now add one more — only the oldest active gets evicted, not a
        # random one.
        limiter.check("newcomer")
        assert limiter.sender_count() <= max_s
        assert "newcomer" in limiter._requests

    def test_memory_stays_bounded(self):
        """len(_requests) never exceeds max_senders + 1 even under load.

        The +1 accounts for the new sender that was just added by check()
        before _evict_stale_senders runs.  After eviction the count must
        be <= max_senders.
        """
        max_s = 10
        limiter = RateLimiter(rpm=1000, window_seconds=60, max_senders=max_s)

        # Hammer the limiter with many unique senders
        for i in range(max_s * 5):
            limiter.check(f"flood-{i}")
            # After every check, we should never be far over max_senders.
            # check() adds one entry then calls _evict_stale_senders, so
            # post-call we should be at most max_senders.
            assert limiter.sender_count() <= max_s, (
                f"sender_count {limiter.sender_count()} exceeded max_senders "
                f"{max_s} after sender flood-{i}"
            )
