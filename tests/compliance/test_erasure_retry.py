"""Tests for erasure propagation retry scheduling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ampro.compliance.erasure_propagation import (
    DEFAULT_RETRY_BASE_DELAY_SEC,
    ErasurePropagationStatusBody,
    MAX_ERASURE_RETRIES,
    MAX_RETRY_DELAY_SEC,
    compute_next_retry,
)


def test_erasure_retry_schedule_exponential_backoff():
    """compute_next_retry doubles the base delay per attempt."""
    now = datetime(2026, 4, 21, tzinfo=timezone.utc)
    base = DEFAULT_RETRY_BASE_DELAY_SEC

    # Attempt 0: base * 2^0 = base.
    r0 = compute_next_retry(0, base, now=now, jitter=0)
    assert r0 == now + timedelta(seconds=base)

    # Attempt 1: base * 2^1 = 2*base.
    r1 = compute_next_retry(1, base, now=now, jitter=0)
    assert r1 == now + timedelta(seconds=2 * base)

    # Attempt 5: base * 2^5 = 32*base.
    r5 = compute_next_retry(5, base, now=now, jitter=0)
    assert r5 == now + timedelta(seconds=32 * base)


def test_retry_schedule_is_capped():
    """High retry counts are capped at MAX_RETRY_DELAY_SEC."""
    now = datetime(2026, 4, 21, tzinfo=timezone.utc)
    r_high = compute_next_retry(25, DEFAULT_RETRY_BASE_DELAY_SEC, now=now, jitter=0)
    assert r_high <= now + timedelta(seconds=MAX_RETRY_DELAY_SEC)


def test_erasure_body_tracks_retry_metadata():
    """The body model accepts retry fields within documented bounds."""
    body = ErasurePropagationStatusBody(
        erasure_id="er_1",
        agent_id="agent://acme.example.com/billing",
        status="pending",
        records_affected=0,
        timestamp="2026-04-21T00:00:00Z",
        retry_count=3,
        next_retry_at=datetime(2026, 4, 21, 1, 0, tzinfo=timezone.utc),
        last_error="connection refused",
        final=False,
    )
    assert body.retry_count == 3
    assert body.next_retry_at is not None
    assert body.last_error == "connection refused"
    assert body.final is False


def test_retry_count_max_enforced():
    """retry_count has an inclusive upper bound of MAX_ERASURE_RETRIES."""
    ErasurePropagationStatusBody(
        erasure_id="er_1",
        agent_id="a",
        status="failed",
        records_affected=0,
        timestamp="2026-04-21T00:00:00Z",
        retry_count=MAX_ERASURE_RETRIES,
        final=True,
    )
    # retry_count > MAX_ERASURE_RETRIES should raise.
    try:
        ErasurePropagationStatusBody(
            erasure_id="er_1",
            agent_id="a",
            status="failed",
            records_affected=0,
            timestamp="2026-04-21T00:00:00Z",
            retry_count=MAX_ERASURE_RETRIES + 1,
        )
    except Exception:
        pass
    else:
        raise AssertionError("retry_count > MAX_ERASURE_RETRIES must be rejected")
