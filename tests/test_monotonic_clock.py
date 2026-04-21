"""
Tests for P0.D Task 5.2 + 5.4 — Monotonic clock consistency.

Verifies that all security modules use ``time.monotonic()`` for TTL/window
arithmetic, and that ``time.time()`` is NOT used except for externally-visible
timestamps (HTTP headers, wire-format signatures).

Also verifies rate limiter behaviour:
- Concurrent requests under the limit all succeed.
- Requests over the limit are rejected even if the wall-clock is manipulated.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import threading
import time
from unittest import mock

import pytest


# ── helpers ────────────────────────────────────────────────────────────────


def _count_time_time_calls(source: str) -> list[int]:
    """Return line numbers where ``time.time()`` is called in *source*.

    Uses AST parsing so string mentions (docstrings, comments) are ignored.
    Detects both ``time.time()`` and alias patterns like ``_time.time()``.
    """
    tree = ast.parse(textwrap.dedent(source))
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match: time.time() or _time.time()
        if isinstance(func, ast.Attribute) and func.attr == "time":
            if isinstance(func.value, ast.Name) and func.value.id in ("time", "_time"):
                hits.append(node.lineno)
    return hits


# ── Source-level checks ────────────────────────────────────────────────────


class TestNoTimeTimeCalls:
    """Verify that security modules do NOT call ``time.time()`` for TTL math.

    We AST-parse each module's source code and assert zero ``time.time()``
    calls. Allowed exceptions are annotated in the test.
    """

    def test_nonce_tracker_no_time_time(self):
        from ampro.security import nonce_tracker

        source = inspect.getsource(nonce_tracker)
        hits = _count_time_time_calls(source)
        assert hits == [], (
            f"nonce_tracker.py calls time.time() at lines {hits} — "
            "should use time.monotonic()"
        )

    def test_dedup_no_time_time(self):
        from ampro.security import dedup

        source = inspect.getsource(dedup)
        hits = _count_time_time_calls(source)
        assert hits == [], (
            f"dedup.py calls time.time() at lines {hits} — "
            "should use time.monotonic()"
        )

    def test_sender_tracker_no_time_time(self):
        from ampro.security import sender_tracker

        source = inspect.getsource(sender_tracker)
        hits = _count_time_time_calls(source)
        assert hits == [], (
            f"sender_tracker.py calls time.time() at lines {hits} — "
            "should use time.monotonic()"
        )

    def test_concurrency_limiter_no_time_time(self):
        from ampro.security import concurrency_limiter

        source = inspect.getsource(concurrency_limiter)
        hits = _count_time_time_calls(source)
        assert hits == [], (
            f"concurrency_limiter.py calls time.time() at lines {hits} — "
            "should use time.monotonic()"
        )

    def test_rate_limiter_time_time_only_for_reset_header(self):
        """rate_limiter.py may use time.time() ONLY for the X-RateLimit-Reset
        HTTP header (a Unix epoch timestamp). All window arithmetic must use
        time.monotonic().
        """
        from ampro.security import rate_limiter

        source = inspect.getsource(rate_limiter)
        hits = _count_time_time_calls(source)
        # Exactly 1 hit is allowed — the reset_at line for the HTTP header.
        assert len(hits) <= 1, (
            f"rate_limiter.py calls time.time() at lines {hits} — "
            "only one call (for X-RateLimit-Reset header) is permitted"
        )

    def test_trust_resolver_no_time_time_for_cache(self):
        """trust/resolver.py public key cache must use time.monotonic()."""
        from ampro.trust import resolver

        source = inspect.getsource(resolver.get_public_key)
        hits = _count_time_time_calls(source)
        assert hits == [], (
            f"resolver.get_public_key() calls time.time() at lines {hits} — "
            "cache TTL should use time.monotonic()"
        )


# ── Behavioural checks ────────────────────────────────────────────────────


class TestRateLimiterMonotonicBehaviour:
    """Verify rate limiter correctness under concurrent and clock-skew scenarios."""

    def test_concurrent_requests_under_limit_all_succeed(self):
        """When N concurrent requests are under the limit, all should succeed."""
        from ampro.security.rate_limiter import RateLimiter

        limiter = RateLimiter(rpm=50, window_seconds=60)
        barrier = threading.Barrier(30)
        results: list[bool] = []
        results_lock = threading.Lock()

        def worker():
            barrier.wait()
            allowed, _ = limiter.check("test-sender")
            with results_lock:
                results.append(allowed)

        threads = [threading.Thread(target=worker) for _ in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(results), (
            f"All 30 requests (under limit of 50) should succeed, "
            f"but {results.count(False)} were rejected"
        )

    def test_concurrent_requests_over_limit_rejected(self):
        """When N concurrent requests exceed the limit, excess must be rejected."""
        from ampro.security.rate_limiter import RateLimiter

        limiter = RateLimiter(rpm=10, window_seconds=60)
        barrier = threading.Barrier(30)
        allowed_count = 0
        count_lock = threading.Lock()

        def worker():
            nonlocal allowed_count
            barrier.wait()
            allowed, _ = limiter.check("same-sender")
            if allowed:
                with count_lock:
                    allowed_count += 1

        threads = [threading.Thread(target=worker) for _ in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert allowed_count == 10, (
            f"Expected exactly 10 allowed (rpm=10), got {allowed_count}"
        )

    def test_rate_limiter_immune_to_wall_clock_rollback(self):
        """Monotonic clock prevents bypass via wall-clock manipulation.

        We mock ``time.time`` to jump backwards. The rate limiter's window
        arithmetic (which uses ``time.monotonic``) must NOT be affected —
        over-limit requests must still be rejected.
        """
        from ampro.security.rate_limiter import RateLimiter

        limiter = RateLimiter(rpm=5, window_seconds=60)

        # Fill up the limit
        for _ in range(5):
            allowed, _ = limiter.check("victim")
            assert allowed

        # Manipulate wall clock backward by 120 seconds
        original_time = time.time
        with mock.patch("time.time", return_value=original_time() - 120):
            # Should still be rejected because monotonic clock is unaffected
            allowed, info = limiter.check("victim")
            assert not allowed, (
                "Rate limiter should reject requests even when wall clock is "
                "rolled back — window uses time.monotonic()"
            )
            assert info.remaining == 0

    def test_rate_limiter_reset_is_unix_timestamp(self):
        """The ``reset`` field in RateLimitInfo must be a Unix epoch timestamp,
        not a monotonic value. Clients need this for the X-RateLimit-Reset header.
        """
        from ampro.security.rate_limiter import RateLimiter

        limiter = RateLimiter(rpm=100, window_seconds=60)
        _, info = limiter.check("ts-check-sender")

        # A Unix timestamp for "now + 60s" should be roughly time.time() + 60.
        # A monotonic() value would be much smaller (seconds since boot).
        # We check that reset is a plausible Unix epoch (> 1_600_000_000 = Sep 2020).
        assert info.reset > 1_600_000_000, (
            f"reset={info.reset} looks like a monotonic value, not a Unix timestamp"
        )


class TestNonceTrackerMonotonic:
    """Verify nonce tracker uses monotonic clock for replay window."""

    def test_nonce_replay_detected_despite_wall_clock_rollback(self):
        from ampro.security.nonce_tracker import NonceTracker

        tracker = NonceTracker(window_seconds=3600)

        # First use — not a replay
        assert tracker.is_replay("nonce-1") is False

        # Roll back wall clock
        original_time = time.time
        with mock.patch("time.time", return_value=original_time() - 7200):
            # Monotonic clock is unaffected, so replay is still detected
            assert tracker.is_replay("nonce-1") is True


class TestSenderTrackerMonotonic:
    """Verify sender tracker uses monotonic clock for failure windows."""

    def test_failure_window_immune_to_wall_clock(self):
        from ampro.security.sender_tracker import SenderState, SenderTracker

        tracker = SenderTracker(failure_threshold=3, failure_window=300)

        # Record 3 failures → should become THROTTLED
        for _ in range(3):
            tracker.record_failure("bad-guy")

        assert tracker.get_state("bad-guy") == SenderState.THROTTLED

        # Even with wall-clock manipulation, state remains THROTTLED
        original_time = time.time
        with mock.patch("time.time", return_value=original_time() - 600):
            # Monotonic clock is not affected, so state should persist
            assert tracker.get_state("bad-guy") == SenderState.THROTTLED
