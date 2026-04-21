"""Tests for v0.1.9 encryption module."""




class TestEncryptedBody:
    """EncryptedBody — JWE-encrypted message body."""

    def test_encrypted_body_creation(self):
        from ampro import EncryptedBody

        body = EncryptedBody(
            ciphertext="Y2lwaGVydGV4dA==",
            iv="aXY=",
            tag="dGFn",
            algorithm="A256GCM",
            recipient_key_id="key-recipient-1",
        )
        assert body.ciphertext == "Y2lwaGVydGV4dA=="
        assert body.iv == "aXY="
        assert body.tag == "dGFn"
        assert body.algorithm == "A256GCM"
        assert body.recipient_key_id == "key-recipient-1"

    def test_content_encryption_header_constant(self):
        from ampro import CONTENT_ENCRYPTION_HEADER

        assert CONTENT_ENCRYPTION_HEADER == "Content-Encryption"

    def test_content_encryption_in_standard_headers(self):
        from ampro import STANDARD_HEADERS

        assert "Content-Encryption" in STANDARD_HEADERS

    def test_json_round_trip(self):
        from ampro import EncryptedBody

        body = EncryptedBody(
            ciphertext="abc123",
            iv="iv456",
            tag="tag789",
            algorithm="A128GCM",
            recipient_key_id="key-2",
        )
        json_str = body.model_dump_json()
        restored = EncryptedBody.model_validate_json(json_str)
        assert restored.ciphertext == body.ciphertext
        assert restored.iv == body.iv
        assert restored.tag == body.tag
        assert restored.algorithm == body.algorithm
        assert restored.recipient_key_id == body.recipient_key_id
