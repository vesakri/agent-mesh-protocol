"""
AMP Client SDK — Internal HTTP Transport.

NOT public API.  All public functions in send / discover / stream / session
delegate to these helpers for HTTP communication.

Handles:
  - agent:// URI resolution to HTTPS endpoints via /.well-known/agent.json
  - POST /agent/message with AgentMessage envelope
  - Error mapping from HTTP responses to AmpProtocolError
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ampro.core.addressing import AddressType, parse_agent_uri
from ampro.core.envelope import AgentMessage
from ampro.wire.errors import ProblemDetail
from ampro.client.errors import AmpProtocolError

logger = logging.getLogger("ampro.client")

# Header sent on all AMP client requests.
_USER_AGENT = "ampro-client/0.2.1"


async def _resolve_endpoint(uri: str) -> str:
    """Resolve an ``agent://`` URI to an HTTPS base URL.

    Currently supports HOST form only (e.g. ``agent://weather.example.com``).
    Slug and DID resolution are future work.

    Returns:
        The HTTPS base URL (e.g. ``https://weather.example.com``).

    Raises:
        ValueError: If the URI uses an unsupported address form (slug or DID).
    """
    addr = parse_agent_uri(uri)

    if addr.address_type == AddressType.HOST:
        return f"https://{addr.host}"

    if addr.address_type == AddressType.SLUG:
        raise ValueError(
            f"Slug-based addressing ({uri}) requires registry resolution "
            f"which is not yet implemented in the client SDK."
        )

    if addr.address_type == AddressType.DID:
        raise ValueError(
            f"DID-based addressing ({uri}) requires DID resolution "
            f"which is not yet implemented in the client SDK."
        )

    raise ValueError(f"Unknown address type: {addr.address_type}")


def _raise_for_problem(response: httpx.Response) -> None:
    """Parse a non-2xx response as RFC 7807 ProblemDetail and raise.

    If the response body cannot be parsed as ProblemDetail, a generic
    AmpProtocolError is raised with the status code and raw body.
    """
    try:
        data = response.json()
        problem = ProblemDetail.model_validate(data)
    except Exception:
        problem = ProblemDetail(
            type="urn:amp:error:unknown",
            title=f"HTTP {response.status_code}",
            status=response.status_code,
            detail=response.text[:512] if response.text else None,
        )
    raise AmpProtocolError(problem)


async def _post_message(
    endpoint: str,
    msg: AgentMessage,
    *,
    timeout: float = 30.0,
    extra_headers: dict[str, str] | None = None,
) -> AgentMessage:
    """POST an AgentMessage to ``/agent/message`` and return the response.

    Args:
        endpoint: HTTPS base URL of the target agent.
        msg: The message envelope to send.
        timeout: Request timeout in seconds.
        extra_headers: Additional HTTP headers (e.g. Session-Binding).

    Returns:
        The response parsed as an AgentMessage.

    Raises:
        AmpProtocolError: If the server returns a non-2xx response.
    """
    url = f"{endpoint}/agent/message"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": _USER_AGENT,
    }
    if extra_headers:
        headers.update(extra_headers)

    payload = msg.model_dump(mode="json")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
        )

    if response.status_code >= 400:
        _raise_for_problem(response)

    return AgentMessage.model_validate(response.json())


async def _get_json(
    url: str,
    *,
    timeout: float = 30.0,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """GET a URL and return parsed JSON.

    Raises:
        AmpProtocolError: If the server returns a non-2xx response.
    """
    headers = {"User-Agent": _USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code >= 400:
        _raise_for_problem(response)

    return response.json()
