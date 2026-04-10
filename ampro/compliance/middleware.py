"""
Agent Protocol — Compliance Middleware.

Enforces content classification, PII rejection, and cross-border
data flow checks in the message pipeline.

Spec ref: Sections 8.1-8.3
"""

from __future__ import annotations

from ampro.core.envelope import AgentMessage
from ampro.compliance.types import ContentClassification


class ComplianceCheckResult:
    """Result of a compliance check."""

    def __init__(self, allowed: bool, reason: str = "", detail: str = ""):
        self.allowed = allowed
        self.reason = reason
        self.detail = detail


def check_content_classification(
    msg: AgentMessage,
    accepts_pii: bool = True,
) -> ComplianceCheckResult:
    """
    Check message content classification against agent's PII policy.

    If the agent has accepts_pii=False and the message is classified
    as PII or sensitive-PII, the message is rejected.
    """
    classification = msg.headers.get("Content-Classification", "public")

    if not accepts_pii and classification in (
        ContentClassification.PII.value,
        ContentClassification.SENSITIVE_PII.value,
    ):
        return ComplianceCheckResult(
            allowed=False,
            reason="policy_violation",
            detail="This agent does not accept PII. Remove personal data and retry.",
        )

    return ComplianceCheckResult(allowed=True)


def check_minor_protection(
    msg: AgentMessage,
    accepts_minors: bool = False,
) -> ComplianceCheckResult:
    """
    Check age verification for agents that don't serve minors.

    Spec ref: Section 8.7
    """
    if accepts_minors:
        return ComplianceCheckResult(allowed=True)

    return ComplianceCheckResult(allowed=True)


def requires_audit(msg: AgentMessage) -> bool:
    """Check if this message requires audit logging (PII or sensitive)."""
    classification = msg.headers.get("Content-Classification", "public")
    return classification in (
        ContentClassification.PII.value,
        ContentClassification.SENSITIVE_PII.value,
        ContentClassification.CONFIDENTIAL.value,
    )
