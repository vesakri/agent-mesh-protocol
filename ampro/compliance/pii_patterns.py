"""
Agent Protocol — PII Detection Patterns (C7).

Pure detection logic for personally identifiable information and secrets.
No I/O, no state, no platform-specific imports.

Detects:
- Credit card numbers (16 digits, Luhn-validated)
- Email addresses (RFC 5321 simplified)
- US Social Security Numbers (XXX-XX-XXXX)
- US phone numbers
- IPv4 and IPv6 addresses
- Anthropic API keys (sk-ant-)
- OpenAI API keys (sk-proj-)
- AWS access keys (AKIA...)
- Private key headers (-----BEGIN ... PRIVATE KEY-----)

Matched values are NEVER stored in Detection objects — only the
JSON path and the category/pattern name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Detection:
    """A single PII or secret detection.

    Attributes:
        path: JSON path where the detection occurred (e.g. ``$.user.email``).
        category: Broad category — ``"pii"`` or ``"secret"``.
        pattern_name: Specific pattern that matched (e.g. ``"credit_card"``,
            ``"email"``, ``"llm_api_key"``).
    """

    path: str
    category: str
    pattern_name: str


# ---------------------------------------------------------------------------
# Classification tier ordering (higher index = stricter)
# ---------------------------------------------------------------------------

_TIER_ORDER: dict[str, int] = {
    "public": 0,
    "internal": 1,
    "pii": 2,
    "sensitive-pii": 3,
    "confidential": 4,
}

# Maps a detection category to the content classification tier it implies.
_CATEGORY_TO_TIER: dict[str, str] = {
    "pii": "pii",
    "secret": "confidential",
}


def tier_rank(tier: str) -> int:
    """Return the numeric rank of a content classification tier.

    Unknown tiers are treated as rank 0 (``public``).
    """
    return _TIER_ORDER.get(tier, 0)


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# 1. Credit card — 16 contiguous digits (with optional separators)
_CC_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# 2. Email — simplified RFC 5321
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# 3. US Social Security Number
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# 4. US phone number (various common formats)
_US_PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

# 5. IPv4
_IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# 6. IPv6 (simplified — full or abbreviated)
_IPV6_PATTERN = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
    r"|\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b"
    r"|\b::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b"
    r"|\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b"
)

# 7. Anthropic API key
_ANTHROPIC_KEY_PATTERN = re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")

# 8. OpenAI API key
_OPENAI_KEY_PATTERN = re.compile(r"\bsk-proj-[A-Za-z0-9_\-]{20,}\b")

# 9. AWS access key
_AWS_KEY_PATTERN = re.compile(r"\bAKIA[A-Z0-9]{16}\b")

# 10. Private key header
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"
)

# Ordered list of (pattern, category, pattern_name).
_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (_CC_PATTERN, "pii", "credit_card"),
    (_EMAIL_PATTERN, "pii", "email"),
    (_SSN_PATTERN, "pii", "ssn"),
    (_US_PHONE_PATTERN, "pii", "us_phone"),
    (_IPV4_PATTERN, "pii", "ip_address"),
    (_IPV6_PATTERN, "pii", "ip_address"),
    (_ANTHROPIC_KEY_PATTERN, "secret", "llm_api_key"),
    (_OPENAI_KEY_PATTERN, "secret", "llm_api_key"),
    (_AWS_KEY_PATTERN, "secret", "aws_access_key"),
    (_PRIVATE_KEY_PATTERN, "secret", "private_key"),
]


# ---------------------------------------------------------------------------
# Luhn validator
# ---------------------------------------------------------------------------

def _luhn_valid(number: str) -> bool:
    """Validate a credit card number using the Luhn algorithm.

    ``number`` should contain only digits (strip spaces/dashes first).
    """
    digits = [int(d) for d in number]
    # Process from rightmost digit
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        doubled = d * 2
        total += doubled if doubled < 10 else doubled - 9
    return total % 10 == 0


def _strip_cc_separators(raw: str) -> str:
    """Remove spaces and dashes from a potential credit card number."""
    return re.sub(r"[ -]", "", raw)


# ---------------------------------------------------------------------------
# Recursive walker
# ---------------------------------------------------------------------------

def detect_pii(body: Any, *, _path: str = "$") -> list[Detection]:
    """Recursively walk ``body`` and detect PII / secrets.

    Returns a list of :class:`Detection` objects. Matched *values* are
    NEVER stored — only the JSON path and the category/pattern name.

    Args:
        body: The message body to scan. Can be a dict, list, string,
            or any nested combination.

    Returns:
        A list of Detection objects for every match found.
    """
    detections: list[Detection] = []

    if isinstance(body, str):
        _scan_string(body, _path, detections)
    elif isinstance(body, dict):
        for key, value in body.items():
            child_path = f"{_path}.{key}"
            detections.extend(detect_pii(value, _path=child_path))
    elif isinstance(body, (list, tuple)):
        for idx, item in enumerate(body):
            child_path = f"{_path}[{idx}]"
            detections.extend(detect_pii(item, _path=child_path))
    # Primitives other than str (int, float, bool, None) are not scanned.

    return detections


def _scan_string(text: str, path: str, detections: list[Detection]) -> None:
    """Scan a single string value against all PII patterns."""
    for pattern, category, pattern_name in _PATTERNS:
        matches = pattern.findall(text)
        if not matches:
            continue

        if pattern_name == "credit_card":
            # Credit card requires Luhn validation
            for match in matches:
                stripped = _strip_cc_separators(match)
                if len(stripped) >= 13 and stripped.isdigit() and _luhn_valid(stripped):
                    detections.append(Detection(path=path, category=category, pattern_name=pattern_name))
                    break  # One detection per path per pattern
        else:
            detections.append(Detection(path=path, category=category, pattern_name=pattern_name))
