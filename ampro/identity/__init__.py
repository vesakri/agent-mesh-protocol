"""Identity, authentication, linking, and migration."""

from ampro.identity.types import (
    ConsentScope, IdentityProof, ConsentRequest, ConsentGrant,
)
from ampro.identity.auth_methods import AuthMethod, ParsedAuth, parse_authorization
from ampro.identity.link import IdentityLinkProofBody
from ampro.identity.migration import IdentityMigrationBody
from ampro.identity.cross_verification import (
    VerificationResult, cross_verify_identifiers,
    check_all_verified, get_failed_identifiers,
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
