"""
Agent Protocol — Callback URL Delivery.

Delivers task results to caller-specified callback URLs with retry.
Uses the same AgentMessage envelope for delivery.

Spec ref: Section 5.5
- Verify callback URL reachability before accepting
- Retry: 3 attempts, exponential backoff (1s, 5s, 25s)
- SSRF validation on callback URLs
"""

from __future__ import annotations

import logging
from typing import Any

from ampro.transport.attachment import validate_attachment_url

logger = logging.getLogger(__name__)

RETRY_DELAYS = [1, 5, 25]  # seconds


def validate_callback_url(url: str) -> bool:
    """
    Validate a callback URL for safety.
    Must be HTTPS + pass SSRF checks.
    """
    if not url.startswith("https://"):
        return False
    return validate_attachment_url(url)


async def deliver_callback(
    callback_url: str,
    message: dict[str, Any],
    max_retries: int = 3,
) -> bool:
    """
    Deliver a message to a callback URL with retry.

    Returns True if delivery succeeded, False if all retries failed.

    WARNING: This implementation does not pin DNS resolution. Production
    deployments should resolve DNS once and pin the IP for the duration
    of delivery attempts to prevent DNS rebinding attacks.
    """
    import asyncio

    if not validate_callback_url(callback_url):
        logger.warning("Callback URL failed validation: %s", callback_url)
        return False

    # HEAD reachability check (spec Section 5.5)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            head_resp = await client.head(callback_url)
            if head_resp.status_code >= 400:
                logger.warning("Callback URL HEAD check failed: %s → %d", callback_url, head_resp.status_code)
                return False
    except Exception as exc:
        logger.warning("Callback URL unreachable: %s → %s", callback_url, exc)
        return False

    for attempt in range(max_retries):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    callback_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code in (200, 201, 202, 204):
                    logger.info("Callback delivered to %s (attempt %d)", callback_url, attempt + 1)
                    return True
                logger.warning(
                    "Callback to %s returned %d (attempt %d)",
                    callback_url, resp.status_code, attempt + 1,
                )
        except Exception as exc:
            logger.warning(
                "Callback to %s failed (attempt %d): %s",
                callback_url, attempt + 1, exc,
            )

        if attempt < max_retries - 1:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            await asyncio.sleep(delay)

    logger.error("Callback delivery to %s failed after %d attempts", callback_url, max_retries)
    return False
