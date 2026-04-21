"""
Agent Protocol — Data Residency.

Declares where data must reside. Agents declare residency requirements
via the Data-Residency header. Tasks that would violate residency
constraints are rejected with reason 'residency_violation'.

PURE — zero platform-specific imports. Only pydantic, re, and stdlib.
"""

# ─── Reference implementation, not production-wired ────────────────
# This module is part of the AMP protocol surface and is validated by
# the test suite against the normative spec at
# `docs/WIRE-BINDING.md`. It has no first-party runtime caller as of
# ampro v0.3.0; downstream implementers may depend on it directly, or
# provide their own implementation conforming to the same contract.
# ───────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_REGION_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,28}[a-z0-9]")

# Known cloud-provider region codes. Advisory: unknown regions still pass
# shape validation (for forward-compat with new regions), but a WARNING is
# logged so operators can catch typos.
#
# Sources (abbreviated):
#   - AWS:   https://docs.aws.amazon.com/general/latest/gr/rande.html
#   - GCP:   https://cloud.google.com/compute/docs/regions-zones
#   - Azure: https://azure.microsoft.com/en-us/global-infrastructure/geographies/
KNOWN_REGIONS: frozenset[str] = frozenset({
    # AWS
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ca-central-1", "ca-west-1",
    "eu-west-1", "eu-west-2", "eu-west-3",
    "eu-central-1", "eu-central-2",
    "eu-north-1", "eu-south-1", "eu-south-2",
    "ap-south-1", "ap-south-2",
    "ap-southeast-1", "ap-southeast-2", "ap-southeast-3",
    "ap-southeast-4", "ap-southeast-5",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "ap-east-1",
    "sa-east-1",
    "me-south-1", "me-central-1",
    "af-south-1",
    "il-central-1",
    # GCP
    "us-central1", "us-east1", "us-east4", "us-east5",
    "us-south1", "us-west1", "us-west2", "us-west3", "us-west4",
    "northamerica-northeast1", "northamerica-northeast2",
    "southamerica-east1", "southamerica-west1",
    "europe-central2", "europe-north1", "europe-southwest1",
    "europe-west1", "europe-west2", "europe-west3", "europe-west4",
    "europe-west6", "europe-west8", "europe-west9", "europe-west12",
    "asia-east1", "asia-east2",
    "asia-northeast1", "asia-northeast2", "asia-northeast3",
    "asia-south1", "asia-south2",
    "asia-southeast1", "asia-southeast2",
    "australia-southeast1", "australia-southeast2",
    "me-west1",
    # Azure
    "eastus", "eastus2", "westus", "westus2", "westus3",
    "centralus", "northcentralus", "southcentralus", "westcentralus",
    "northeurope", "westeurope",
    "uksouth", "ukwest",
    "francecentral", "francesouth",
    "germanywestcentral", "germanynorth",
    "switzerlandnorth", "switzerlandwest",
    "swedencentral",
    "norwayeast", "norwaywest",
    "eastasia", "southeastasia",
    "japaneast", "japanwest",
    "koreacentral", "koreasouth",
    "southindia", "centralindia", "westindia",
    "canadacentral", "canadaeast",
    "brazilsouth", "brazilsoutheast",
    "australiaeast", "australiacentral", "australiasoutheast",
    "uaenorth", "uaecentral",
    "qatarcentral",
    "southafricanorth", "southafricawest",
})


class DataResidency(BaseModel):
    """Residency constraint attached to a message or agent.

    Distinguishes data **at rest** (``storage_regions``) from data
    **in flight** (``transit_regions``).  Both MUST be validated
    against the message's allowed set.

    Backwards compatibility: the original ``region`` + ``allowed_regions``
    fields are preserved and continue to work as "storage" shorthand.
    They are soft-deprecated in favour of the explicit
    ``storage_regions`` / ``transit_regions`` fields.
    """

    region: str = Field(
        description=(
            "DEPRECATED (use storage_regions). Data residency region "
            "identifier (e.g. eu-west-1, us-east-1)."
        ),
    )
    strict: bool = Field(
        default=True,
        description="When True, data MUST NOT leave the region",
    )
    allowed_regions: list[str] = Field(
        default_factory=list,
        description="Additional regions where data may be stored (when strict=False)",
    )
    storage_regions: list[str] = Field(
        default_factory=list,
        description="Where data is stored at rest (v0.3.x+).",
    )
    transit_regions: list[str] = Field(
        default_factory=list,
        description="Regions data traverses in flight (v0.3.x+).",
    )

    model_config = {"extra": "ignore"}


def validate_residency_region(region: str) -> bool:
    """Return *True* if *region* is a valid residency region identifier.

    Format: lowercase alphanumeric + hyphens, 3-30 characters,
    must start and end with an alphanumeric character.

    Regions not in :data:`KNOWN_REGIONS` still pass shape validation (for
    forward-compat with new provider regions), but a WARNING is logged so
    operators can catch typos in configuration.
    """
    if _REGION_RE.fullmatch(region) is None:
        return False
    if region not in KNOWN_REGIONS:
        logger.warning(
            "[data-residency] region %r passed shape check but is not in "
            "KNOWN_REGIONS; accepting for forward-compat — verify spelling.",
            region,
        )
    return True


def _allowed_set(message_residency: DataResidency) -> set[str]:
    """Return the set of regions allowed by *message_residency*."""
    allowed = {message_residency.region}
    if not message_residency.strict:
        allowed.update(message_residency.allowed_regions)
    return allowed


def check_residency_violation(
    message_residency: DataResidency,
    agent_residency: DataResidency,
) -> tuple[bool, str | None]:
    """Check whether an agent may handle a message given residency constraints.

    Validates both storage (at rest) and transit (in flight) regions
    against the message's allowed set.  Returns ``(has_violation, detail)``.
    When *has_violation* is ``False``, *detail* is ``None``.
    """
    allowed = _allowed_set(message_residency)

    # Collect agent storage regions (explicit + legacy fallback).
    storage_regions = (
        set(agent_residency.storage_regions)
        if agent_residency.storage_regions
        else {agent_residency.region}
    )

    for region in storage_regions:
        if region not in allowed:
            if message_residency.strict:
                return True, (
                    f"strict residency: message requires "
                    f"'{message_residency.region}' but agent stores in "
                    f"'{region}'"
                )
            return True, (
                f"residency violation: agent storage region '{region}' "
                f"is not in allowed_regions "
                f"{sorted(allowed - {message_residency.region})} "
                f"for message region '{message_residency.region}'"
            )

    # Validate transit regions (only present on the explicit field).
    for region in agent_residency.transit_regions:
        if region not in allowed:
            return True, (
                f"residency violation: transit region '{region}' "
                f"is not in allowed set {sorted(allowed)} "
                f"for message region '{message_residency.region}'"
            )

    return False, None
