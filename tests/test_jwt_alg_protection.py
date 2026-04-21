"""Tests for JWT algorithm allow-list protection (P0.D finding 2.4)."""

from __future__ import annotations

import base64
import json

import pytest

from ampro.trust.resolver import ALLOWED_JWT_ALGS, validate_jwt_algorithm


def _make_jwt(alg: str) -> str:
    """Build a minimal JWT with the given alg header (no real signature)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": alg, "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "test"}).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


class TestValidateJwtAlgorithm:
    """validate_jwt_algorithm must reject dangerous algorithms."""

    def test_alg_none_lowercase(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("none")) is False

    def test_alg_none_capitalized(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("None")) is False

    def test_alg_none_uppercase(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("NONE")) is False

    def test_alg_hs256_symmetric_rejected(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("HS256")) is False

    def test_alg_hs384_symmetric_rejected(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("HS384")) is False

    def test_alg_hs512_symmetric_rejected(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("HS512")) is False

    def test_alg_eddsa_allowed(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("EdDSA")) is True

    def test_alg_rs256_allowed(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("RS256")) is True

    def test_alg_es256_allowed(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("ES256")) is True

    def test_alg_es384_allowed(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("ES384")) is True

    def test_alg_rs384_allowed(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("RS384")) is True

    def test_alg_rs512_allowed(self) -> None:
        assert validate_jwt_algorithm(_make_jwt("RS512")) is True

    def test_malformed_not_three_segments(self) -> None:
        assert validate_jwt_algorithm("only.two") is False

    def test_malformed_single_segment(self) -> None:
        assert validate_jwt_algorithm("nope") is False

    def test_malformed_four_segments(self) -> None:
        assert validate_jwt_algorithm("a.b.c.d") is False

    def test_invalid_base64_header(self) -> None:
        assert validate_jwt_algorithm("!!!.payload.sig") is False

    def test_header_not_json(self) -> None:
        header_b64 = base64.urlsafe_b64encode(b"not json").rstrip(b"=").decode()
        assert validate_jwt_algorithm(f"{header_b64}.payload.sig") is False

    def test_header_missing_alg(self) -> None:
        header_b64 = base64.urlsafe_b64encode(
            json.dumps({"typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        assert validate_jwt_algorithm(f"{header_b64}.payload.sig") is False

    def test_alg_not_string(self) -> None:
        header_b64 = base64.urlsafe_b64encode(
            json.dumps({"alg": 123}).encode()
        ).rstrip(b"=").decode()
        assert validate_jwt_algorithm(f"{header_b64}.payload.sig") is False

    def test_allowed_algs_constant_is_frozenset(self) -> None:
        assert isinstance(ALLOWED_JWT_ALGS, frozenset)
        assert "EdDSA" in ALLOWED_JWT_ALGS
        assert "none" not in ALLOWED_JWT_ALGS
        assert "HS256" not in ALLOWED_JWT_ALGS
