"""Identity, authentication, linking, and migration."""

from ampro.identity.auth_methods import AuthMethod, ParsedAuth, parse_authorization
from ampro.identity.cross_verification import (
    VerificationResult,
    check_all_verified,
    cross_verify_identifiers,
    get_failed_identifiers,
)
from ampro.identity.link import IdentityLinkProofBody
from ampro.identity.migration import IdentityMigrationBody
from ampro.identity.types import (
    ConsentGrant,
    ConsentRequest,
    ConsentScope,
    IdentityProof,
)

__all__ = [
    # Types
    "ConsentScope", "IdentityProof", "ConsentRequest", "ConsentGrant",
    # Auth methods
    "AuthMethod", "ParsedAuth", "parse_authorization",
    # Linking
    "IdentityLinkProofBody",
    # Migration
    "IdentityMigrationBody",
    # Cross-verification
    "VerificationResult", "cross_verify_identifiers",
    "check_all_verified", "get_failed_identifiers",
]
