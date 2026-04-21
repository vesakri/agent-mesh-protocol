"""
Agent Protocol — Erasure Authorization (C8).

Owner-only authorization for GDPR erasure requests. Pure logic — no
platform-specific imports, no I/O, no state.

This module is PURE — no platform-specific imports.
"""

from __future__ import annotations


def is_authorized_to_erase(
    *,
    sender: str,
    subject_id: str,
    platform_identities: frozenset[str],
) -> bool:
    """Owner-only authorization for erasure requests.

    Returns True if and only if:
      - sender == subject_id (subject is erasing their own data), OR
      - sender in platform_identities (e.g. the runtime's own identity
        making a system-initiated erasure)

    ``subject_proof`` is NOT consulted in v1. The field on
    ``ErasureRequest`` is reserved for future signed-proof support once
    the format and issuer trust model are validated by product/legal.

    "sender" comes from the verified envelope, which the bus's signature
    verification has already authenticated (P0.A).

    Args:
        sender: The authenticated identity of the requester (from the
            verified message envelope).
        subject_id: The ``subject_id`` field from the ``ErasureRequest``
            — the data subject whose data would be erased.
        platform_identities: A frozenset of identities that the platform
            considers trusted for system-initiated erasure (e.g. the
            runtime service identity, an admin identity).

    Returns:
        True if the sender is authorized; False otherwise.
    """
    if sender == subject_id:
        return True
    if sender in platform_identities:
        return True
    return False
