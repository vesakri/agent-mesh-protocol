"""Tests for ampro.core.addressing — agent:// URI parsing."""

from __future__ import annotations

import pytest

from ampro.core.addressing import (
    AddressType,
    AgentAddress,
    parse_agent_uri,
)


class TestIPv6:
    """Issue #18 — IPv6 literal in bracketed form agent://[...]"""

    def test_parse_ipv6_address(self):
        addr = parse_agent_uri("agent://[2001:db8::1]")
        assert addr.address_type == AddressType.HOST
        assert addr.host == "2001:db8::1"
        assert addr.port is None

    def test_parse_ipv6_loopback(self):
        addr = parse_agent_uri("agent://[::1]")
        assert addr.address_type == AddressType.HOST
        assert addr.host == "::1"

    def test_parse_ipv6_with_port(self):
        """Issue #19 — port with IPv6 literal."""
        addr = parse_agent_uri("agent://[2001:db8::1]:8443")
        assert addr.host == "2001:db8::1"
        assert addr.port == 8443

    def test_parse_ipv6_invalid_literal_rejected(self):
        with pytest.raises(ValueError):
            parse_agent_uri("agent://[not:an:ipv6:addr:xxx]")

    def test_parse_ipv6_missing_closing_bracket(self):
        with pytest.raises(ValueError):
            parse_agent_uri("agent://[2001:db8::1")


class TestHostWithPort:
    """Issue #19 — hostname with :port."""

    def test_parse_host_with_port(self):
        addr = parse_agent_uri("agent://bakery.example.com:8443")
        assert addr.address_type == AddressType.HOST
        assert addr.host == "bakery.example.com"
        assert addr.port == 8443

    def test_parse_host_without_port(self):
        addr = parse_agent_uri("agent://bakery.example.com")
        assert addr.host == "bakery.example.com"
        assert addr.port is None

    def test_port_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            parse_agent_uri("agent://bakery.example.com:70000")


class TestPercentEncoding:
    """Issue #20 — percent-encoded authority decoding with safety checks."""

    def test_percent_encoded_decoded_safely(self):
        # %61 → "a" — decoded before parsing.
        addr = parse_agent_uri("agent://b%61kery.example.com")
        assert addr.host == "bakery.example.com"

    def test_percent_encoded_null_byte_rejected(self):
        with pytest.raises(ValueError):
            parse_agent_uri("agent://bakery%00.example.com")

    def test_percent_encoded_newline_rejected(self):
        with pytest.raises(ValueError):
            parse_agent_uri("agent://bakery%0a.example.com")

    def test_raw_control_char_rejected(self):
        with pytest.raises(ValueError):
            parse_agent_uri("agent://bakery\x00.example.com")


class TestNFKCNormalization:
    """Issue #21 — NFKC + IDNA ACE-form conversion for Unicode hostnames."""

    def test_nfkc_normalization_applied(self):
        # Unicode hostname should normalize to ACE (punycode) form.
        addr = parse_agent_uri("agent://bücher.example.com")
        assert addr.host.startswith("xn--")  # ACE prefix
        assert "example.com" in addr.host

    def test_ascii_hostname_unchanged(self):
        addr = parse_agent_uri("agent://bakery.example.com")
        assert addr.host == "bakery.example.com"


class TestMultiAtSign:
    """Issue #22 — rsplit('@') + reject extra '@' in slug."""

    def test_multi_at_rejected(self):
        # Two '@' signs in slug — must be rejected.
        with pytest.raises(ValueError) as exc:
            parse_agent_uri("agent://foo@bar@registry.example.com")
        assert "multiple '@'" in str(exc.value)

    def test_slug_at_registry_still_works(self):
        addr = parse_agent_uri("agent://sales@acme.example.com")
        assert addr.address_type == AddressType.SLUG
        assert addr.slug == "sales"
        assert addr.registry == "acme.example.com"


class TestRegistryResolveUrlSSRF:
    """Issue #23 — registry_resolve_url() blocks SSRF via validate_attachment_url."""

    def test_registry_resolve_url_blocks_ssrf(self):
        # Registry points at localhost → must be rejected.
        addr = AgentAddress(
            raw="agent://sales@localhost",
            address_type=AddressType.SLUG,
            slug="sales",
            registry="localhost",
        )
        with pytest.raises(ValueError) as exc:
            addr.registry_resolve_url()
        assert "SSRF" in str(exc.value)

    def test_registry_resolve_url_allows_public_registry(self):
        addr = AgentAddress(
            raw="agent://sales@registry.example.com",
            address_type=AddressType.SLUG,
            slug="sales",
            registry="registry.example.com",
        )
        url = addr.registry_resolve_url()
        assert url == "https://registry.example.com/agent/resolve/sales"
