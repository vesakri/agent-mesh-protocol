"""
Agent Protocol — Compliance Types.

Models for GDPR erasure, data export, jurisdiction declaration,
content classification, and data retention policies.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


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
    subject_proof: str = Field(description="Proof of identity for the data subject (e.g. signed token)")
    scope: Literal["all", "conversations", "tasks", "tools"] = Field(description="Scope of data to erase")
    reason: Literal["user_request", "account_deletion", "consent_withdrawn", "legal_order"] = Field(description="Legal basis for the erasure request")
    deadline: str = Field(description="ISO 8601 deadline for completion")
    callback_url: str | None = Field(default=None, description="URL to notify when erasure is complete")
    model_config = {"extra": "ignore"}


class ErasureResponse(BaseModel):
    subject_id: str = Field(description="Unique identifier of the data subject whose data was erased")
    status: Literal["completed", "partial", "failed"] = Field(description="Outcome status of the erasure operation")
    records_deleted: int = Field(default=0, description="Total number of records deleted")
    categories_deleted: list[str] = Field(default_factory=list, description="Data categories that were successfully deleted")
    retained: list[dict[str, Any]] = Field(default_factory=list, description="Records retained with legal justification for each")
    completed_at: str = Field(description="ISO 8601 timestamp when erasure was completed")
    model_config = {"extra": "ignore"}


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
