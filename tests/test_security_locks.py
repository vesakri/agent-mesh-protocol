"""
Tests for C15 — async/threading locks on all 5 security modules.

Verifies:
1. Each module has a _lock attribute of the correct type.
2. Concurrent access does not corrupt shared state.
"""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from ampro.security.concurrency_limiter import ConcurrencyLimiter
from ampro.security.dedup import InMemoryDedupStore
from ampro.security.nonce_tracker import NonceTracker
from ampro.security.rate_limiter import RateLimiter
from ampro.security.sender_tracker import SenderTracker


# ---------------------------------------------------------------------------
# Test 1: Lock attribute exists on every security module
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls,lock_type",
    [
        (InMemoryDedupStore, asyncio.Lock),
        (NonceTracker, threading.Lock),
        (ConcurrencyLimiter, threading.Lock),
        (SenderTracker, threading.Lock),
        (RateLimiter, threading.Lock),
    ],
    ids=[
        "InMemoryDedupStore",
        "NonceTracker",
        "ConcurrencyLimiter",
        "SenderTracker",
        "RateLimiter",
    ],
)
def test_lock_attribute_exists(cls, lock_type):
    """Every security module MUST have a _lock of the correct type."""
    instance = cls()
    assert hasattr(instance, "_lock"), f"{cls.__name__} missing _lock attribute"
    lock = instance._lock
    if lock_type is threading.Lock:
        assert hasattr(lock, "acquire") and hasattr(lock, "release"), (
            f"{cls.__name__}._lock should be a threading lock, got {type(lock)}"
        )
    else:
        assert isinstance(lock, lock_type), (
            f"{cls.__name__}._lock should be {lock_type.__name__}, got {type(lock)}"
        )


# ---------------------------------------------------------------------------
# Test 2: Concurrent is_duplicate calls on InMemoryDedupStore
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dedup_concurrent_is_duplicate():
    """Concurrent is_duplicate calls must not corrupt the seen dict.

    Fire 200 coroutines each checking a unique message_id. Every single
    one should report *not* duplicate (first time seen). Then a second
    round with the same IDs should all be duplicates.
    """
    store = InMemoryDedupStore(window_seconds=300, max_size=100_000)

    ids = [f"msg-{i}" for i in range(200)]

    # Round 1 — all should be non-duplicate
    results = await asyncio.gather(*(store.is_duplicate(mid) for mid in ids))
    assert all(r is False for r in results), "First-time IDs should not be duplicates"

    # Round 2 — all should now be duplicate
    results2 = await asyncio.gather(*(store.is_duplicate(mid) for mid in ids))
    assert all(r is True for r in results2), "Repeated IDs should be duplicates"


# ---------------------------------------------------------------------------
# Test 3: Concurrent acquire/release on ConcurrencyLimiter
# ---------------------------------------------------------------------------


def test_concurrency_limiter_threaded_acquire_release():
    """Concurrent acquire + release must maintain total_active invariant.

    Each thread acquires a slot, checks in, then releases. After all
    threads finish, total_active must be 0.
    """
    limiter = ConcurrencyLimiter(max_total=200, per_sender_pct=1.0)
    barrier = threading.Barrier(50)

    def worker(sender: str):
        barrier.wait()
        acquired = limiter.acquire(sender)
        if acquired:
            # Simulate work
            pass
            limiter.release(sender)

    threads = []
    for i in range(50):
        t = threading.Thread(target=worker, args=(f"sender-{i}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert limiter.total_active == 0, (
        f"total_active should be 0 after all releases, got {limiter.total_active}"
    )


# ---------------------------------------------------------------------------
# Test 4: Concurrent check on RateLimiter doesn't exceed limit
# ---------------------------------------------------------------------------


def test_rate_limiter_threaded_check():
    """Concurrent check() calls must not allow more than rpm requests.

    With rpm=20 and 50 threads all calling check() for the same sender,
    exactly 20 should be allowed and 30 rejected.
    """
    limiter = RateLimiter(rpm=20, window_seconds=60)
    barrier = threading.Barrier(50)
    allowed_count = 0
    count_lock = threading.Lock()

    def worker():
        nonlocal allowed_count
        barrier.wait()
        allowed, _info = limiter.check("same-sender")
        if allowed:
            with count_lock:
                allowed_count += 1

    threads = []
    for _ in range(50):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert allowed_count == 20, (
        f"Expected exactly 20 allowed, got {allowed_count}"
    )


# ---------------------------------------------------------------------------
# Test 5: Concurrent record_failure on SenderTracker
# ---------------------------------------------------------------------------


def test_sender_tracker_threaded_record_failure():
    """Concurrent record_failure calls must not lose or duplicate state.

    With failure_threshold=3, three concurrent failures for the same
    sender should escalate to THROTTLED exactly once.
    """
    tracker = SenderTracker(failure_threshold=3, failure_window=300)
    barrier = threading.Barrier(3)
    results: list[str] = []
    results_lock = threading.Lock()

    def worker():
        barrier.wait()
        state = tracker.record_failure("bad-sender")
        with results_lock:
            results.append(state.value)

    threads = []
    for _ in range(3):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # With 3 failures hitting threshold=3, at least the last one should see THROTTLED
    assert "throttled" in results, (
        f"Expected at least one THROTTLED state, got {results}"
    )
    # Final state should be THROTTLED
    from ampro.security.sender_tracker import SenderState
    assert tracker.get_state("bad-sender") == SenderState.THROTTLED
