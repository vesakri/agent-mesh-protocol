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

from enum import Enum
from pydantic import BaseModel, Field


SCHEME = "agent"


class AddressType(str, Enum):
    HOST = "host"
    SLUG = "slug"
    DID = "did"


class AgentAddress(BaseModel):
    raw: str = Field(description="Original URI string")
    address_type: AddressType
    host: str | None = None
    slug: str | None = None
    registry: str | None = None
    did: str | None = None

    model_config = {"extra": "ignore"}

    def to_uri(self) -> str:
        if self.address_type == AddressType.DID:
            return f"agent://{self.did}"
        if self.address_type == AddressType.SLUG:
            return f"agent://{self.slug}@{self.registry}"
        return f"agent://{self.host}"

    def agent_json_url(self) -> str:
        if self.address_type != AddressType.HOST:
            raise ValueError(f"agent_json_url() requires HOST address, got {self.address_type}")
        return f"https://{self.host}/.well-known/agent.json"

    def registry_resolve_url(self) -> str:
        """Build the registry resolution URL for a SLUG address.

        WARNING: Callers MUST validate the returned URL against SSRF
        before fetching (e.g. via ``validate_attachment_url``).
        """
        if self.address_type != AddressType.SLUG:
            raise ValueError(f"registry_resolve_url() requires SLUG address, got {self.address_type}")
        return f"https://{self.registry}/agent/resolve/{self.slug}"


def parse_agent_uri(uri: str) -> AgentAddress:
    if not uri.startswith("agent://"):
        raise ValueError(f"Agent URI must start with agent://, got: {uri!r}")
    authority = uri[len("agent://"):]
    if not authority:
        raise ValueError("Agent URI has empty authority")
    if "did:" in authority:
        return AgentAddress(raw=uri, address_type=AddressType.DID, did=authority)
    if "@" in authority:
        slug, registry = authority.split("@", 1)
        if not slug or not registry:
            raise ValueError(f"Invalid slug@registry format: {authority!r}")
        return AgentAddress(raw=uri, address_type=AddressType.SLUG, slug=slug, registry=registry)
    return AgentAddress(raw=uri, address_type=AddressType.HOST, host=authority)


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
