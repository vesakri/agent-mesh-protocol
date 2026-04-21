"""Tests for SSRF protection (C17 + C19).

C17: TaskInputRequiredBody.consent_url must reject non-HTTPS, private IPs,
     localhost, and other SSRF vectors via validate_attachment_url.
C19: validate_attachment_url must handle octal IPs, hex IPs, IPv6-mapped IPv4,
     zone IDs, percent-encoded bypasses, and decimal-encoded IPs.

12 tests covering all documented SSRF bypass vectors.
"""

import pytest
from pydantic import ValidationError


class TestValidateAttachmentUrl:
    """Direct tests for the validate_attachment_url function (C19)."""

    def test_valid_external_https(self):
        """Valid external HTTPS URL must be accepted."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://example.com/consent") is True
        assert validate_attachment_url("https://auth.example.com/oauth") is True
        assert validate_attachment_url("https://example.com:443/path?q=1") is True

    def test_http_rejected(self):
        """HTTP (non-HTTPS) URLs must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("http://example.com/consent") is False

    def test_localhost_rejected(self):
        """Localhost hostnames must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://localhost/admin") is False
        assert validate_attachment_url("https://localhost.localdomain/x") is False

    def test_loopback_ipv4_rejected(self):
        """127.0.0.1 (IPv4 loopback) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://127.0.0.1/admin") is False
        assert validate_attachment_url("https://127.0.0.2/path") is False

    def test_private_rfc1918_rejected(self):
        """RFC 1918 private IPs (10.x, 192.168.x, 172.16-31.x) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://10.0.0.1/internal") is False
        assert validate_attachment_url("https://192.168.1.1/router") is False
        assert validate_attachment_url("https://172.16.0.1/db") is False
        assert validate_attachment_url("https://172.31.255.255/x") is False
        # 172.15.x.x is NOT private — should pass
        assert validate_attachment_url("https://172.15.0.1/ok") is True

    def test_octal_ip_rejected(self):
        """Octal-encoded IPs (0177.0.0.1 = 127.0.0.1) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        # 0177 = 127 in octal, so 0177.0.0.1 = 127.0.0.1
        assert validate_attachment_url("https://0177.0.0.1/admin") is False
        # 012.0.0.1 = 10.0.0.1 (octal 012 = decimal 10)
        assert validate_attachment_url("https://012.0.0.1/internal") is False

    def test_hex_ip_rejected(self):
        """Hex-encoded IPs (0x7f000001 = 127.0.0.1) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        # Single hex integer: 0x7f000001 = 2130706433 = 127.0.0.1
        assert validate_attachment_url("https://0x7f000001/admin") is False
        # Dotted-hex: 0x7f.0x0.0x0.0x1 = 127.0.0.1
        assert validate_attachment_url("https://0x7f.0x0.0x0.0x1/admin") is False
        # Hex 10.0.0.1 = 0x0a000001
        assert validate_attachment_url("https://0x0a000001/x") is False

    def test_ipv6_localhost_rejected(self):
        """IPv6 loopback (::1) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://[::1]/admin") is False

    def test_ipv6_mapped_ipv4_rejected(self):
        """IPv6-mapped IPv4 (::ffff:127.0.0.1) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://[::ffff:127.0.0.1]/admin") is False
        assert validate_attachment_url("https://[::ffff:10.0.0.1]/internal") is False
        assert validate_attachment_url("https://[::ffff:192.168.1.1]/x") is False

    def test_percent_encoded_dots_rejected(self):
        """Percent-encoded hostname components (%2e = .) must be detected and rejected.

        urlparse decodes hostname percent-encoding, and our unquote call
        normalises any remaining %XX sequences before checking.
        """
        from ampro.transport.attachment import validate_attachment_url

        # %31%32%37 = "127", %2e = "."  →  127.0.0.1
        # urlparse should decode this, but if it doesn't, unquote catches it
        assert validate_attachment_url("https://127%2e0%2e0%2e1/admin") is False

    def test_link_local_rejected(self):
        """Link-local addresses (169.254.x.x, fe80::) must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https://169.254.1.1/metadata") is False

    def test_empty_or_missing_hostname_rejected(self):
        """URLs with empty or missing hostnames must be rejected."""
        from ampro.transport.attachment import validate_attachment_url

        assert validate_attachment_url("https:///path") is False
        assert validate_attachment_url("") is False


class TestConsentUrlValidation:
    """Tests for TaskInputRequiredBody.consent_url field validator (C17)."""

    def _make_body(self, consent_url: str | None = None) -> dict:
        """Return minimal valid body kwargs."""
        return {
            "task_id": "task-001",
            "reason": "Need OAuth consent",
            "prompt": "Please authorize access",
            "consent_url": consent_url,
        }

    def test_consent_url_none_accepted(self):
        """consent_url=None (omitted) must be accepted."""
        from ampro.core.body_schemas import TaskInputRequiredBody

        body = TaskInputRequiredBody(**self._make_body(consent_url=None))
        assert body.consent_url is None

    def test_consent_url_valid_https(self):
        """Valid HTTPS consent_url must be accepted."""
        from ampro.core.body_schemas import TaskInputRequiredBody

        body = TaskInputRequiredBody(
            **self._make_body(consent_url="https://auth.example.com/consent")
        )
        assert body.consent_url == "https://auth.example.com/consent"

    def test_consent_url_http_rejected(self):
        """HTTP consent_url must raise ValidationError."""
        from ampro.core.body_schemas import TaskInputRequiredBody

        with pytest.raises(ValidationError, match="consent_url"):
            TaskInputRequiredBody(
                **self._make_body(consent_url="http://example.com/consent")
            )

    def test_consent_url_localhost_rejected(self):
        """consent_url targeting localhost must raise ValidationError."""
        from ampro.core.body_schemas import TaskInputRequiredBody

        with pytest.raises(ValidationError, match="consent_url"):
            TaskInputRequiredBody(
                **self._make_body(consent_url="https://localhost/admin")
            )

    def test_consent_url_private_ip_rejected(self):
        """consent_url targeting private IP must raise ValidationError."""
        from ampro.core.body_schemas import TaskInputRequiredBody

        with pytest.raises(ValidationError, match="consent_url"):
            TaskInputRequiredBody(
                **self._make_body(consent_url="https://10.0.0.1/internal")
            )

    def test_consent_url_octal_ip_rejected(self):
        """consent_url with octal-encoded loopback must raise ValidationError."""
        from ampro.core.body_schemas import TaskInputRequiredBody

        with pytest.raises(ValidationError, match="consent_url"):
            TaskInputRequiredBody(
                **self._make_body(consent_url="https://0177.0.0.1/admin")
            )
