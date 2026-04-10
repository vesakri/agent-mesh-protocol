"""
Agent Protocol — Compliance Certifications.

Agents declare compliance certifications in agent.json. These are
links to external attestations (SOC2, ISO27001, etc.), not
protocol-level enforcement.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CertificationLink(BaseModel):
    """A link to an external compliance certification."""

    standard: str = Field(description="Certification standard (e.g. SOC2, ISO27001)")
    url: str = Field(description="URL to the certification document")
    verified_by: str = Field(description="agent:// URI of the verifying authority")
    expires_at: str = Field(description="ISO-8601 expiration timestamp")

    model_config = {"extra": "ignore"}
