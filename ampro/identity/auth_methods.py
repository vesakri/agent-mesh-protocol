"""
Agent Protocol — Multi-Method Authorization.

Parses Authorization headers into structured auth info.
Supports: Bearer JWT, DID proof, API key, mTLS (implicit).

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AuthMethod(str, Enum):
    JWT = "jwt"
    DID = "did"
    API_KEY = "api_key"
    MTLS = "mtls"
    NONE = "none"


class ParsedAuth(BaseModel):
    method: AuthMethod = Field(default=AuthMethod.NONE, description="Detected authorization method (jwt, did, api_key, mtls, none)")
    token: str = Field(default="", description="Extracted token or credential value from the header")
    raw: str = Field(default="", description="Original Authorization header value before parsing")

    model_config = {"extra": "ignore"}

    def max_trust_tier(self) -> str:
        if self.method == AuthMethod.JWT:
            return "owner"
        if self.method in (AuthMethod.DID, AuthMethod.API_KEY, AuthMethod.MTLS):
            return "verified"
        return "external"


def parse_authorization(header: str | None) -> ParsedAuth:
    if not header:
        return ParsedAuth()
    stripped = header.strip()
    if not stripped:
        return ParsedAuth()
    lower = stripped.lower()
    if lower.startswith("bearer "):
        token = stripped[7:].strip()
        if not token:
            return ParsedAuth(raw=stripped)
        return ParsedAuth(method=AuthMethod.JWT, token=token, raw=stripped)
    if lower.startswith("did "):
        token = stripped[4:].strip()
        if not token:
            return ParsedAuth(raw=stripped)
        return ParsedAuth(method=AuthMethod.DID, token=token, raw=stripped)
    if lower.startswith("apikey "):
        token = stripped[7:].strip()
        if not token:
            return ParsedAuth(raw=stripped)
        return ParsedAuth(method=AuthMethod.API_KEY, token=token, raw=stripped)
    return ParsedAuth(raw=stripped)
