"""
Agent Protocol — Compliance Types.

Models for GDPR erasure, data export, jurisdiction declaration,
content classification, and data retention policies.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ContentClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PII = "pii"
    SENSITIVE_PII = "sensitive-pii"
    CONFIDENTIAL = "confidential"


class ComplianceJurisdictionInfo(BaseModel):
    """Extended jurisdiction info for compliance declarations (GDPR, data processing, PII).

    Not to be confused with ``ampro.compliance.jurisdiction.JurisdictionInfo``
    which is a lightweight model for cross-border conflict detection.
    """

    jurisdiction: str = Field(description="Primary jurisdiction (ISO 3166-1 alpha-2)")
    additional_jurisdictions: list[str] = Field(default_factory=list, description="Additional jurisdictions that apply (ISO 3166-1 alpha-2 codes)")
    data_processing_agreement_url: str | None = Field(default=None, description="URL to the data processing agreement, if any")
    privacy_policy_url: str | None = Field(default=None, description="URL to the privacy policy, if any")
    frameworks: list[str] = Field(default_factory=list, description="Compliance frameworks in effect (e.g. GDPR, CCPA, HIPAA)")
    data_residency: str | None = Field(default=None, description="Required data residency region (e.g. EU, US-EAST)")
    accepts_pii: bool = Field(default=True, description="Whether this agent accepts personally identifiable information")
    accepts_minors: bool = Field(default=False, description="Whether this agent accepts data from minors (under 16)")
    model_config = {"extra": "ignore"}


class RetentionPolicy(BaseModel):
    messages: str = Field(default="30d", description="Retention period for messages (e.g. 30d, 90d)")
    task_history: str = Field(default="90d", description="Retention period for task history records")
    tool_logs: str = Field(default="90d", description="Retention period for tool invocation logs")
    audit_logs: str = Field(default="365d", description="Retention period for audit log entries")
    sessions: str = Field(default="7d", description="Retention period for session data")
    model_config = {"extra": "ignore"}


class ErasureRequest(BaseModel):
    subject_id: str = Field(description="Unique identifier of the data subject requesting erasure")
    subject_proof: str = Field(description="RESERVED for v2. Proof of identity for the data subject (e.g. signed token). Not validated in v1 — the sender's identity from the verified envelope is the sole authorization signal. This field is retained in the schema for forward compatibility; supply any non-empty string.")
    scope: Literal["all", "conversations", "tasks", "tools"] = Field(description="Scope of data to erase")
    reason: Literal["user_request", "account_deletion", "consent_withdrawn", "legal_order"] = Field(description="Legal basis for the erasure request")
    deadline: str = Field(description="ISO 8601 deadline for completion")
    callback_url: str | None = Field(default=None, description="URL to notify when erasure is complete")
    model_config = {"extra": "ignore"}


class RetainedRecord(BaseModel):
    """A record retained despite an erasure request, with its legal justification.

    Supports partial-erasure tracking: not every record can be deleted
    (audit logs, regulatory-retention windows, etc.).  Each retained
    record MUST carry a machine-readable ``reason`` and a human
    ``legal_basis`` citing the statute or policy.
    """

    record_id: str = Field(..., max_length=256, description="Stable record identifier")
    category: str = Field(
        ...,
        description="e.g. 'audit_log', 'financial_record'",
    )
    reason: Literal["legal_hold", "regulatory_retention", "user_denied"] = Field(
        ..., description="Machine-readable retention cause",
    )
    legal_basis: str = Field(
        ...,
        max_length=512,
        description="Statute or policy reference",
    )
    review_after: datetime | None = Field(
        default=None,
        description="Timestamp after which retention should be re-evaluated",
    )

    model_config = {"extra": "ignore"}


class ErasureResponse(BaseModel):
    subject_id: str = Field(description="Unique identifier of the data subject whose data was erased")
    status: Literal["completed", "partial", "failed"] = Field(description="Outcome status of the erasure operation")
    records_deleted: int = Field(default=0, description="Total number of records deleted")
    categories_deleted: list[str] = Field(default_factory=list, description="Data categories that were successfully deleted")
    retained: list[RetainedRecord] = Field(
        default_factory=list,
        description="Records retained with legal justification for each",
    )
    completed_at: str = Field(description="ISO 8601 timestamp when erasure was completed")
    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_retained(cls, values: Any) -> Any:
        """Accept legacy ``list[dict]`` input for ``retained`` (best-effort).

        Older callers may still emit untyped dictionaries.  We upgrade
        each dict to :class:`RetainedRecord`; dicts missing required
        fields are rejected by the nested model (the dict remains in
        place and Pydantic will raise a ValidationError).
        """
        if not isinstance(values, dict):
            return values
        retained = values.get("retained")
        if not isinstance(retained, list):
            return values
        upgraded: list[Any] = []
        for item in retained:
            if isinstance(item, dict):
                upgraded.append(RetainedRecord.model_validate(item))
            else:
                upgraded.append(item)
        values = {**values, "retained": upgraded}
        return values


class ExportRequest(BaseModel):
    subject_id: str = Field(description="Unique identifier of the data subject requesting export")
    subject_proof: str = Field(description="Proof of identity for the data subject (e.g. signed token)")
    scope: Literal["all", "conversations", "tasks", "tools"] = Field(default="all", description="Scope of data to export")
    format: Literal["json", "csv"] = Field(default="json", description="Desired export file format")
    callback_url: str | None = Field(default=None, description="URL to notify when export is ready for download")
    model_config = {"extra": "ignore"}


class ExportResponse(BaseModel):
    subject_id: str = Field(description="Unique identifier of the data subject whose data was exported")
    status: Literal["completed", "partial", "failed"] = Field(description="Outcome status of the export operation")
    export_url: str | None = Field(default=None, description="Signed URL to download the exported data package")
    size_bytes: int | None = Field(default=None, description="Total size of the export in bytes")
    expires_at: str | None = Field(default=None, description="ISO 8601 timestamp when the download URL expires")
    categories_exported: list[str] = Field(default_factory=list, description="Data categories included in the export")
    model_config = {"extra": "ignore"}
