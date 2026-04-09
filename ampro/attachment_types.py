"""
Agent Protocol — Binary Attachment Types.

Attachments are URL-referenced, not embedded. SHA-256 for integrity.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class Attachment(BaseModel):
    """A binary attachment referenced by URL."""

    name: str = Field(description="Filename")
    url: str = Field(description="HTTPS download URL")
    content_type: str = Field(description="MIME type")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    sha256: str = Field(description="SHA-256 hash for integrity")

    model_config = {"extra": "ignore"}

    @field_validator("url")
    @classmethod
    def url_must_be_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("Attachment URL must be HTTPS")
        return v


_PRIVATE_PREFIXES = ("127.", "10.", "192.168.", "169.254.", "0.")
_PRIVATE_HOSTS = {"localhost", "localhost.localdomain", "[::1]"}


def validate_attachment_url(url: str) -> bool:
    """SSRF protection — returns True if URL is safe to fetch."""
    if not url.startswith("https://"):
        return False
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if hostname in _PRIVATE_HOSTS:
        return False
    if any(hostname.startswith(p) for p in _PRIVATE_PREFIXES):
        return False
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return False
    except ValueError:
        pass
    if hostname.startswith("172."):
        try:
            second_octet = int(hostname.split(".")[1])
            if 16 <= second_octet <= 31:
                return False
        except (IndexError, ValueError):
            pass
    return True
