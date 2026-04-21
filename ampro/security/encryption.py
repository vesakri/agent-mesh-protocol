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
# Exceptions
# ---------------------------------------------------------------------------


class EncryptionDowngradeError(Exception):
    """Raised when a plaintext message arrives on a session that negotiated
    mandatory encryption.

    Sessions whose initial message set ``required_encryption=True`` on the
    :class:`EncryptedBody` MUST NOT accept subsequent plaintext bodies.
    Downgrade attempts are rejected at the middleware layer.
    """


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
    required_encryption: bool = Field(
        default=False,
        description=(
            "When True, all subsequent messages in this session MUST also be "
            "encrypted. Plaintext bodies received after this flag has been "
            "pinned on the session MUST be rejected (downgrade prevention)."
        ),
    )

    model_config = {"extra": "ignore"}


class EncryptionKeyOfferBody(BaseModel):
    """body.type = 'encryption.key_offer' — Advertise public-key wrapping options.

    Sent by the initiating side to announce which key-exchange schemes it
    supports and the corresponding public keys it will accept wraps for.
    The recipient picks one scheme and replies with an
    :class:`EncryptionKeyAcceptBody`.
    """

    agent_id: str = Field(description="agent:// URI of the offering agent")
    supported_schemes: list[str] = Field(
        description=(
            "Ordered list of key-exchange schemes the sender supports, "
            "e.g. ['x25519-chacha20poly1305']. Order indicates preference."
        ),
    )
    wrapping_keys: dict[str, str] = Field(
        description=(
            "Mapping of scheme identifier to base64-encoded public key the "
            "recipient should wrap its ephemeral/session key against."
        ),
    )

    model_config = {"extra": "ignore"}


class EncryptionKeyAcceptBody(BaseModel):
    """body.type = 'encryption.key_accept' — Recipient selects a scheme.

    The recipient chooses one scheme from the offer and returns its own
    ephemeral public key. Actual key derivation / wrapping is performed by
    the implementation plugged in on top of this protocol surface.
    """

    chosen_scheme: str = Field(
        description="Scheme selected from the offer's supported_schemes",
    )
    ephemeral_key: str = Field(
        description="Base64-encoded ephemeral public key for the chosen scheme",
    )

    model_config = {"extra": "ignore"}
