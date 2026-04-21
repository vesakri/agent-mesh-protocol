"""
Agent Protocol — Binary Attachment Types.

Attachments are URL-referenced, not embedded. SHA-256 for integrity.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import unquote, urlparse

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
_PRIVATE_HOSTS = {"localhost", "localhost.localdomain", "[::1]", "::1"}

# Pattern to detect octal octets: leading zero followed by digit(s), e.g. "0177"
_OCTAL_OCTET_RE = re.compile(r"^0\d+$")


def _parse_octal_ip(hostname: str) -> ipaddress.IPv4Address | None:
    """Parse dotted-octal IP notation (e.g. 0177.0.0.1 → 127.0.0.1).

    Returns the resolved IPv4Address or None if not octal notation.
    """
    parts = hostname.split(".")
    if len(parts) != 4:
        return None
    # At least one octet must look octal (leading zero + digit)
    has_octal = any(_OCTAL_OCTET_RE.match(p) for p in parts)
    if not has_octal:
        return None
    try:
        decimal_parts = []
        for part in parts:
            if _OCTAL_OCTET_RE.match(part):
                decimal_parts.append(int(part, 8))
            else:
                decimal_parts.append(int(part))
        if any(p < 0 or p > 255 for p in decimal_parts):
            return None
        dotted = ".".join(str(p) for p in decimal_parts)
        return ipaddress.IPv4Address(dotted)
    except (ValueError, OverflowError):
        return None


def _parse_hex_dotted_ip(hostname: str) -> ipaddress.IPv4Address | None:
    """Parse dotted-hex IP notation (e.g. 0x7f.0x0.0x0.0x1 → 127.0.0.1).

    Returns the resolved IPv4Address or None if not hex-dotted notation.
    """
    parts = hostname.split(".")
    if len(parts) != 4:
        return None
    has_hex = any(p.lower().startswith("0x") for p in parts)
    if not has_hex:
        return None
    try:
        decimal_parts = []
        for part in parts:
            if part.lower().startswith("0x"):
                decimal_parts.append(int(part, 16))
            else:
                decimal_parts.append(int(part))
        if any(p < 0 or p > 255 for p in decimal_parts):
            return None
        dotted = ".".join(str(p) for p in decimal_parts)
        return ipaddress.IPv4Address(dotted)
    except (ValueError, OverflowError):
        return None


def _is_private_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address is private, loopback, link-local, or reserved."""
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
        return True
    # IPv6-mapped IPv4: extract the IPv4 part and check it
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        return _is_private_ip(addr.ipv4_mapped)
    return False


def validate_attachment_url(url: str) -> bool:
    """SSRF protection — returns True if URL is safe to fetch.

    Validates against:
    - Non-HTTPS schemes
    - Private/loopback/link-local IPs (dotted-decimal, octal, hex, integer)
    - IPv6 loopback and link-local (including zone IDs)
    - IPv6-mapped IPv4 addresses (::ffff:127.0.0.1)
    - Percent-encoded hostname bypasses (%2e etc.)
    - Localhost and known private hostnames
    """
    if not url.startswith("https://"):
        return False
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    # Decode percent-encoding to prevent bypasses like %2e for dots
    hostname = unquote(hostname)
    if not hostname:
        return False  # Reject URLs with no valid hostname
    # Lowercase for consistent comparison
    hostname = hostname.lower()
    # Strip IPv6 zone ID (e.g. "fe80::1%25eth0" or "fe80::1%eth0")
    # Zone IDs can be used to bypass IP checks
    clean_hostname = hostname.split("%")[0]
    # Check known private hostnames
    if clean_hostname in _PRIVATE_HOSTS:
        return False
    # Check known private IP prefixes (dotted-decimal)
    if any(clean_hostname.startswith(p) for p in _PRIVATE_PREFIXES):
        return False
    # Check 172.16-31.x.x range
    if clean_hostname.startswith("172."):
        try:
            second_octet = int(clean_hostname.split(".")[1])
            if 16 <= second_octet <= 31:
                return False
        except (IndexError, ValueError):
            pass
    # --- Alternative IP format checks ---
    # 1. Octal IP: 0177.0.0.1 → 127.0.0.1
    octal_addr = _parse_octal_ip(clean_hostname)
    if octal_addr is not None and _is_private_ip(octal_addr):
        return False
    # 2. Hex-dotted IP: 0x7f.0.0.1 → 127.0.0.1
    hex_dotted_addr = _parse_hex_dotted_ip(clean_hostname)
    if hex_dotted_addr is not None and _is_private_ip(hex_dotted_addr):
        return False
    # 3. Decimal integer IP: 2130706433 → 127.0.0.1
    try:
        if clean_hostname.isdigit():
            addr = ipaddress.ip_address(int(clean_hostname))
            if _is_private_ip(addr):
                return False
    except (ValueError, OverflowError):
        pass
    # 4. Hex integer IP: 0x7f000001 → 127.0.0.1
    try:
        if clean_hostname.startswith("0x") and "." not in clean_hostname:
            addr = ipaddress.ip_address(int(clean_hostname, 16))
            if _is_private_ip(addr):
                return False
    except (ValueError, OverflowError):
        pass
    # 5. Standard IP address check (IPv4/IPv6 including mapped addresses)
    try:
        addr = ipaddress.ip_address(clean_hostname)
        if _is_private_ip(addr):
            return False
    except ValueError:
        pass
    return True
