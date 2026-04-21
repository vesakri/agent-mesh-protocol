"""GDPR compliance, jurisdiction, and audit."""

from ampro.compliance.audit_attestation import AuditAttestationBody, verify_attestation
from ampro.compliance.audit_logger import (
    AuditEntry,
    AuditLogger,
    AuditStorage,
    InMemoryAuditStorage,
)
from ampro.compliance.certifications import CertificationLink
from ampro.compliance.consent_revoke import DataConsentRevokeBody
from ampro.compliance.data_residency import (
    DataResidency,
    check_residency_violation,
    validate_residency_region,
)
from ampro.compliance.erasure import ErasureProcessor
from ampro.compliance.erasure_propagation import (
    DEFAULT_RETRY_BASE_DELAY_SEC,
    MAX_ERASURE_RETRIES,
    MAX_RETRY_DELAY_SEC,
    ErasurePropagationStatus,
    ErasurePropagationStatusBody,
    compute_next_retry,
)
from ampro.compliance.jurisdiction import (
    AdequacyDecision,
    AdequacyRegistry,
    JurisdictionInfo,
    NoOpAdequacyRegistry,
    TransferDecision,
    TransferMechanism,
    applicable_rules,
    check_cross_border_transfer,
    check_jurisdiction_conflict,
    get_adequacy_registry,
    register_adequacy_registry,
    validate_jurisdiction_code,
    validate_jurisdiction_source,
)
from ampro.compliance.middleware import (
    ComplianceCheckResult,
    check_content_classification,
    check_minor_protection,
    requires_audit,
)
from ampro.compliance.types import (
    ComplianceJurisdictionInfo,
    ContentClassification,
    ErasureRequest,
    ErasureResponse,
    ExportRequest,
    ExportResponse,
    RetainedRecord,
    RetentionPolicy,
)

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
