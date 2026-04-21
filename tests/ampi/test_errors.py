"""Tests for AMPI error hierarchy."""
from __future__ import annotations


def test_amp_error_has_code_and_message():
    from ampro.ampi.errors import AMPError
    err = AMPError("test_code", "something went wrong")
    assert err.code == "test_code"
    assert err.message == "something went wrong"
    assert str(err) == "test_code: something went wrong"


def test_amp_error_optional_details():
    from ampro.ampi.errors import AMPError
    err = AMPError("test", "msg", details={"key": "val"})
    assert err.details == {"key": "val"}


def test_stream_limit_exceeded_is_amp_error():
    from ampro.ampi.errors import AMPError, StreamLimitExceeded
    err = StreamLimitExceeded("max_events", limit=10000, current=10001)
    assert isinstance(err, AMPError)
    assert err.code == "stream_limit_exceeded"
    assert err.limit == 10000
    assert err.current == 10001


def test_backpressure_error_is_amp_error():
    from ampro.ampi.errors import AMPError, BackpressureError
    err = BackpressureError("client_slow")
    assert isinstance(err, AMPError)
    assert err.code == "backpressure"
    assert err.reason == "client_slow"


def test_amp_error_to_problem_detail():
    from ampro.ampi.errors import AMPError
    err = AMPError("invalid_scope", "scope not allowed")
    pd = err.to_problem_detail(status=403)
    assert pd.status == 403
    assert "invalid_scope" in pd.detail
