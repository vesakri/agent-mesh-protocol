# Changelog

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
