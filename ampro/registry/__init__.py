"""Agent registry, search, and federation."""

from ampro.registry.federation import (
    RegistryFederationRequest,
    RegistryFederationResponse,
    verify_federation_trust_proof,
)
from ampro.registry.search import (
    RegistrySearchMatch,
    RegistrySearchRequest,
    RegistrySearchResult,
)
from ampro.registry.types import RegistryRegistration, RegistryResolution

__all__ = [
    # Types
    "RegistryResolution", "RegistryRegistration",
    # Search
    "RegistrySearchRequest", "RegistrySearchMatch", "RegistrySearchResult",
    # Federation
    "RegistryFederationRequest", "RegistryFederationResponse",
    "verify_federation_trust_proof",
]
