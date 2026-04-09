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


class JurisdictionInfo(BaseModel):
    jurisdiction: str = Field(description="Primary jurisdiction (ISO 3166-1 alpha-2)")
    additional_jurisdictions: list[str] = Field(default_factory=list)
    data_processing_agreement_url: str | None = None
    privacy_policy_url: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    data_residency: str | None = None
    accepts_pii: bool = True
    accepts_minors: bool = False
    model_config = {"extra": "ignore"}


class RetentionPolicy(BaseModel):
    messages: str = Field(default="30d")
    task_history: str = Field(default="90d")
    tool_logs: str = Field(default="90d")
    audit_logs: str = Field(default="365d")
    sessions: str = Field(default="7d")
    model_config = {"extra": "ignore"}


class ErasureRequest(BaseModel):
    subject_id: str
    subject_proof: str
    scope: Literal["all", "conversations", "tasks", "tools"]
    reason: Literal["user_request", "account_deletion", "consent_withdrawn", "legal_order"]
    deadline: str = Field(description="ISO 8601 deadline for completion")
    callback_url: str | None = None
    model_config = {"extra": "ignore"}


class ErasureResponse(BaseModel):
    subject_id: str
    status: Literal["completed", "partial", "failed"]
    records_deleted: int = 0
    categories_deleted: list[str] = Field(default_factory=list)
    retained: list[dict[str, Any]] = Field(default_factory=list)
    completed_at: str = Field(description="ISO 8601 timestamp")
    model_config = {"extra": "ignore"}


class ExportRequest(BaseModel):
    subject_id: str
    subject_proof: str
    scope: Literal["all", "conversations", "tasks", "tools"] = "all"
    format: Literal["json", "csv"] = "json"
    callback_url: str | None = None
    model_config = {"extra": "ignore"}


class ExportResponse(BaseModel):
    subject_id: str
    status: Literal["completed", "partial", "failed"]
    export_url: str | None = None
    size_bytes: int | None = None
    expires_at: str | None = None
    categories_exported: list[str] = Field(default_factory=list)
    model_config = {"extra": "ignore"}
