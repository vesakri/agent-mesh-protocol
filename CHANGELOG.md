# Changelog

## [0.2.2] - 2026-04-10

### Added
- Reference server (`ampro/server/`) — minimal AMP agent in 10 lines
  - `AgentServer` class with `@server.on()` decorator pattern
  - Framework-agnostic `route()` method + FastAPI/Flask adapters
  - Auto-generated agent.json, health, SSE placeholder
  - RFC 7807 error responses on validation failure
- Client SDK (`ampro/client/`) — talk to any AMP agent
  - `send()` — one-shot message like httpx.post()
  - `discover()` — fetch agent capabilities
  - `stream()` — SSE streaming with reconnection
  - `connect()` — 3-phase handshake session with auto-binding
  - `AmpProtocolError` wrapping RFC 7807 responses
- 10 implementation guidance examples (31-40)
  - Server: simple, tools, auth, sessions, streaming
  - Client: send, handshake, streaming
  - Integration: two agents talking, delegation chain with costs

## [0.2.1] - 2026-04-10

### Security Fixes
- DID proof now fail-closed (returns EXTERNAL instead of VERIFIED without signature verification)
- Session binding rejects empty shared_secret
- HMAC nonce concatenation uses null byte delimiter to prevent collisions
- Key revocation now includes `validate_revocation_signature()` helper
- JWKS revocation check has defensive type validation
- Trust resolver logs at WARNING on failure (was DEBUG)
- API key validation uses constant-time comparison (hmac.compare_digest)
- Cross-verification did:key returns fail-closed until key extraction implemented
- Bearer token whitespace-only now correctly rejected
- DID base64 payload has length limit (10KB)
- RFC 9421 rejects URLs with newlines (signature base injection)
- IPv6 zone ID stripped before SSRF validation
- IPv6 loopback ::1 added to private hosts
- Empty hostname URLs now rejected
- Chain budget regex pre-compiled with non-backtracking pattern

### DoS Protection
- Dedup store bounded to 100K entries with LRU eviction
- Nonce tracker bounded to 100K entries with LRU eviction
- Rate limiter bounded to 100K senders with stale eviction
- Sender tracker bounded to 100K senders with eviction
- Stream bus bounded to 10K active streams
- Streaming queue bounded to 1K events (drops on overflow)
- Scope narrowing limited to 100 scopes per link
- Capability string parsing limited to 50 entries
- HandshakeStateMachine now thread-safe (threading.Lock)
- ApiKeyStore.is_blocked() race condition fixed (pop vs del)

### Code Quality
- Duplicate JurisdictionInfo renamed to ComplianceJurisdictionInfo in compliance/types.py
- TrustScore.tier validated against valid tier values
- TrustScore.factors validated (0-200 per factor)
- SessionConfig.max_messages capped at 10,000
- All 11 subpackage __init__.py files now re-export their contents with __all__
- Trust tier field descriptions updated across handshake and upgrade modules

## [0.2.0] - 2026-04-10

### Changed (BREAKING)
- **Package reorganized into subdirectories.** Modules moved from flat `ampro/*.py` into 11 subpackages: `core/`, `trust/`, `session/`, `identity/`, `delegation/`, `streaming/`, `security/`, `compliance/`, `registry/`, `agent/`, `transport/`
- Direct submodule imports (e.g. `from ampro.trust_score import ...`) must update to new paths (e.g. `from ampro.trust.score import ...`)
- **Public API unchanged.** `from ampro import X` still works for all 187 exports

### Migration Guide
| Old import | New import |
|------------|-----------|
| `from ampro.trust_score import ...` | `from ampro.trust.score import ...` |
| `from ampro.body_schemas import ...` | `from ampro.core.body_schemas import ...` |
| `from ampro.streaming import ...` | `from ampro.streaming.events import ...` |
| `from ampro.envelope import ...` | `from ampro.core.envelope import ...` |
| `from ampro import X` | `from ampro import X` (unchanged) |

See the full mapping in CONTRIBUTING.md.

## [0.1.9] - 2026-04-10

### Added
- `EncryptedBody` model + `CONTENT_ENCRYPTION_HEADER` — end-to-end JWE encryption
- `Content-Encryption` header
- `trust.proof` body type (`TrustProofBody`) — zero-knowledge trust proofs
- `CertificationLink` model + `certifications` array in `AgentJson`

### Changed
- Standard headers grew from 50 to 51
- Body type registry grew from 48 to 49
- Exports grew from 184 to 188

## [0.1.8] - 2026-04-10

### Added
- `identity.link_proof` body type — cryptographic proof two addresses are the same entity
- `registry.federation_request` / `registry.federation_response` body types — inter-registry trust
- `identity.migration` body type — agent address migration with proof
- `audit.attestation` body type — signed proof both parties agree on session events
- `moved_to` field on `AgentJson` — migration redirect pointer

### Changed
- Body type registry grew from 43 to 48
- Exports grew from 179 to 184

## [0.1.7] - 2026-04-09

### Added
- `StreamChannel` / `StreamChannelOpenEvent` / `StreamChannelCloseEvent` — stream multiplexing
- `StreamCheckpointEvent` — periodic state snapshots for reconnection
- `StreamAuthRefreshEvent` — mid-stream JWT renewal
- `Stream-Channel` header
- 4 new streaming event types (channel_open, channel_close, checkpoint, auth_refresh)

### Changed
- Standard headers grew from 49 to 50
- Streaming event types grew from 13 to 17
- Exports grew from 174 to 179+

## [0.1.6] - 2026-04-09

### Added
- `JurisdictionInfo` model + `validate_jurisdiction_code` + `check_jurisdiction_conflict` — cross-border jurisdiction declaration
- `Jurisdiction` + `Data-Residency` headers
- `erasure.propagation_status` body type — track erasure across delegation chains
- `data.consent_revoke` body type — revoke previously granted consent
- `DataResidency` model + `validate_residency_region` + `check_residency_violation`
- `ErasurePropagationStatus` enum (pending, completed, failed)
- `DataConsentRequestBody` + `DataConsentResponseBody` now exported from top-level

### Changed
- Standard headers grew from 47 to 49
- Body type registry grew from 41 to 43
- Exports grew from 163 to 174

## [0.1.5] - 2026-04-09

### Added
- `TraceContext` model + `generate_trace_id` / `generate_span_id` / `inject_trace_headers` / `extract_trace_context` — W3C Trace Context for delegation chains
- `task.revoke` body type (`TaskRevokeBody`) — revoke tasks with cascade and revoke_children flags
- `Priority` enum (batch, normal, priority, urgent, critical) — standardized priority levels
- `Trace-Id` + `Span-Id` headers

### Changed
- Standard headers grew from 45 to 47
- Body type registry grew from 40 to 41
- Exports grew from 156 to 163

## [0.1.4] - 2026-04-09

### Added
- `RegistrySearchRequest` / `RegistrySearchMatch` / `RegistrySearchResult` — structured service discovery
- `task.redirect` body type (`TaskRedirectBody`) — load-aware task redirection
- `X-Load-Level` header — agent load percentage (0-100)

### Changed
- Standard headers grew from 44 to 45
- Body type registry grew from 39 to 40
- Exports grew from 152 to 156

## [0.1.3] - 2026-04-09

### Added
- `agent.deactivation_notice` body type — orderly shutdown notification
- `AgentLifecycleStatus` enum (active, deactivating, decommissioned)
- `CostReceipt` + `CostReceiptChain` models — per-hop cost attribution in delegation chains
- `cost_receipt` field on `TaskCompleteBody`
- `Hop-Timeout` header — per-hop timeout declaration
- `status` field on `AgentJson` (active/deactivating/decommissioned)
- `status` + `gone` fields on `RegistryResolution` — 410 Gone support

### Changed
- Standard headers grew from 43 to 44
- Body type registry grew from 38 to 39
- Exports grew from 148 to 152+

## [0.1.2] - 2026-04-09

### Added
- `key.revocation` body type + `Key-Revoked-At` header — emergency key revocation broadcast
- `task.challenge` / `task.challenge_response` body types — anti-abuse challenge mechanism
- `tool.consent_request` / `tool.consent_grant` body types + `ToolDefinition` model — per-tool consent
- `stream.ack` / `stream.pause` / `stream.resume` streaming event types — backpressure flow control
- `trust.upgrade_request` / `trust.upgrade_response` body types — mid-conversation identity verification
- `Anonymous-Sender-Hint` header — pseudonymous rate limiting
- `previous_session_id` field on `SessionInitBody` — session resumption
- `resumed` field on `SessionEstablishedBody` — resumption status
- `RevocationReason` enum (key_compromise, key_rotation, agent_decommissioned)
- `ChallengeReason` enum (first_contact, suspicious_behavior, rate_limit_exceeded, trust_upgrade)
- 5 new test vector files, 4 new examples, 75 new tests

### Changed
- Standard headers grew from 41 to 43
- Streaming event types grew from 10 to 13
- Body type registry grew from 31 to 38
- Exports grew from 135 to 148+

## [0.1.1] - 2026-04-09

### Added
- 3-phase session handshake (session.init → session.established → session.confirm)
- 8 session body types: init, established, confirm, ping, pong, pause, resume, close
- HandshakeStateMachine with 8 states and validated transitions
- HMAC-SHA256 session binding (derive_binding_token, create/verify message binding)
- Trust scoring: 5-factor numeric score (0-1000) with tier mapping
- TrustPolicy: score-based rate limits and content filter policy
- Visibility control: 4 levels (public, authenticated, private, hidden)
- Contact policies: 5 levels (open, handshake_required, verified_only, delegation_only, explicit_invite)
- agent.json conditional filtering based on caller trust tier
- Context schema URN parsing and matching (urn:namespace:name:version)
- 6 new standard headers: Session-Binding, Trust-Score, Context-Schema, Transaction-Id, Correlation-Group, Commitment-Level
- AgentJson: visibility and supported_schemas fields
- 9 language-agnostic test vector files (tests/vectors/)
- 3 new examples: handshake, visibility, context schema

### Changed
- SessionState expanded from 4 to 8 states (added IDLE, INIT_SENT, INIT_RECEIVED, ESTABLISHED)
- Standard headers grew from 35 to 41
- Exports grew from ~108 to ~125+

## [0.1.0] - 2026-04-08

### Added
- `agent://` URI addressing with 3 forms (host, registry slug, DID)
- 23 body type schemas with Pydantic validation
- Multi-method authentication (JWT, DID, API key, mTLS)
- 4-tier trust resolution chain
- Ed25519 delegation chains with clock skew, fan-out, budget enforcement
- SSE streaming with heartbeat, sequencing, replay
- GDPR compliance (PII classification, audit hash-chain, erasure)
- Security: dedup, nonce, rate limiting, concurrency cap, poison message protection
- JWKS caching with key rotation and revocation
- Identifier cross-verification
- Capability negotiation with 8 groups, 6 levels
- Version negotiation with Accept-Version preference lists

### Changed
- Complete rewrite from v0.1.0 to match Agent OS Protocol spec
- `body_type` field added to AgentMessage (MUST per spec)
- 35 standard headers (was 15)
- 10 streaming event types (was 9, added heartbeat)
- `Visited-Spaces` renamed to `Visited-Agents`

### Removed
- `AgentCard` (replaced by `AgentJson`)
- `Endpoints` class (replaced by spec Section 9.5)
- `BodyStatus` enum (replaced by body type schemas)
