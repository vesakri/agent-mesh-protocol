"""Tests for PII detection + content classification (C7).

15 tests covering:
- Each PII pattern individually (9 tests)
- Middleware override behavior (3 tests)
- Bus integration wiring (3 tests)
"""

from __future__ import annotations

from ampro.compliance.middleware import (
    check_content_classification,
)
from ampro.compliance.pii_patterns import (
    _luhn_valid,
    detect_pii,
    tier_rank,
)
from ampro.core.envelope import AgentMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _msg(body, classification: str = "public", **kw) -> AgentMessage:
    """Build a minimal AgentMessage with the given body and classification."""
    headers = {"Content-Classification": classification}
    return AgentMessage(
        sender="agent://test/sender",
        recipient="agent://test/recipient",
        body_type="message",
        body=body,
        headers=headers,
        **kw,
    )


# ===========================================================================
# Pattern tests — one per detection type
# ===========================================================================


class TestCreditCardDetection:
    """1. Credit card with Luhn validation."""

    def test_valid_cc_detected(self):
        # Visa test number (Luhn-valid)
        body = {"card": "4111111111111111"}
        detections = detect_pii(body)
        assert len(detections) >= 1
        cc = [d for d in detections if d.pattern_name == "credit_card"]
        assert len(cc) == 1
        assert cc[0].category == "pii"
        assert cc[0].path == "$.card"

    def test_invalid_luhn_not_detected(self):
        # Failing Luhn — change last digit
        body = {"card": "4111111111111112"}
        detections = detect_pii(body)
        cc = [d for d in detections if d.pattern_name == "credit_card"]
        assert len(cc) == 0

    def test_luhn_algorithm(self):
        assert _luhn_valid("4111111111111111") is True
        assert _luhn_valid("4111111111111112") is False
        assert _luhn_valid("5500000000000004") is True  # Mastercard test


class TestEmailDetection:
    """2. Email pattern."""

    def test_email_detected(self):
        body = {"contact": "user@example.com"}
        detections = detect_pii(body)
        emails = [d for d in detections if d.pattern_name == "email"]
        assert len(emails) == 1
        assert emails[0].category == "pii"
        assert emails[0].path == "$.contact"


class TestSSNDetection:
    """3. US SSN pattern."""

    def test_ssn_detected(self):
        body = {"ssn": "123-45-6789"}
        detections = detect_pii(body)
        ssns = [d for d in detections if d.pattern_name == "ssn"]
        assert len(ssns) == 1
        assert ssns[0].category == "pii"


class TestPhoneDetection:
    """4. US phone pattern."""

    def test_us_phone_detected(self):
        body = {"phone": "555-123-4567"}
        detections = detect_pii(body)
        phones = [d for d in detections if d.pattern_name == "us_phone"]
        assert len(phones) == 1
        assert phones[0].category == "pii"


class TestIPDetection:
    """5. IPv4 and IPv6 patterns."""

    def test_ipv4_detected(self):
        body = {"server": "192.168.1.100"}
        detections = detect_pii(body)
        ips = [d for d in detections if d.pattern_name == "ip_address"]
        assert len(ips) >= 1
        assert ips[0].category == "pii"

    def test_ipv6_detected(self):
        body = {"server": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"}
        detections = detect_pii(body)
        ips = [d for d in detections if d.pattern_name == "ip_address"]
        assert len(ips) >= 1
        assert ips[0].category == "pii"


class TestAPIKeyDetection:
    """6-7. Anthropic and OpenAI API key patterns."""

    def test_anthropic_key_detected(self):
        body = {"key": "sk-ant-api03-abcdefghijklmnopqrstuvwxyz"}
        detections = detect_pii(body)
        keys = [d for d in detections if d.pattern_name == "llm_api_key"]
        assert len(keys) == 1
        assert keys[0].category == "secret"

    def test_openai_key_detected(self):
        body = {"key": "sk-proj-abcdefghijklmnopqrstuvwxyz"}
        detections = detect_pii(body)
        keys = [d for d in detections if d.pattern_name == "llm_api_key"]
        assert len(keys) == 1
        assert keys[0].category == "secret"


class TestAWSKeyDetection:
    """8. AWS access key pattern."""

    def test_aws_key_detected(self):
        body = {"aws": "AKIAIOSFODNN7EXAMPLE"}
        detections = detect_pii(body)
        aws = [d for d in detections if d.pattern_name == "aws_access_key"]
        assert len(aws) == 1
        assert aws[0].category == "secret"


class TestPrivateKeyDetection:
    """9. Private key header pattern."""

    def test_private_key_detected(self):
        body = {"pem": "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."}
        detections = detect_pii(body)
        pks = [d for d in detections if d.pattern_name == "private_key"]
        assert len(pks) == 1
        assert pks[0].category == "secret"


# ===========================================================================
# Recursive walker tests
# ===========================================================================


class TestRecursiveWalker:
    """Tests for nested structure detection and JSON path reporting."""

    def test_nested_dict(self):
        body = {"user": {"profile": {"email": "test@example.com"}}}
        detections = detect_pii(body)
        emails = [d for d in detections if d.pattern_name == "email"]
        assert len(emails) == 1
        assert emails[0].path == "$.user.profile.email"

    def test_list_indexing(self):
        body = {"users": ["alice@example.com", "bob@example.com"]}
        detections = detect_pii(body)
        emails = [d for d in detections if d.pattern_name == "email"]
        assert len(emails) == 2
        paths = {d.path for d in emails}
        assert "$.users[0]" in paths
        assert "$.users[1]" in paths

    def test_no_detections_clean_body(self):
        body = {"message": "Hello, world!", "count": 42}
        detections = detect_pii(body)
        assert detections == []


# ===========================================================================
# Middleware override behavior
# ===========================================================================


class TestMiddlewareOverride:
    """Tests for classification override logic in check_content_classification."""

    def test_no_pii_returns_sender_classification(self):
        """Clean body: sender's classification is preserved, no override."""
        msg = _msg({"greeting": "hello"}, classification="public")
        result = check_content_classification(msg)
        assert result.allowed is True
        assert result.overridden is False
        assert result.classification == "public"

    def test_override_when_pii_detected_and_sender_under_classified(self):
        """Sender says public, but body has an email -> override to pii."""
        msg = _msg(
            {"contact": "user@example.com"},
            classification="public",
        )
        result = check_content_classification(msg)
        assert result.allowed is True
        assert result.overridden is True
        assert result.classification == "pii"

    def test_no_override_when_sender_already_strict(self):
        """Sender already claims pii for email content -> no override."""
        msg = _msg(
            {"contact": "user@example.com"},
            classification="pii",
        )
        result = check_content_classification(msg)
        assert result.allowed is True
        assert result.overridden is False
        assert result.classification == "pii"

    def test_secret_overrides_to_confidential(self):
        """Secret detection (API key) overrides to confidential tier."""
        msg = _msg(
            {"key": "sk-ant-api03-abcdefghijklmnopqrstuvwxyz"},
            classification="public",
        )
        result = check_content_classification(msg)
        assert result.allowed is True
        assert result.overridden is True
        assert result.classification == "confidential"

    def test_accepts_pii_false_blocks_detected_pii(self):
        """When accepts_pii=False and PII is detected, message is blocked."""
        msg = _msg(
            {"email": "user@example.com"},
            classification="public",
        )
        result = check_content_classification(msg, accepts_pii=False)
        assert result.allowed is False
        assert result.reason == "policy_violation"
        assert result.overridden is True
        assert result.classification == "pii"

    def test_accepts_pii_false_clean_body_allowed(self):
        """When accepts_pii=False but body is clean, message is allowed."""
        msg = _msg({"greeting": "hello"}, classification="public")
        result = check_content_classification(msg, accepts_pii=False)
        assert result.allowed is True


# ===========================================================================
# Tier ranking
# ===========================================================================


class TestTierRanking:
    """Tier rank ordering."""

    def test_tier_order(self):
        assert tier_rank("public") < tier_rank("internal")
        assert tier_rank("internal") < tier_rank("pii")
        assert tier_rank("pii") < tier_rank("sensitive-pii")
        assert tier_rank("sensitive-pii") < tier_rank("confidential")

    def test_unknown_tier_defaults_to_zero(self):
        assert tier_rank("unknown") == 0
        assert tier_rank("") == 0
