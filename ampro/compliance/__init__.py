"""GDPR compliance, jurisdiction, and audit."""

from ampro.compliance.types import (
    ContentClassification, ComplianceJurisdictionInfo, RetentionPolicy,
    ErasureRequest, ErasureResponse, ExportRequest, ExportResponse,
)
from ampro.compliance.jurisdiction import (
    JurisdictionInfo, validate_jurisdiction_code, check_jurisdiction_conflict,
)
from ampro.compliance.middleware import (
    ComplianceCheckResult,
    check_content_classification, check_minor_protection, requires_audit,
)
from ampro.compliance.audit_logger import AuditLogger, AuditEntry
from ampro.compliance.erasure import ErasureProcessor
from ampro.compliance.erasure_propagation import (
    ErasurePropagationStatus, ErasurePropagationStatusBody,
)
from ampro.compliance.consent_revoke import DataConsentRevokeBody
from ampro.compliance.data_residency import (
    DataResidency, validate_residency_region, check_residency_violation,
)
from ampro.compliance.audit_attestation import AuditAttestationBody
from ampro.compliance.certifications import CertificationLink

__all__ = [
    # Types
    "ContentClassification", "ComplianceJurisdictionInfo", "RetentionPolicy",
    "ErasureRequest", "ErasureResponse", "ExportRequest", "ExportResponse",
    # Jurisdiction
    "JurisdictionInfo", "validate_jurisdiction_code", "check_jurisdiction_conflict",
    # Middleware
    "ComplianceCheckResult",
    "check_content_classification", "check_minor_protection", "requires_audit",
    # Audit
    "AuditLogger", "AuditEntry",
    # Erasure
    "ErasureProcessor",
    "ErasurePropagationStatus", "ErasurePropagationStatusBody",
    # Consent
    "DataConsentRevokeBody",
    # Data residency
    "DataResidency", "validate_residency_region", "check_residency_violation",
    # Attestation
    "AuditAttestationBody",
    # Certifications
    "CertificationLink",
]
