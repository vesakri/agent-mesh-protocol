"""Agent registry, search, and federation."""

from ampro.registry.types import RegistryResolution, RegistryRegistration
from ampro.registry.search import (
    RegistrySearchRequest, RegistrySearchMatch, RegistrySearchResult,
)
from ampro.registry.federation import (
    RegistryFederationRequest, RegistryFederationResponse,
    verify_federation_trust_proof,
)

__all__ = [
    # Types
    "RegistryResolution", "RegistryRegistration",
    # Search
    "RegistrySearchRequest", "RegistrySearchMatch", "RegistrySearchResult",
    # Federation
    "RegistryFederationRequest", "RegistryFederationResponse",
    "verify_federation_trust_proof",
]
