"""Tests for handshake body types and state machine."""
import pytest


class TestHandshakeBodyTypes:
    # Test each of the 8 body types can be constructed with valid data
    def test_session_init_body(self):
        from ampro import SessionInitBody
        body = SessionInitBody(
            proposed_capabilities=["messaging", "tools"],
            proposed_version="1.0.0",
            client_nonce="abc123",
        )
        assert body.proposed_version == "1.0.0"
        assert body.conversation_id is None  # optional

    def test_session_init_body_with_conversation(self):
        from ampro import SessionInitBody
        body = SessionInitBody(
            proposed_capabilities=["messaging"],
            proposed_version="1.0.0",
            client_nonce="abc123",
            conversation_id="conv-1",
        )
        assert body.conversation_id == "conv-1"

    def test_session_established_body(self):
        from ampro import SessionEstablishedBody
        body = SessionEstablishedBody(
            session_id="sess-1",
            negotiated_capabilities=["messaging"],
            negotiated_version="1.0.0",
            trust_tier="verified",
            trust_score=450,
            server_nonce="xyz789",
            binding_token="token-abc",
        )
        assert body.session_ttl_seconds == 3600  # default
        assert body.trust_score == 450

    def test_session_confirm_body(self):
        from ampro import SessionConfirmBody
        body = SessionConfirmBody(session_id="sess-1", binding_proof="proof-123")
        assert body.binding_proof == "proof-123"

    def test_session_ping_body(self):
        from ampro import SessionPingBody
        body = SessionPingBody(session_id="sess-1", timestamp="2026-04-09T12:00:00Z")
        assert body.timestamp == "2026-04-09T12:00:00Z"

    def test_session_pong_body(self):
        from ampro import SessionPongBody
        body = SessionPongBody(session_id="sess-1", timestamp="2026-04-09T12:00:00Z")
        assert body.active_tasks == 0  # default

    def test_session_pong_body_with_tasks(self):
        from ampro import SessionPongBody
        body = SessionPongBody(session_id="sess-1", timestamp="2026-04-09T12:00:00Z", active_tasks=5)
        assert body.active_tasks == 5

    def test_session_pause_body(self):
        from ampro import SessionPauseBody
        body = SessionPauseBody(session_id="sess-1")
        assert body.reason is None
        assert body.resume_token is None

    def test_session_resume_body(self):
        from ampro import SessionResumeBody
        body = SessionResumeBody(session_id="sess-1", resume_token="tok-1")
        assert body.resume_token == "tok-1"

    def test_session_close_body(self):
        from ampro import SessionCloseBody
        body = SessionCloseBody(session_id="sess-1", reason="done")
        assert body.reason == "done"


class TestHandshakeStateMachine:
    def test_initial_state(self):
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        assert sm.state == HandshakeState.IDLE

    def test_client_flow(self):
        """Client: IDLE -> INIT_SENT -> ESTABLISHED -> CONFIRMED -> ACTIVE"""
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        assert sm.transition("send_init") == HandshakeState.INIT_SENT
        assert sm.transition("receive_established") == HandshakeState.ESTABLISHED
        assert sm.transition("send_confirm") == HandshakeState.CONFIRMED
        assert sm.transition("activate") == HandshakeState.ACTIVE

    def test_server_flow(self):
        """Server: IDLE -> INIT_RECEIVED -> ESTABLISHED -> CONFIRMED -> ACTIVE"""
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        assert sm.transition("receive_init") == HandshakeState.INIT_RECEIVED
        assert sm.transition("send_established") == HandshakeState.ESTABLISHED
        assert sm.transition("receive_confirm") == HandshakeState.CONFIRMED
        assert sm.transition("activate") == HandshakeState.ACTIVE

    def test_pause_resume(self):
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        sm.transition("send_init")
        sm.transition("receive_established")
        sm.transition("send_confirm")
        sm.transition("activate")
        assert sm.transition("pause") == HandshakeState.PAUSED
        assert sm.transition("resume") == HandshakeState.ACTIVE

    def test_close_from_active(self):
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        sm.transition("send_init")
        sm.transition("receive_established")
        sm.transition("send_confirm")
        sm.transition("activate")
        assert sm.transition("close") == HandshakeState.CLOSED

    def test_close_from_paused(self):
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        sm.transition("send_init")
        sm.transition("receive_established")
        sm.transition("send_confirm")
        sm.transition("activate")
        sm.transition("pause")
        assert sm.transition("close") == HandshakeState.CLOSED

    def test_close_from_established(self):
        """Abort during handshake"""
        from ampro import HandshakeStateMachine, HandshakeState
        sm = HandshakeStateMachine()
        sm.transition("send_init")
        sm.transition("receive_established")
        assert sm.transition("close") == HandshakeState.CLOSED

    def test_invalid_transition(self):
        from ampro import HandshakeStateMachine
        sm = HandshakeStateMachine()
        with pytest.raises(ValueError, match="not allowed"):
            sm.transition("activate")  # Can't activate from IDLE

    def test_invalid_transition_from_closed(self):
        from ampro import HandshakeStateMachine
        sm = HandshakeStateMachine()
        sm.transition("send_init")
        sm.transition("receive_established")
        sm.transition("close")
        with pytest.raises(ValueError):
            sm.transition("send_init")  # Can't restart from CLOSED


class TestHandshakeBodyTypeRegistry:
    """Test that session.* body types are registered in the body type registry."""

    def test_validate_session_init(self):
        from ampro import validate_body
        body = validate_body("session.init", {
            "proposed_capabilities": ["messaging"],
            "proposed_version": "1.0.0",
            "client_nonce": "abc",
        })
        assert hasattr(body, "proposed_capabilities")

    def test_validate_session_established(self):
        from ampro import validate_body
        body = validate_body("session.established", {
            "session_id": "s1",
            "negotiated_capabilities": ["messaging"],
            "negotiated_version": "1.0.0",
            "trust_tier": "verified",
            "trust_score": 450,
            "server_nonce": "xyz",
            "binding_token": "tok",
        })
        assert hasattr(body, "session_id")

    def test_validate_session_close(self):
        from ampro import validate_body
        body = validate_body("session.close", {"session_id": "s1"})
        assert hasattr(body, "session_id")

    def test_all_eight_registered(self):
        from ampro import validate_body
        types = [
            "session.init", "session.established", "session.confirm",
            "session.ping", "session.pong",
            "session.pause", "session.resume", "session.close",
        ]
        for t in types:
            # Should not return raw dict (which means "unknown type")
            if t == "session.init":
                result = validate_body(t, {"proposed_capabilities": ["x"], "proposed_version": "1.0.0", "client_nonce": "n"})
            elif t == "session.established":
                result = validate_body(t, {"session_id": "s", "negotiated_capabilities": ["x"], "negotiated_version": "1.0.0", "trust_tier": "verified", "trust_score": 0, "server_nonce": "n", "binding_token": "t"})
            elif t == "session.confirm":
                result = validate_body(t, {"session_id": "s", "binding_proof": "p"})
            elif t in ("session.ping", "session.pong"):
                result = validate_body(t, {"session_id": "s", "timestamp": "2026-01-01T00:00:00Z"})
            elif t == "session.pause":
                result = validate_body(t, {"session_id": "s"})
            elif t == "session.resume":
                result = validate_body(t, {"session_id": "s"})
            elif t == "session.close":
                result = validate_body(t, {"session_id": "s"})
            assert not isinstance(result, dict), f"{t} should be registered but returned raw dict"
