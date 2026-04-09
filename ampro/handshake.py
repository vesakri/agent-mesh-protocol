"""
Agent Protocol — Handshake Body Types & State Machine.

Implements the session handshake lifecycle for the Agent Mesh Protocol:
  1. Client sends session.init with proposed capabilities and nonce
  2. Server replies with session.established (negotiated capabilities + binding token)
  3. Client sends session.confirm (binding proof)
  4. Session transitions to ACTIVE

Once active, sessions support ping/pong keepalive, pause/resume, and close.

The HandshakeStateMachine enforces valid state transitions and raises
ValueError on illegal moves.

PURE — zero platform-specific imports. Only pydantic and stdlib.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Handshake state enum
# ---------------------------------------------------------------------------


class HandshakeState(str, Enum):
    """States in the session handshake lifecycle."""

    IDLE = "idle"
    INIT_SENT = "init_sent"
    INIT_RECEIVED = "init_received"
    ESTABLISHED = "established"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# Session init / teardown body types
# ---------------------------------------------------------------------------


class SessionInitBody(BaseModel):
    """body.type = 'session.init' — Propose a new session with capabilities."""

    proposed_capabilities: list[str] = Field(
        description="Capabilities the client wants to negotiate (e.g. messaging, tools, streaming)",
    )
    proposed_version: str = Field(
        description="Protocol version the client proposes (e.g. 1.0.0)",
    )
    client_nonce: str = Field(
        description="Random 256-bit hex string for replay protection",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID to resume or bind to",
    )

    model_config = {"extra": "ignore"}


class SessionEstablishedBody(BaseModel):
    """body.type = 'session.established' — Server accepts the session."""

    session_id: str = Field(
        description="Unique session identifier assigned by the server",
    )
    negotiated_capabilities: list[str] = Field(
        description="Intersection of proposed and supported capabilities",
    )
    negotiated_version: str = Field(
        description="Protocol version both sides agreed on",
    )
    trust_tier: str = Field(
        description="Trust tier granted to the client (internal, owner, verified, external)",
    )
    trust_score: int = Field(
        description="Numeric trust score from 0-1000",
    )
    session_ttl_seconds: int = Field(
        default=3600,
        description="Session time-to-live in seconds",
    )
    server_nonce: str = Field(
        description="Server-side 256-bit hex nonce for binding proof",
    )
    binding_token: str = Field(
        description="Token the client must prove possession of in session.confirm",
    )

    model_config = {"extra": "ignore"}


class SessionConfirmBody(BaseModel):
    """body.type = 'session.confirm' — Client proves it holds the binding token."""

    session_id: str = Field(
        description="Session ID from the session.established message",
    )
    binding_proof: str = Field(
        description="Cryptographic proof derived from client_nonce, server_nonce, and binding_token",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Keepalive body types
# ---------------------------------------------------------------------------


class SessionPingBody(BaseModel):
    """body.type = 'session.ping' — Keepalive ping."""

    session_id: str = Field(
        description="Session ID to keep alive",
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp of the ping",
    )

    model_config = {"extra": "ignore"}


class SessionPongBody(BaseModel):
    """body.type = 'session.pong' — Keepalive pong response."""

    session_id: str = Field(
        description="Session ID being kept alive",
    )
    timestamp: str = Field(
        description="ISO-8601 timestamp of the pong",
    )
    active_tasks: int = Field(
        default=0,
        description="Number of tasks currently active in this session",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Pause / resume / close body types
# ---------------------------------------------------------------------------


class SessionPauseBody(BaseModel):
    """body.type = 'session.pause' — Temporarily suspend the session."""

    session_id: str = Field(
        description="Session ID to pause",
    )
    reason: str | None = Field(
        default=None,
        description="Human-readable reason for pausing",
    )
    resume_token: str | None = Field(
        default=None,
        description="Token required to resume this session",
    )

    model_config = {"extra": "ignore"}


class SessionResumeBody(BaseModel):
    """body.type = 'session.resume' — Resume a paused session."""

    session_id: str = Field(
        description="Session ID to resume",
    )
    resume_token: str | None = Field(
        default=None,
        description="Token provided during pause, if one was issued",
    )

    model_config = {"extra": "ignore"}


class SessionCloseBody(BaseModel):
    """body.type = 'session.close' — Gracefully close the session."""

    session_id: str = Field(
        description="Session ID to close",
    )
    reason: str | None = Field(
        default=None,
        description="Human-readable reason for closing",
    )

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Handshake state machine
# ---------------------------------------------------------------------------

# Transition table: (current_state, event) → next_state
_TRANSITIONS: dict[tuple[HandshakeState, str], HandshakeState] = {
    # Initiating
    (HandshakeState.IDLE, "send_init"): HandshakeState.INIT_SENT,
    (HandshakeState.IDLE, "receive_init"): HandshakeState.INIT_RECEIVED,
    # Establishing
    (HandshakeState.INIT_SENT, "receive_established"): HandshakeState.ESTABLISHED,
    (HandshakeState.INIT_RECEIVED, "send_established"): HandshakeState.ESTABLISHED,
    # Confirming
    (HandshakeState.ESTABLISHED, "receive_confirm"): HandshakeState.CONFIRMED,
    (HandshakeState.ESTABLISHED, "send_confirm"): HandshakeState.CONFIRMED,
    # Activating
    (HandshakeState.CONFIRMED, "activate"): HandshakeState.ACTIVE,
    # Pause / resume
    (HandshakeState.ACTIVE, "pause"): HandshakeState.PAUSED,
    (HandshakeState.PAUSED, "resume"): HandshakeState.ACTIVE,
    # Closing (from multiple states)
    (HandshakeState.ACTIVE, "close"): HandshakeState.CLOSED,
    (HandshakeState.PAUSED, "close"): HandshakeState.CLOSED,
    (HandshakeState.ESTABLISHED, "close"): HandshakeState.CLOSED,
}


class HandshakeStateMachine:
    """Enforces valid state transitions for the session handshake lifecycle.

    Usage:
        sm = HandshakeStateMachine()
        sm.transition("send_init")       # IDLE → INIT_SENT
        sm.transition("receive_established")  # INIT_SENT → ESTABLISHED
        sm.transition("send_confirm")    # ESTABLISHED → CONFIRMED
        sm.transition("activate")        # CONFIRMED → ACTIVE

        sm.transition("invalid_event")   # raises ValueError
    """

    def __init__(self) -> None:
        self._state = HandshakeState.IDLE

    @property
    def state(self) -> HandshakeState:
        """Current state of the handshake."""
        return self._state

    def transition(self, event: str) -> HandshakeState:
        """Attempt a state transition triggered by *event*.

        Args:
            event: The transition event name (e.g., "send_init", "close").

        Returns:
            The new HandshakeState after a successful transition.

        Raises:
            ValueError: If the event is not valid for the current state.
        """
        key = (self._state, event)
        next_state = _TRANSITIONS.get(key)
        if next_state is None:
            raise ValueError(
                f"Invalid transition: event '{event}' is not allowed "
                f"in state '{self._state.value}'"
            )
        self._state = next_state
        return self._state
