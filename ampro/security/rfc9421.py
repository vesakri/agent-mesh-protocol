"""
Agent Protocol -- RFC 9421 HTTP Message Signatures.

Implements HTTP message signing and verification using Ed25519,
following RFC 9421 (HTTP Message Signatures) conventions.

Covered components: @method, @target-uri, @authority,
content-digest, content-type.

NOTE: This file must NOT import any app.* modules outside
protocol siblings -- it is protocol-pure.
"""

from __future__ import annotations

import base64
import hashlib
import re
import time
from urllib.parse import urlparse

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


# ---------------------------------------------------------------------------
# Content-Digest helper
# ---------------------------------------------------------------------------


def _content_digest_sha256(body: bytes) -> str:
    """
    Compute Content-Digest header value per RFC 9530.

    Returns:
        String in format ``sha-256=:<base64>:``
    """
    digest = hashlib.sha256(body).digest()
    b64 = base64.b64encode(digest).decode("ascii")
    return f"sha-256=:{b64}:"


# ---------------------------------------------------------------------------
# Signature base construction
# ---------------------------------------------------------------------------

# Derived components start with "@"
_DERIVED_COMPONENTS = {"@method", "@target-uri", "@authority"}


def create_signature_base(
    method: str,
    url: str,
    headers: dict[str, str],
    covered_components: list[str],
    *,
    created: int | None = None,
    keyid: str = "",
) -> str:
    """
    Build the signature base string per RFC 9421 Section 2.5.

    Each covered component occupies its own line in the format::

        "<component>": <value>

    The final line is the ``@signature-params`` pseudo-component
    containing the ordered list of covered components plus metadata.

    Args:
        method: HTTP method (GET, POST, ...).
        url: Full request URL.
        headers: HTTP headers (case-insensitive lookup).
        covered_components: Ordered list of component identifiers
            (e.g. ``["@method", "@target-uri", "content-type"]``).
        created: Unix timestamp; defaults to ``int(time.time())``.
        keyid: Key identifier to embed in signature params.

    Returns:
        The signature base string ready for signing.
    """
    if created is None:
        created = int(time.time())

    parsed = urlparse(url)
    # Case-insensitive header lookup
    lower_headers = {k.lower(): v for k, v in headers.items()}

    lines: list[str] = []
    for comp in covered_components:
        if comp == "@method":
            lines.append(f'"@method": {method.upper()}')
        elif comp == "@target-uri":
            lines.append(f'"@target-uri": {url}')
        elif comp == "@authority":
            authority = parsed.netloc or parsed.hostname or ""
            lines.append(f'"@authority": {authority}')
        else:
            # Regular header field
            value = lower_headers.get(comp.lower(), "")
            lines.append(f'"{comp}": {value}')

    # Build @signature-params
    comp_list = " ".join(f'"{c}"' for c in covered_components)
    sig_params = f"({comp_list});created={created};keyid=\"{keyid}\";alg=\"ed25519\""
    lines.append(f'"@signature-params": {sig_params}')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def sign_request(
    private_key_bytes: bytes,
    key_id: str,
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None = None,
) -> dict[str, str]:
    """
    Sign an HTTP request per RFC 9421.

    If *body* is provided, a ``content-digest`` header value is computed
    and included in the covered components automatically.

    Args:
        private_key_bytes: Raw 32-byte Ed25519 private key.
        key_id: Key identifier (embedded in Signature-Input).
        method: HTTP method.
        url: Full request URL.
        headers: Mutable dict of HTTP headers (``content-digest`` is
            added when *body* is present).
        body: Optional request body bytes.

    Returns:
        Dict with ``Signature`` and ``Signature-Input`` header values
        to merge into the outgoing request headers.
    """
    # Determine covered components
    covered: list[str] = ["@method", "@target-uri", "@authority"]

    # If body is present, compute content-digest and add to headers
    if body is not None:
        digest_value = _content_digest_sha256(body)
        headers["content-digest"] = digest_value
        covered.append("content-digest")

    # Include content-type if present in headers
    lower_headers = {k.lower(): v for k, v in headers.items()}
    if "content-type" in lower_headers:
        covered.append("content-type")

    created = int(time.time())

    sig_base = create_signature_base(
        method=method,
        url=url,
        headers=headers,
        covered_components=covered,
        created=created,
        keyid=key_id,
    )

    # Sign with Ed25519
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature_bytes = private_key.sign(sig_base.encode("utf-8"))
    sig_b64 = base64.b64encode(signature_bytes).decode("ascii")

    # Build Signature-Input
    comp_list = " ".join(f'"{c}"' for c in covered)
    sig_input = f'sig1=({comp_list});created={created};keyid="{key_id}";alg="ed25519"'

    return {
        "Signature": f"sig1=:{sig_b64}:",
        "Signature-Input": sig_input,
    }


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

# Pattern to parse Signature-Input value
_SIG_INPUT_RE = re.compile(
    r"sig1=\((?P<components>[^)]*)\)"
    r";created=(?P<created>\d+)"
    r';keyid="(?P<keyid>[^"]*)"'
    r';alg="(?P<alg>[^"]*)"'
)


def verify_request(
    public_key_bytes: bytes,
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None = None,
) -> bool:
    """
    Verify an RFC 9421 signed HTTP request.

    Parses ``Signature-Input`` to determine the covered components,
    reconstructs the signature base, and verifies the Ed25519 signature.

    If *body* is provided and ``content-digest`` is among the covered
    components, the digest is recomputed and compared before signature
    verification proceeds.

    Args:
        public_key_bytes: Raw 32-byte Ed25519 public key.
        method: HTTP method.
        url: Full request URL.
        headers: HTTP headers (must include ``Signature``,
            ``Signature-Input``, and any covered header fields).
        body: Optional request body bytes.

    Returns:
        True if the signature is valid, False otherwise.
    """
    lower_headers = {k.lower(): v for k, v in headers.items()}

    sig_input_raw = lower_headers.get("signature-input", "")
    sig_raw = lower_headers.get("signature", "")

    if not sig_input_raw or not sig_raw:
        return False

    # Parse Signature-Input
    match = _SIG_INPUT_RE.match(sig_input_raw)
    if not match:
        return False

    components_str = match.group("components")
    created = int(match.group("created"))
    keyid = match.group("keyid")

    # Parse covered components: "comp1" "comp2" ...
    covered = re.findall(r'"([^"]+)"', components_str)

    # If body provided and content-digest is covered, verify digest first
    if body is not None and "content-digest" in covered:
        expected_digest = _content_digest_sha256(body)
        actual_digest = lower_headers.get("content-digest", "")
        if actual_digest != expected_digest:
            return False

    # Reconstruct signature base
    sig_base = create_signature_base(
        method=method,
        url=url,
        headers=headers,
        covered_components=covered,
        created=created,
        keyid=keyid,
    )

    # Extract signature bytes: sig1=:<base64>:
    sig_match = re.match(r"sig1=:([A-Za-z0-9+/=]+):", sig_raw)
    if not sig_match:
        return False
    sig_bytes = base64.b64decode(sig_match.group(1))

    # Verify with Ed25519
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(sig_bytes, sig_base.encode("utf-8"))
        return True
    except Exception:
        return False
