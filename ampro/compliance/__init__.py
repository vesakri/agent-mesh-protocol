"""GDPR compliance, jurisdiction, and audit."""

from ampro.compliance.types import (
    ContentClassification, ComplianceJurisdictionInfo, RetentionPolicy,
    ErasureRequest, ErasureResponse, ExportRequest, ExportResponse,
    RetainedRecord,
)
from ampro.compliance.jurisdiction import (
    JurisdictionInfo, validate_jurisdiction_code, check_jurisdiction_conflict,
    validate_jurisdiction_source,
    TransferMechanism, AdequacyDecision, TransferDecision,
    AdequacyRegistry, NoOpAdequacyRegistry,
    register_adequacy_registry, get_adequacy_registry,
    check_cross_border_transfer, applicable_rules,
)
from ampro.compliance.middleware import (
    ComplianceCheckResult,
    check_content_classification, check_minor_protection, requires_audit,
)
from ampro.compliance.audit_logger import AuditLogger, AuditEntry, AuditStorage, InMemoryAuditStorage
from ampro.compliance.erasure import ErasureProcessor
from ampro.compliance.erasure_propagation import (
    ErasurePropagationStatus, ErasurePropagationStatusBody,
    compute_next_retry,
    MAX_ERASURE_RETRIES, DEFAULT_RETRY_BASE_DELAY_SEC, MAX_RETRY_DELAY_SEC,
)
from ampro.compliance.consent_revoke import DataConsentRevokeBody
from ampro.compliance.data_residency import (
    DataResidency, validate_residency_region, check_residency_violation,
)
from ampro.compliance.audit_attestation import AuditAttestationBody, verify_attestation
from ampro.compliance.certifications import CertificationLink

__all__ = [
    # Types
    "ContentClassification", "ComplianceJurisdictionInfo", "RetentionPolicy",
    "ErasureRequest", "ErasureResponse", "ExportRequest", "ExportResponse",
    "RetainedRecord",
    # Jurisdiction
    "JurisdictionInfo", "validate_jurisdiction_code", "check_jurisdiction_conflict",
    "validate_jurisdiction_source",
    "TransferMechanism", "AdequacyDecision", "TransferDecision",
    "AdequacyRegistry", "NoOpAdequacyRegistry",
    "register_adequacy_registry", "get_adequacy_registry",
    "check_cross_border_transfer", "applicable_rules",
    # Middleware
    "ComplianceCheckResult",
    "check_content_classification", "check_minor_protection", "requires_audit",
    # Audit
    "AuditLogger", "AuditEntry", "AuditStorage", "InMemoryAuditStorage",
    # Erasure
    "ErasureProcessor",
    "ErasurePropagationStatus", "ErasurePropagationStatusBody",
    "compute_next_retry",
    "MAX_ERASURE_RETRIES", "DEFAULT_RETRY_BASE_DELAY_SEC", "MAX_RETRY_DELAY_SEC",
    # Consent
    "DataConsentRevokeBody",
    # Data residency
    "DataResidency", "validate_residency_region", "check_residency_violation",
    # Attestation
    "AuditAttestationBody", "verify_attestation",
    # Certifications
    "CertificationLink",
]
