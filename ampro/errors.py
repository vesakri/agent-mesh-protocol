"""Unified error hierarchy for ampro.

All module-specific errors inherit from ``AmpError`` so callers can
catch protocol-level failures uniformly while still distinguishing
crypto from compliance from transport failures.

The hierarchy is intentionally shallow:

  AmpError
    ├── ValidationError           — envelope / body / addressing
    ├── TrustError                — trust resolution or verification
    ├── CryptoError               — cryptographic operation failure
    ├── SessionError              — session handshake / state-machine
    ├── CompliancePolicyError     — jurisdiction / residency / erasure
    ├── RateLimitError            — rate limit / quota exceeded
    ├── TransportError            — transport-level failures (redirect,
    │                                SSRF, etc.)
    └── NotImplementedInProtocol  — feature defined but not implemented

Module-specific exceptions in other parts of ampro inherit from the
appropriate base so that callers can write ``except AmpError`` once
to catch any protocol-level failure.
"""

from __future__ import annotations


class AmpError(Exception):
    """Base class for all ampro exceptions."""


class ValidationError(AmpError):
    """Protocol validation failure (envelope, body, addressing)."""


class TrustError(AmpError):
    """Trust resolution or verification failure."""


class CryptoError(AmpError):
    """Cryptographic operation failure."""


class SessionError(AmpError):
    """Session handshake or state-machine failure."""


class CompliancePolicyError(AmpError):
    """Compliance policy violation (jurisdiction, residency, erasure)."""


class RateLimitError(AmpError):
    """Rate limit / quota exceeded."""


class TransportError(AmpError):
    """Transport-level failure (redirect loop, SSRF rejected, etc.)."""


class NotImplementedInProtocol(AmpError):
    """Feature is defined in the protocol but not implemented by this peer."""


# ---------------------------------------------------------------------------
# Concrete transport-level exceptions
# ---------------------------------------------------------------------------


class RedirectLoopError(TransportError):
    """Raised when a task.redirect chain exceeds max hops or contains a cycle."""


class MigrationChainTooLongError(TransportError):
    """Raised when following ``moved_to`` pointers exceeds ``MAX_MIGRATION_HOPS``."""
