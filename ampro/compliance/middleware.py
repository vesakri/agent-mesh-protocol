"""
Agent Protocol — Compliance Middleware.

Enforces content classification, PII rejection, and cross-border
data flow checks in the message pipeline.

Spec ref: Sections 8.1-8.3
"""

from __future__ import annotations

import logging

from ampro.core.envelope import AgentMessage
from ampro.compliance.types import ContentClassification

logger = logging.getLogger(__name__)


class ComplianceCheckResult:
    """Result of a compliance check."""

    def __init__(
        self,
        allowed: bool,
        reason: str = "",
        detail: str = "",
        overridden: bool = False,
        classification: str = "public",
    ):
        self.allowed = allowed
        self.reason = reason
        self.detail = detail
        self.overridden = overridden
        self.classification = classification


def check_content_classification(
    msg: AgentMessage,
    accepts_pii: bool = True,
) -> ComplianceCheckResult:
    """
    Check message content classification with server-side PII detection.

    1. Read sender's Content-Classification header (default ``public``).
    2. Run ``detect_pii(msg.body)`` to scan for PII / secrets.
    3. If no detections -> return sender's claim unchanged.
    4. If detections -> compute the highest-tier detection.
    5. If detected tier > sender's tier -> override, log warning with
       paths (NOT values), return overridden classification.
    6. Otherwise -> return sender's claim (sender already strict enough).

    After classification is resolved, enforce ``accepts_pii`` policy.
    """
    from ampro.compliance.pii_patterns import (
        _CATEGORY_TO_TIER,
        detect_pii,
        tier_rank,
    )

    sender_classification = msg.headers.get("Content-Classification", "public")
    effective_classification = sender_classification
    overridden = False

    # Server-side PII detection
    detections = detect_pii(msg.body)
    if detections:
        # Compute the highest tier among all detections
        highest_tier = sender_classification
        for det in detections:
            det_tier = _CATEGORY_TO_TIER.get(det.category, "pii")
            if tier_rank(det_tier) > tier_rank(highest_tier):
                highest_tier = det_tier

        if tier_rank(highest_tier) > tier_rank(sender_classification):
            overridden = True
            effective_classification = highest_tier
            # Log paths only — NEVER log matched values
            paths = [det.path for det in detections]
            logger.warning(
                "Content classification overridden: sender claimed %r, "
                "detected %r at paths %s",
                sender_classification,
                highest_tier,
                paths,
            )

    # Enforce accepts_pii policy against the effective classification
    if not accepts_pii and effective_classification in (
        ContentClassification.PII.value,
        ContentClassification.SENSITIVE_PII.value,
        ContentClassification.CONFIDENTIAL.value,
    ):
        return ComplianceCheckResult(
            allowed=False,
            reason="policy_violation",
            detail="This agent does not accept PII. Remove personal data and retry.",
            overridden=overridden,
            classification=effective_classification,
        )

    return ComplianceCheckResult(
        allowed=True,
        overridden=overridden,
        classification=effective_classification,
    )


def check_minor_protection(
    msg: AgentMessage,
) -> ComplianceCheckResult:
    """
    Check whether a message involves a minor and enforce guardian rules.

    Logic:
      1. Extract subject from msg.body["subject_id"] or msg.headers["Subject-Id"].
      2. If no subject → allowed (nothing to protect).
      3. If subject is not a minor (registry) → allowed.
      4. If subject IS a minor:
         a. Guardian exists AND sender == guardian → allowed.
         b. Otherwise → blocked (reason="minor_protection").

    The default NoOpMinorRegistry returns is_minor=False for everyone,
    so this function is effectively a no-op until a platform registers a
    real registry (AM-2).

    Spec ref: Section 8.7
    """
    from ampro.compliance.registry import get_minor_registry

    registry = get_minor_registry()

    # Extract subject_id from body (dict) or headers
    subject_id: str | None = None
    if isinstance(msg.body, dict):
        subject_id = msg.body.get("subject_id")
    if subject_id is None:
        subject_id = msg.headers.get("Subject-Id")

    # No subject identified → nothing to protect
    if not subject_id:
        return ComplianceCheckResult(allowed=True)

    # Subject is not a minor → allowed
    if not registry.is_minor(subject_id):
        return ComplianceCheckResult(allowed=True)

    # Subject IS a minor — check guardian authorization
    guardian = registry.guardian_of(subject_id)
    if guardian and msg.sender == guardian:
        return ComplianceCheckResult(allowed=True)

    # Minor with no guardian, or sender is not the guardian → blocked
    return ComplianceCheckResult(
        allowed=False,
        reason="minor_protection",
        detail=f"Subject '{subject_id}' is a minor. Only an authorized guardian may send messages involving this subject.",
    )


def requires_audit(msg: AgentMessage) -> bool:
    """Check if this message requires audit logging (PII or sensitive)."""
    classification = msg.headers.get("Content-Classification", "public")
    return classification in (
        ContentClassification.PII.value,
        ContentClassification.SENSITIVE_PII.value,
        ContentClassification.CONFIDENTIAL.value,
    )
