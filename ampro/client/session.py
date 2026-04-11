"""
AMP Client SDK — Session management with 3-phase handshake.

Implements the full session lifecycle:
  1. Client sends ``session.init`` with ``client_nonce``
  2. Server replies ``session.established`` with ``server_nonce`` + ``binding_token``
  3. Client sends ``session.confirm`` with ``binding_proof``
  4. Session is ACTIVE — all subsequent messages include binding headers

Usage::

    from ampro.client import connect

    async with await connect("agent://weather.example.com") as session:
        reply = await session.send({"q": "forecast"})
        print(reply.body)
"""

from __future__ import annotations

import secrets
from types import TracebackType
from typing import Any

from ampro.core.envelope import AgentMessage
from ampro.session.binding import create_message_binding
from ampro.client.core import _resolve_endpoint, _post_message


class Session:
    """An active AMP session with automatic message binding.

    Obtained via :func:`connect`.  Use as an async context manager::

        async with await connect("agent://target.example.com") as s:
            reply = await s.send({"hello": "world"})
    """

    def __init__(
        self,
        *,
        endpoint: str,
        target_uri: str,
        sender: str,
        session_id: str,
        binding_token: str,
    ) -> None:
        self._endpoint = endpoint
        self._target_uri = target_uri
        self._sender = sender
        self.session_id = session_id
        self._binding_token = binding_token

    async def send(
        self,
        body: dict[str, Any],
        body_type: str = "message",
        headers: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> AgentMessage:
        """Send a message within this session.

        Automatically attaches ``Session-Id`` and ``Session-Binding``
        headers with a per-message HMAC proof.

        Args:
            body: Message body (dict).
            body_type: AMP body type (default ``"message"``).
            headers: Additional AMP headers.
            timeout: HTTP timeout in seconds.

        Returns:
            The response ``AgentMessage``.
        """
        msg_headers: dict[str, Any] = {"Session-Id": self.session_id}
        if headers:
            msg_headers.update(headers)

        msg = AgentMessage(
            sender=self._sender,
            recipient=self._target_uri,
            body_type=body_type,
            headers=msg_headers,
            body=body,
        )

        # Compute per-message binding proof
        binding_proof = create_message_binding(
            self.session_id,
            msg.id,
            self._binding_token,
        )

        return await _post_message(
            self._endpoint,
            msg,
            timeout=timeout,
            extra_headers={"Session-Binding": binding_proof},
        )

    async def close(self) -> None:
        """Gracefully close the session by sending ``session.close``."""
        msg = AgentMessage(
            sender=self._sender,
            recipient=self._target_uri,
            body_type="session.close",
            headers={"Session-Id": self.session_id},
            body={"session_id": self.session_id, "reason": "client_close"},
        )
        binding_proof = create_message_binding(
            self.session_id,
            msg.id,
            self._binding_token,
        )
        await _post_message(
            self._endpoint,
            msg,
            extra_headers={"Session-Binding": binding_proof},
        )

    async def __aenter__(self) -> Session:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            await self.close()
        except Exception:
            # Best-effort close — don't mask the original exception
            pass


async def connect(
    to: str,
    sender: str | None = None,
) -> Session:
    """Establish a session via the 3-phase AMP handshake.

    1. Sends ``session.init`` with a random ``client_nonce``.
    2. Receives ``session.established`` with ``server_nonce``,
       ``session_id``, and ``binding_token``.
    3. Sends ``session.confirm`` with ``binding_proof``
       (HMAC-SHA256 with binding_token as key over
       client_nonce + server_nonce + session_id).

    Args:
        to: Agent URI of the target agent.
        sender: Agent URI of the sender (defaults to ``"anonymous"``).

    Returns:
        An active ``Session`` ready for communication.

    Raises:
        AmpProtocolError: If any handshake step fails.
        ValueError: If the URI cannot be resolved or the server
            returns an unexpected body type.
    """
    endpoint = await _resolve_endpoint(to)
    sender_uri = sender or "anonymous"
    client_nonce = secrets.token_hex(32)

    # Phase 1: session.init
    init_msg = AgentMessage(
        sender=sender_uri,
        recipient=to,
        body_type="session.init",
        body={
            "proposed_capabilities": ["messaging"],
            "proposed_version": "1.0.0",
            "client_nonce": client_nonce,
        },
    )
    established_msg = await _post_message(endpoint, init_msg)

    # Validate the response
    if established_msg.body_type != "session.established":
        raise ValueError(
            f"Expected session.established, got {established_msg.body_type}"
        )

    body = established_msg.body
    if not isinstance(body, dict):
        raise ValueError("session.established body must be a dict")

    required_keys = {"session_id", "server_nonce", "binding_token"}
    missing = required_keys - set(body.keys())
    if missing:
        raise ValueError(f"session.established missing required fields: {missing}")

    session_id = body["session_id"]
    server_nonce = body["server_nonce"]
    binding_token = body["binding_token"]

    # Phase 2: compute binding proof
    # HMAC-SHA256 with binding_token as key, client_nonce + server_nonce as message
    from ampro.session.binding import derive_binding_token

    binding_proof = derive_binding_token(
        client_nonce=client_nonce,
        server_nonce=server_nonce,
        session_id=session_id,
        shared_secret=binding_token,
    )

    # Phase 3: session.confirm
    confirm_msg = AgentMessage(
        sender=sender_uri,
        recipient=to,
        body_type="session.confirm",
        headers={"Session-Id": session_id},
        body={
            "session_id": session_id,
            "binding_proof": binding_proof,
        },
    )
    await _post_message(endpoint, confirm_msg)

    return Session(
        endpoint=endpoint,
        target_uri=to,
        sender=sender_uri,
        session_id=session_id,
        binding_token=binding_token,
    )
