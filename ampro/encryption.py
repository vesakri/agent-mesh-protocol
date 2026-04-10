"""
Agent Protocol — End-to-End Encryption.

JWE envelope support for encrypted message bodies. When the
Content-Encryption header is present, the body field contains an
EncryptedBody that must be decrypted before processing.

This module is PURE — only stdlib + pydantic.
No platform-specific imports (app.*, etc.).
Designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_ENCRYPTION_HEADER = "Content-Encryption"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class EncryptedBody(BaseModel):
    """JWE-encrypted message body payload."""

    ciphertext: str = Field(description="Base64-encoded encrypted payload")
    iv: str = Field(description="Base64-encoded initialization vector")
    tag: str = Field(description="Base64-encoded authentication tag")
    algorithm: str = Field(description="JWE encryption algorithm (e.g. A256GCM)")
    recipient_key_id: str = Field(description="Key ID of the intended recipient")

    model_config = {"extra": "ignore"}
