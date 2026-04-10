"""
Agent Protocol — Context Schema URN Parsing and Matching.

Domain-agnostic schema declaration via URN identifiers. Agents advertise
which context schemas they understand (e.g. purchase orders, invoices,
shipping manifests) using URNs of the form:

    urn:<namespace>:<name>:<version>

Examples:
    urn:schema:purchase-order:v1
    urn:schema:com.example.invoice:v2
    urn:domain:shipping-manifest:v1

This module is PURE — only pydantic from external, no platform-specific imports.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextSchemaInfo(BaseModel):
    """Parsed representation of a context schema URN."""

    urn: str = Field(description="Full URN string, e.g. 'urn:schema:purchase-order:v1'")
    namespace: str = Field(description="Namespace segment, e.g. 'schema'")
    name: str = Field(description="Schema name, e.g. 'purchase-order'")
    version: str = Field(description="Version segment, e.g. 'v1'")

    model_config = {"extra": "ignore"}


def parse_schema_urn(urn: str) -> ContextSchemaInfo:
    """Parse a URN like ``urn:schema:purchase-order:v1`` into its parts.

    Format::

        urn:<namespace>:<name>:<version>

    The *name* may contain dots for reverse-domain notation
    (e.g. ``com.example.purchase-order``).  The parser splits on exactly
    four colon-separated segments: ``urn``, namespace, name, and version.

    Raises:
        ValueError: If *urn* is empty, does not start with ``urn:``, or
            does not contain exactly four colon-separated parts.
    """
    if not urn or not isinstance(urn, str):
        raise ValueError("URN must be a non-empty string")

    parts = urn.split(":")
    if len(parts) != 4:
        raise ValueError(
            f"URN must have exactly 4 colon-separated parts (urn:<namespace>:<name>:<version>), "
            f"got {len(parts)}: {urn!r}"
        )

    prefix, namespace, name, version = parts

    if prefix.lower() != "urn":
        raise ValueError(f"URN must start with 'urn:', got {prefix!r}")

    if not namespace:
        raise ValueError("Namespace segment must not be empty")

    if not name:
        raise ValueError("Name segment must not be empty")

    if not version:
        raise ValueError("Version segment must not be empty")

    return ContextSchemaInfo(
        urn=urn,
        namespace=namespace,
        name=name,
        version=version,
    )


def check_schema_supported(urn: str | None, supported_schemas: list[str]) -> bool:
    """Check whether *urn* is present in *supported_schemas*.

    Comparison is case-insensitive.

    Returns ``False`` when:
    - *urn* is ``None`` or empty
    - *supported_schemas* is empty
    """
    if not urn:
        return False

    if not supported_schemas:
        return False

    urn_lower = urn.lower()
    return any(s.lower() == urn_lower for s in supported_schemas)
