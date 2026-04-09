"""Comprehensive tests for agent-protocol package."""

import pytest
from pydantic import ValidationError


class TestImports:
    def test_version(self):
        import ampro
        assert ampro.__version__ == "0.1.1"

    def test_all_exports(self):
        import ampro
        assert len(ampro.__all__) >= 100


class TestAddressing:
    def test_parse_host(self):
        from ampro import parse_agent_uri, AddressType
        addr = parse_agent_uri("agent://bakery.com")
        assert addr.address_type == AddressType.HOST
        assert addr.host == "bakery.com"

    def test_parse_slug(self):
        from ampro import parse_agent_uri, AddressType
        addr = parse_agent_uri("agent://sales@acme.example.com")
        assert addr.address_type == AddressType.SLUG
        assert addr.slug == "sales"
        assert addr.registry == "acme.example.com"

    def test_parse_did(self):
        from ampro import parse_agent_uri, AddressType
        addr = parse_agent_uri("agent://did:web:example.com")
        assert addr.address_type == AddressType.DID

    def test_normalize(self):
        from ampro import normalize_shorthand
        assert normalize_shorthand("@test", "registry.example.com") == "agent://test@registry.example.com"

    def test_invalid_scheme(self):
        from ampro import parse_agent_uri
        with pytest.raises(ValueError):
            parse_agent_uri("http://bakery.com")


class TestEnvelope:
    def test_body_type_field(self):
        from ampro import AgentMessage
        msg = AgentMessage(sender="agent://a.com", recipient="agent://b.com", body_type="task.create")
        assert msg.body_type == "task.create"

    def test_body_type_default(self):
        from ampro import AgentMessage
        msg = AgentMessage(sender="agent://a.com", recipient="agent://b.com")
        assert msg.body_type == "message"

    def test_headers_count(self):
        from ampro import STANDARD_HEADERS
        assert len(STANDARD_HEADERS) == 41


class TestBodySchemas:
    def test_validate_task_create(self):
        from ampro import validate_body
        body = validate_body("task.create", {"description": "Do something"})
        assert body.description == "Do something"

    def test_invalid_body(self):
        from ampro import validate_body
        with pytest.raises(ValidationError):
            validate_body("task.create", {})

    def test_unknown_passthrough(self):
        from ampro import validate_body
        result = validate_body("com.custom.type", {"foo": "bar"})
        assert result == {"foo": "bar"}

    def test_escalate_body(self):
        from ampro import validate_body
        body = validate_body("task.escalate", {
            "task_id": "t-1", "escalate_to": "sender_human", "reason": "Need help"
        })
        assert body.escalate_to == "sender_human"


class TestTrust:
    def test_four_tiers(self):
        from ampro import TrustTier
        assert len(TrustTier) == 4

    def test_can_delegate(self):
        from ampro import TrustTier
        assert TrustTier.EXTERNAL.can_delegate is False
        assert TrustTier.VERIFIED.can_delegate is True
        assert TrustTier.OWNER.can_delegate is True

    def test_clock_skew(self):
        from ampro import CLOCK_SKEW_SECONDS
        assert CLOCK_SKEW_SECONDS == 60


class TestCapabilities:
    def test_eight_groups(self):
        from ampro import CapabilityGroup
        assert len(CapabilityGroup) == 8

    def test_level_computation(self):
        from ampro import CapabilityGroup, CapabilitySet
        caps = CapabilitySet(groups={CapabilityGroup.MESSAGING, CapabilityGroup.TOOLS})
        assert caps.level == 2


class TestStreaming:
    def test_ten_events(self):
        from ampro import StreamingEventType
        assert len(StreamingEventType) == 10

    def test_heartbeat(self):
        from ampro import StreamingEventType
        assert StreamingEventType.HEARTBEAT == "heartbeat"

    def test_seq_field(self):
        from ampro import StreamingEvent, StreamingEventType
        event = StreamingEvent(type=StreamingEventType.HEARTBEAT, seq=42, id="s:42")
        assert event.seq == 42

    def test_sse_format(self):
        from ampro import StreamingEvent, StreamingEventType
        event = StreamingEvent(type=StreamingEventType.TEXT_DELTA, seq=1, id="s:1", data={"text": "hi"})
        sse = event.to_sse()
        assert "event: text_delta" in sse
        assert "id: s:1" in sse


class TestDelegation:
    def test_delegation_link_fields(self):
        from ampro import DelegationLink
        from datetime import datetime, timezone
        link = DelegationLink(
            delegator="agent://a.com", delegate="agent://b.com",
            scopes=["tool:read"], max_fan_out=5, trust_tier="verified",
            chain_budget="remaining=3.50USD;max=5.00USD",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
        )
        assert link.max_fan_out == 5
        assert link.trust_tier == "verified"

    def test_chain_budget_parse(self):
        from ampro import parse_chain_budget
        remaining, max_b = parse_chain_budget("remaining=3.50USD;max=5.00USD")
        assert remaining == 3.50
        assert max_b == 5.00

    def test_visited_agents(self):
        from ampro import check_visited_agents_loop
        assert check_visited_agents_loop("agent://a.com,agent://b.com", "agent://a.com") is True
        assert check_visited_agents_loop("agent://a.com,agent://b.com", "agent://c.com") is False


class TestAuth:
    def test_parse_bearer(self):
        from ampro import parse_authorization, AuthMethod
        auth = parse_authorization("Bearer token123")
        assert auth.method == AuthMethod.JWT

    def test_parse_did(self):
        from ampro import parse_authorization, AuthMethod
        auth = parse_authorization("DID proof123")
        assert auth.method == AuthMethod.DID

    def test_parse_apikey(self):
        from ampro import parse_authorization, AuthMethod
        auth = parse_authorization("ApiKey sk_123")
        assert auth.method == AuthMethod.API_KEY

    def test_parse_none(self):
        from ampro import parse_authorization, AuthMethod
        auth = parse_authorization(None)
        assert auth.method == AuthMethod.NONE


class TestCompliance:
    def test_content_classification(self):
        from ampro import ContentClassification
        assert ContentClassification.PII == "pii"
        assert ContentClassification.SENSITIVE_PII == "sensitive-pii"

    def test_erasure_request(self):
        from ampro import ErasureRequest
        req = ErasureRequest(
            subject_id="u-1", subject_proof="proof",
            scope="all", reason="user_request", deadline="2026-05-08T00:00:00Z",
        )
        assert req.scope == "all"

    def test_audit_logger(self):
        from ampro import AuditLogger, AuditEntry
        logger = AuditLogger()
        entry = logger.log(AuditEntry(
            message_id="m-1", sender="a", recipient="b", body_type="message",
        ))
        assert entry.hash != ""
        assert logger.verify_chain() is True


class TestSecurity:
    def test_dedup(self):
        import asyncio
        from ampro import InMemoryDedupStore
        store = InMemoryDedupStore(window_seconds=300)
        assert asyncio.run(store.is_duplicate("msg-1")) is False
        assert asyncio.run(store.is_duplicate("msg-1")) is True

    def test_nonce(self):
        from ampro import NonceTracker
        tracker = NonceTracker()
        assert tracker.is_replay("n-1") is False
        assert tracker.is_replay("n-1") is True

    def test_rate_limiter(self):
        from ampro import RateLimiter
        limiter = RateLimiter(rpm=2)
        allowed1, _ = limiter.check("s1")
        allowed2, _ = limiter.check("s1")
        allowed3, _ = limiter.check("s1")
        assert allowed1 is True
        assert allowed2 is True
        assert allowed3 is False


class TestNegotiation:
    def test_negotiate_version(self):
        from ampro import negotiate_version
        assert negotiate_version("2.0.0, 0.1.0") == "0.1.0"

    def test_negotiate_version_none(self):
        from ampro import negotiate_version, CURRENT_VERSION
        assert negotiate_version(None) == CURRENT_VERSION


class TestAgentJson:
    def test_schema(self):
        from ampro import AgentJson
        aj = AgentJson(
            protocol_version="0.1.0",
            identifiers=["agent://test.local"],
            endpoint="https://test.local/agent/message",
        )
        assert aj.ttl_seconds == 3600


class TestCrossVerification:
    def test_did_key_self_verifying(self):
        import asyncio
        from ampro import cross_verify_identifiers
        results = asyncio.run(cross_verify_identifiers(
            identifiers=["agent://did:key:z6MkTest"],
            expected_endpoint="https://example.com/agent/message",
        ))
        assert results[0].verified is True


class TestV011Imports:
    """Verify all v0.1.1 types are importable from ampro."""

    def test_version_bumped(self):
        import ampro
        assert ampro.__version__ == "0.1.1"

    def test_handshake_imports(self):
        from ampro import (
            HandshakeState, HandshakeStateMachine,
            SessionInitBody, SessionEstablishedBody, SessionConfirmBody,
            SessionPingBody, SessionPongBody,
            SessionPauseBody, SessionResumeBody, SessionCloseBody,
        )
        assert HandshakeState.IDLE.value == "idle"

    def test_session_binding_imports(self):
        from ampro import (
            SessionBinding, derive_binding_token,
            create_message_binding, verify_message_binding,
        )
        assert callable(derive_binding_token)

    def test_trust_score_imports(self):
        from ampro import TrustFactor, TrustScore, TrustPolicy, calculate_trust_score, score_to_policy
        assert TrustFactor.AGE.value == "age"

    def test_visibility_imports(self):
        from ampro import (
            VisibilityLevel, ContactPolicy, VisibilityConfig,
            check_contact_allowed, filter_agent_json,
        )
        assert VisibilityLevel.PUBLIC.value == "public"

    def test_context_schema_imports(self):
        from ampro import ContextSchemaInfo, parse_schema_urn, check_schema_supported
        assert callable(parse_schema_urn)

    def test_expanded_session_state(self):
        from ampro import SessionState
        # v0.1.1 added IDLE, INIT_SENT, INIT_RECEIVED, ESTABLISHED
        assert hasattr(SessionState, "IDLE")
        assert hasattr(SessionState, "INIT_SENT")
        assert hasattr(SessionState, "INIT_RECEIVED")
        assert hasattr(SessionState, "ESTABLISHED")

    def test_new_standard_headers(self):
        from ampro import STANDARD_HEADERS
        for h in ["Session-Binding", "Trust-Score", "Context-Schema", "Transaction-Id", "Correlation-Group", "Commitment-Level"]:
            assert h in STANDARD_HEADERS, f"Missing header: {h}"

    def test_agent_json_new_fields(self):
        from ampro import AgentJson
        aj = AgentJson(protocol_version="1.0.0", identifiers=["agent://test.com"], endpoint="https://test.com/agent/message")
        assert aj.visibility == {"level": "public", "contact_policy": "open"}
        assert aj.supported_schemas == []

    def test_all_exports_expanded(self):
        import ampro
        assert len(ampro.__all__) >= 115  # grew from 100+
