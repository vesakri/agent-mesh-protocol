"""Tests for the typed RetainedRecord schema in ErasureResponse."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ampro.compliance.types import ErasureResponse, RetainedRecord


def test_retained_record_typed_schema():
    """RetainedRecord requires all structured fields; the ErasureResponse holds them."""
    retained = RetainedRecord(
        record_id="rec_123",
        category="audit_log",
        reason="regulatory_retention",
        legal_basis="SOX section 802 - 7 year retention",
        review_after=datetime(2033, 1, 1, tzinfo=timezone.utc),
    )
    response = ErasureResponse(
        subject_id="user_42",
        status="partial",
        records_deleted=17,
        categories_deleted=["conversations", "tasks"],
        retained=[retained],
        completed_at="2026-04-21T00:00:00Z",
    )

    assert len(response.retained) == 1
    assert response.retained[0].record_id == "rec_123"
    assert response.retained[0].reason == "regulatory_retention"
    assert response.retained[0].legal_basis.startswith("SOX")


def test_legacy_dict_retained_is_upgraded():
    """Legacy ``list[dict]`` input MUST be coerced to RetainedRecord."""
    response = ErasureResponse(
        subject_id="user_42",
        status="partial",
        records_deleted=1,
        retained=[
            {
                "record_id": "rec_1",
                "category": "financial_record",
                "reason": "legal_hold",
                "legal_basis": "ongoing litigation docket #12345",
            }
        ],
        completed_at="2026-04-21T00:00:00Z",
    )

    assert len(response.retained) == 1
    assert isinstance(response.retained[0], RetainedRecord)
    assert response.retained[0].category == "financial_record"


def test_retained_record_rejects_invalid_reason():
    """Unknown retention reasons are rejected."""
    with pytest.raises(ValidationError):
        RetainedRecord(
            record_id="rec_1",
            category="audit_log",
            reason="i_felt_like_it",  # not in the Literal set
            legal_basis="none",
        )


def test_retained_record_rejects_missing_required_fields():
    """Legacy dicts missing required fields are rejected."""
    with pytest.raises(ValidationError):
        ErasureResponse(
            subject_id="user_42",
            status="partial",
            records_deleted=0,
            retained=[{"record_id": "rec_1"}],  # missing category, reason, legal_basis
            completed_at="2026-04-21T00:00:00Z",
        )
