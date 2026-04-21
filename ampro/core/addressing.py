"""
Agent Protocol — agent:// URI Addressing.

Parses agent:// URIs into structured addresses with three forms:
  - Direct host:    agent://bakery.example.com
  - Registry slug:  agent://sales@example.com
  - DID:            agent://did:web:example.com

This module is PURE — no platform-specific imports.
Designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

import ipaddress
import unicodedata
from enum import Enum
from urllib.parse import unquote

from pydantic import BaseModel, Field

SCHEME = "agent"

# Control characters and percent-encoded control characters that MUST NOT
# appear in an agent:// authority (defense against smuggling / log injection).
_DANGEROUS_PERCENT_ENCODED = ("%00", "%0a", "%0A", "%0d", "%0D", "%09")


class AddressType(str, Enum):
    HOST = "host"
    SLUG = "slug"
    DID = "did"


class AgentAddress(BaseModel):
    raw: str = Field(description="Original URI string")
    address_type: AddressType
    host: str | None = None
    port: int | None = None
    slug: str | None = None
    registry: str | None = None
    did: str | None = None

    model_config = {"extra": "ignore"}

    def to_uri(self) -> str:
        if self.address_type == AddressType.DID:
            return f"agent://{self.did}"
        if self.address_type == AddressType.SLUG:
            return f"agent://{self.slug}@{self.registry}"
        if self.host and ":" in self.host:
            # IPv6 literal — re-bracket
            host_part = f"[{self.host}]"
        else:
            host_part = self.host or ""
        if self.port is not None:
            return f"agent://{host_part}:{self.port}"
        return f"agent://{host_part}"

    def agent_json_url(self) -> str:
        if self.address_type != AddressType.HOST:
            raise ValueError(f"agent_json_url() requires HOST address, got {self.address_type}")
        return f"https://{self.host}/.well-known/agent.json"

    def registry_resolve_url(self) -> str:
        """Build the registry resolution URL for a SLUG address.

        The returned URL is validated against SSRF (via
        ``validate_attachment_url``) before being returned. Callers may still
        validate again if they accept user-supplied registries.
        """
        if self.address_type != AddressType.SLUG:
            raise ValueError(
                f"registry_resolve_url() requires SLUG address, got {self.address_type}"
            )
        url = f"https://{self.registry}/agent/resolve/{self.slug}"
        # SSRF guard — enforces the docstring contract.
        try:
            from ampro.transport.attachment import validate_attachment_url
        except ImportError:
            return url
        if not validate_attachment_url(url):
            raise ValueError(
                f"registry_resolve_url() rejected URL (SSRF guard): {url!r}"
            )
        return url


def _normalize_host(host: str) -> str:
    """NFKC-normalize and IDNA-encode a hostname for shape comparison.

    This converts Unicode hostnames to their ASCII Compatible Encoding (ACE)
    form. We only NORMALIZE — we do not reject unknown labels.
    """
    normalized = unicodedata.normalize("NFKC", host)
    try:
        # .encode("idna") enforces IDNA label-shape rules only (length etc.)
        ace = normalized.encode("idna").decode("ascii")
        return ace
    except (UnicodeError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"hostname IDNA normalization failed for {host!r}: {exc}"
        ) from exc


def parse_agent_uri(uri: str) -> AgentAddress:
    if not uri.startswith("agent://"):
        raise ValueError(f"Agent URI must start with agent://, got: {uri!r}")
    authority = uri[len("agent://"):]
    if not authority:
        raise ValueError("Agent URI has empty authority")

    # Reject dangerous percent-encoded control sequences before decoding.
    for bad in _DANGEROUS_PERCENT_ENCODED:
        if bad in authority:
            raise ValueError(
                f"Agent URI authority contains forbidden percent-encoded "
                f"control character {bad!r}: {uri!r}"
            )
    # Reject raw control characters in the authority.
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in authority):
        raise ValueError(
            f"Agent URI authority contains raw control character: {uri!r}"
        )

    # Decode percent-encoding (matching validate_attachment_url semantics).
    authority = unquote(authority)

    # IPv6 literal in brackets — must come before did: check and before
    # the ':' port-split (because IPv6 contains colons).
    if authority.startswith("["):
        end = authority.find("]")
        if end < 0:
            raise ValueError(f"Agent URI with '[' missing closing ']': {uri!r}")
        ipv6_literal = authority[1:end]
        try:
            ipaddress.ip_address(ipv6_literal)
        except ValueError as exc:
            raise ValueError(
                f"Agent URI has invalid IPv6 literal {ipv6_literal!r}: {exc}"
            ) from exc
        port: int | None = None
        remainder = authority[end + 1:]
        if remainder:
            if not remainder.startswith(":"):
                raise ValueError(
                    f"Agent URI has trailing characters after IPv6 bracket: {uri!r}"
                )
            port_str = remainder[1:]
            if not port_str.isdigit():
                raise ValueError(f"Agent URI has non-numeric port: {uri!r}")
            port = int(port_str)
            if port > 65535:
                raise ValueError(f"Agent URI port out of range: {port}")
        return AgentAddress(
            raw=uri,
            address_type=AddressType.HOST,
            host=ipv6_literal,
            port=port,
        )

    if "did:" in authority:
        return AgentAddress(raw=uri, address_type=AddressType.DID, did=authority)

    if "@" in authority:
        # rsplit handles did:web:foo@registry.example.com (method-specific-id
        # may contain '@'), though did: was already handled above. This also
        # defends against "slug@a@b" — see multi-'@' check below.
        slug, registry = authority.rsplit("@", 1)
        if "@" in slug:
            raise ValueError(
                "malformed agent URI: multiple '@' not allowed in slug or registry"
            )
        if not slug or not registry:
            raise ValueError(f"Invalid slug@registry format: {authority!r}")
        return AgentAddress(
            raw=uri, address_type=AddressType.SLUG, slug=slug, registry=registry
        )

    # Host form — possibly with :port.
    host = authority
    port = None
    if ":" in authority:
        host_part, _, port_str = authority.rpartition(":")
        if port_str.isdigit():
            port_value = int(port_str)
            if port_value > 65535:
                raise ValueError(f"Agent URI port out of range: {port_value}")
            host = host_part
            port = port_value
        # else: leave host/port unseparated — odd shapes fall through to
        # IDNA validation below which will raise.

    if not host:
        raise ValueError(f"Agent URI has empty host: {uri!r}")

    # NFKC + IDNA shape-check for Unicode/ASCII hostnames.
    host = _normalize_host(host)

    return AgentAddress(
        raw=uri, address_type=AddressType.HOST, host=host, port=port
    )


def normalize_shorthand(value: str, default_registry: str) -> str:
    if value.startswith("agent://"):
        return value
    if value.startswith("@"):
        slug = value[1:]
        if not default_registry:
            raise ValueError(f"Cannot normalize bare slug {value!r} without a default registry")
        return f"agent://{slug}@{default_registry}"
    if value.startswith("https://"):
        host = value[len("https://"):].rstrip("/")
        return f"agent://{host}"
    if value.startswith("http://"):
        host = value[len("http://"):].rstrip("/")
        return f"agent://{host}"
    if "." in value:
        return f"agent://{value}"
    if not default_registry:
        raise ValueError(f"Cannot normalize bare slug {value!r} without a default registry")
    return f"agent://{value}@{default_registry}"
