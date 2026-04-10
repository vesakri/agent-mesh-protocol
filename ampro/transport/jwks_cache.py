"""
Agent Protocol — JWKS Cache.

In-memory cache for JWKS responses with TTL-based expiry,
force-refresh support, and revoked key checking.

Spec ref: Section 3.8
"""

from __future__ import annotations

import time
from typing import Any


class JWKSCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[dict[str, Any], float]] = {}

    def get(self, url: str, force_refresh: bool = False) -> dict[str, Any] | None:
        if force_refresh:
            return None
        entry = self._store.get(url)
        if entry is None:
            return None
        jwks, cached_at = entry
        if time.monotonic() - cached_at > self._ttl:
            del self._store[url]
            return None
        return jwks

    def put(self, url: str, jwks: dict[str, Any]) -> None:
        self._store[url] = (jwks, time.monotonic())

    def invalidate(self, url: str) -> None:
        self._store.pop(url, None)

    @staticmethod
    def is_key_revoked(jwks: dict[str, Any], kid: str) -> bool:
        revoked = jwks.get("revoked", [])
        return any(r.get("kid") == kid for r in revoked)

    @staticmethod
    def get_non_expired_keys(jwks: dict[str, Any], kid: str) -> list[dict[str, Any]]:
        now = int(time.time())
        result = []
        for key in jwks.get("keys", []):
            if key.get("kid") != kid:
                continue
            exp = key.get("exp")
            if exp is not None and int(exp) < now:
                continue
            result.append(key)
        return result
