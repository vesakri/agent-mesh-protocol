"""Comprehensive tests for agent-protocol package."""

import pytest
from pydantic import ValidationError


class TestImports:
    def test_version(self):
        import ampro
        assert ampro.__version__ == "0.1.7"

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
        assert len(STANDARD_HEADERS) == 50


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
    def test_seventeen_events(self):
        from ampro import StreamingEventType
        assert len(StreamingEventType) == 17

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
        assert ampro.__version__ == "0.1.7"

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


class TestV012Imports:
    """Verify all v0.1.2 types are importable from ampro."""

    def test_version_is_016(self):
        import ampro
        assert ampro.__version__ == "0.1.7"

    def test_key_revocation_imports(self):
        from ampro import RevocationReason, KeyRevocationBody
        assert RevocationReason.KEY_COMPROMISE.value == "key_compromise"

    def test_challenge_imports(self):
        from ampro import ChallengeReason, TaskChallengeBody, TaskChallengeResponseBody
        assert ChallengeReason.FIRST_CONTACT.value == "first_contact"

    def test_tool_consent_imports(self):
        from ampro import ToolConsentRequestBody, ToolConsentGrantBody, ToolDefinition
        td = ToolDefinition(name="test", description="test tool")
        assert td.consent_required is False

    def test_backpressure_imports(self):
        from ampro import StreamAckEvent, StreamPauseEvent, StreamResumeEvent
        ack = StreamAckEvent(last_seq=1, timestamp="2026-01-01T00:00:00Z")
        assert ack.last_seq == 1

    def test_trust_upgrade_imports(self):
        from ampro import TrustUpgradeRequestBody, TrustUpgradeResponseBody
        assert TrustUpgradeRequestBody.model_fields["timeout_seconds"].default == 300

    def test_streaming_event_type_backpressure_members(self):
        from ampro import StreamingEventType
        assert hasattr(StreamingEventType, "STREAM_ACK")
        assert hasattr(StreamingEventType, "STREAM_PAUSE")
        assert hasattr(StreamingEventType, "STREAM_RESUME")

    def test_new_v012_headers(self):
        from ampro import STANDARD_HEADERS
        for h in ["Key-Revoked-At", "Anonymous-Sender-Hint"]:
            assert h in STANDARD_HEADERS, f"Missing v0.1.2 header: {h}"

    def test_all_exports_148(self):
        import ampro
        assert len(ampro.__all__) >= 148


class TestSessionResumption:
    """Test session resumption fields added in v0.1.2."""

    def test_session_init_has_previous_session_id(self):
        from ampro import SessionInitBody
        body = SessionInitBody(
            proposed_capabilities=["messaging"],
            proposed_version="1.0.0",
            client_nonce="nonce123",
            previous_session_id="old-sess-1",
        )
        assert body.previous_session_id == "old-sess-1"

    def test_session_init_previous_session_id_default_none(self):
        from ampro import SessionInitBody
        body = SessionInitBody(
            proposed_capabilities=["messaging"],
            proposed_version="1.0.0",
            client_nonce="nonce123",
        )
        assert body.previous_session_id is None

    def test_session_established_has_resumed(self):
        from ampro import SessionEstablishedBody
        body = SessionEstablishedBody(
            session_id="sess-new",
            negotiated_capabilities=["messaging"],
            negotiated_version="1.0.0",
            trust_tier="verified",
            trust_score=500,
            server_nonce="sn",
            binding_token="bt",
            resumed=True,
        )
        assert body.resumed is True

    def test_session_established_resumed_default_false(self):
        from ampro import SessionEstablishedBody
        body = SessionEstablishedBody(
            session_id="sess-fresh",
            negotiated_capabilities=["messaging"],
            negotiated_version="1.0.0",
            trust_tier="external",
            trust_score=100,
            server_nonce="sn",
            binding_token="bt",
        )
        assert body.resumed is False


class TestV013Imports:
    """Verify all v0.1.3 types are importable from ampro."""

    def test_agent_lifecycle_status_import(self):
        from ampro import AgentLifecycleStatus
        assert AgentLifecycleStatus.ACTIVE == "active"

    def test_agent_deactivation_notice_body_import(self):
        from ampro import AgentDeactivationNoticeBody
        body = AgentDeactivationNoticeBody(
            agent_id="agent://test.com",
            reason="Shutdown",
            deactivation_time="2026-04-09T00:00:00Z",
            active_sessions=0,
        )
        assert body.agent_id == "agent://test.com"

    def test_cost_receipt_import(self):
        from ampro import CostReceipt
        receipt = CostReceipt(
            agent_id="agent://a.com",
            task_id="t-1",
            cost_usd=0.01,
            issued_at="2026-04-09T00:00:00Z",
        )
        assert receipt.cost_usd == 0.01

    def test_cost_receipt_chain_import(self):
        from ampro import CostReceiptChain
        chain = CostReceiptChain()
        assert chain.total_cost_usd == 0.0

    def test_all_exports_count(self):
        import ampro
        assert len(ampro.__all__) >= 152


class TestV014Imports:
    """Verify all v0.1.4 types are importable from ampro."""

    def test_registry_search_request_import(self):
        from ampro import RegistrySearchRequest
        req = RegistrySearchRequest(capability="messaging")
        assert req.max_results == 10

    def test_registry_search_match_import(self):
        from ampro import RegistrySearchMatch
        match = RegistrySearchMatch(
            agent_id="agent://test.com",
            endpoint="https://test.com/agent/message",
            capabilities=["messaging"],
            trust_score=700,
            trust_tier="verified",
        )
        assert match.agent_id == "agent://test.com"

    def test_registry_search_result_import(self):
        from ampro import RegistrySearchResult
        result = RegistrySearchResult()
        assert result.matches == []
        assert result.total_available == 0

    def test_task_redirect_body_import(self):
        from ampro import TaskRedirectBody
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://alt.com",
            reason="overloaded",
        )
        assert body.task_id == "t-1"
        assert body.reason == "overloaded"

    def test_x_load_level_header(self):
        from ampro import STANDARD_HEADERS
        assert "X-Load-Level" in STANDARD_HEADERS

    def test_all_exports_v014_count(self):
        import ampro
        assert len(ampro.__all__) >= 156


class TestV015Imports:
    """Verify all v0.1.5 types are importable from ampro."""

    def test_trace_context_import(self):
        from ampro import TraceContext
        ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
        assert ctx.trace_id == "a" * 32

    def test_generate_trace_id_import(self):
        from ampro import generate_trace_id
        tid = generate_trace_id()
        assert len(tid) == 32

    def test_generate_span_id_import(self):
        from ampro import generate_span_id
        sid = generate_span_id()
        assert len(sid) == 16

    def test_inject_trace_headers_import(self):
        from ampro import inject_trace_headers, TraceContext
        ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
        headers = inject_trace_headers(ctx)
        assert "Trace-Id" in headers

    def test_extract_trace_context_import(self):
        from ampro import extract_trace_context
        result = extract_trace_context({})
        assert result is None

    def test_task_revoke_body_import(self):
        from ampro import TaskRevokeBody
        body = TaskRevokeBody(task_id="t-1", reason="revoked")
        assert body.task_id == "t-1"

    def test_priority_import(self):
        from ampro import Priority
        assert Priority.URGENT == "urgent"

    def test_trace_headers_in_standard_headers(self):
        from ampro import STANDARD_HEADERS
        assert "Trace-Id" in STANDARD_HEADERS
        assert "Span-Id" in STANDARD_HEADERS

    def test_all_exports_v015_count(self):
        import ampro
        assert len(ampro.__all__) >= 163


class TestV016Imports:
    """Verify all v0.1.6 types are importable from ampro."""

    def test_jurisdiction_info_import(self):
        from ampro import JurisdictionInfo
        info = JurisdictionInfo(primary="US")
        assert info.primary == "US"

    def test_validate_jurisdiction_code_import(self):
        from ampro import validate_jurisdiction_code
        assert validate_jurisdiction_code("US") is True

    def test_check_jurisdiction_conflict_import(self):
        from ampro import check_jurisdiction_conflict
        assert callable(check_jurisdiction_conflict)

    def test_erasure_propagation_status_import(self):
        from ampro import ErasurePropagationStatus
        assert ErasurePropagationStatus.PENDING == "pending"

    def test_erasure_propagation_status_body_import(self):
        from ampro import ErasurePropagationStatusBody
        body = ErasurePropagationStatusBody(
            erasure_id="er-1",
            agent_id="agent://test.com",
            status="completed",
            records_affected=5,
            timestamp="2026-04-09T00:00:00Z",
        )
        assert body.records_affected == 5

    def test_data_consent_revoke_body_import(self):
        from ampro import DataConsentRevokeBody
        body = DataConsentRevokeBody(
            grant_id="g-1",
            requester="agent://a.com",
            target="agent://b.com",
            reason="user request",
        )
        assert body.grant_id == "g-1"

    def test_data_residency_import(self):
        from ampro import DataResidency
        dr = DataResidency(region="eu-west-1")
        assert dr.region == "eu-west-1"

    def test_validate_residency_region_import(self):
        from ampro import validate_residency_region
        assert validate_residency_region("us-east-1") is True

    def test_check_residency_violation_import(self):
        from ampro import check_residency_violation
        assert callable(check_residency_violation)

    def test_jurisdiction_header(self):
        from ampro import STANDARD_HEADERS
        assert "Jurisdiction" in STANDARD_HEADERS

    def test_data_residency_header(self):
        from ampro import STANDARD_HEADERS
        assert "Data-Residency" in STANDARD_HEADERS

    def test_all_exports_v016_count(self):
        import ampro
        assert len(ampro.__all__) >= 173


class TestV017Imports:
    """Verify all v0.1.7 types are importable from ampro."""

    def test_stream_channel_import(self):
        from ampro import StreamChannel
        ch = StreamChannel(
            channel_id="ch-test",
            created_at="2026-04-09T12:00:00Z",
        )
        assert ch.channel_id == "ch-test"

    def test_stream_channel_open_event_import(self):
        from ampro import StreamChannelOpenEvent
        event = StreamChannelOpenEvent(
            channel_id="ch-open",
            task_id="t-1",
            created_at="2026-04-09T12:00:00Z",
        )
        assert event.channel_id == "ch-open"

    def test_stream_channel_close_event_import(self):
        from ampro import StreamChannelCloseEvent
        event = StreamChannelCloseEvent(channel_id="ch-close")
        assert event.reason == "complete"

    def test_stream_checkpoint_event_import(self):
        from ampro import StreamCheckpointEvent
        cp = StreamCheckpointEvent(
            checkpoint_id="cp-test",
            seq=0,
            timestamp="2026-04-09T12:00:00Z",
        )
        assert cp.state_snapshot == {}

    def test_stream_auth_refresh_event_import(self):
        from ampro import StreamAuthRefreshEvent
        event = StreamAuthRefreshEvent(
            method="jwt",
            token="tok",
            expires_at="2026-04-09T13:00:00Z",
        )
        assert event.method == "jwt"

    def test_stream_channel_header(self):
        from ampro import STANDARD_HEADERS
        assert "Stream-Channel" in STANDARD_HEADERS

    def test_streaming_event_type_count(self):
        from ampro import StreamingEventType
        assert len(StreamingEventType) == 17

    def test_all_exports_v017_count(self):
        import ampro
        assert len(ampro.__all__) >= 179
