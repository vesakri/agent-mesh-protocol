"""Minimal AMP Client SDK.

Provides a thin, ergonomic layer over the AMP wire protocol for sending
messages, discovering agents, streaming events, and managing sessions.

Usage::

    from ampro.client import send, discover, stream, connect

    # Fire-and-forget message
    reply = await send("agent://weather.example.com", body={"q": "forecast"})

    # Discover capabilities
    info = await discover("agent://weather.example.com")

    # Stream task events
    async for event in stream("agent://weather.example.com", task_id="t-1"):
        print(event.type, event.data)

    # Session with 3-phase handshake
    async with await connect("agent://weather.example.com") as session:
        reply = await session.send({"q": "forecast"})
"""

from __future__ import annotations

from ampro.client.discover import discover
from ampro.client.errors import AmpProtocolError
from ampro.client.send import send
from ampro.client.session import Session, connect
from ampro.client.stream import stream

__all__ = ["send", "discover", "stream", "connect", "Session", "AmpProtocolError"]
