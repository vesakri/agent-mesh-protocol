# Test Vectors

These JSON files are conformance test vectors used by the test suite to validate
AMP protocol implementations. They exist as portable cross-implementation
references — a Go or TypeScript implementation can re-use them to verify
behavioural equivalence with the Python reference.

## Format

Each vector is a self-describing JSON object. Top-level keys typically include:

- `description` — what the vector exercises
- `vectors` — list of individual test cases (name, input, expected output, notes)
- `parse_vectors` / `match_vectors` — split sections for parsers vs matchers
- `$schema`, `title` — optional JSON Schema metadata

Individual cases generally carry `name`, `input` (the protocol message or
operation), `expected` or `valid` (required decision / output), plus free-form
`notes` and (where relevant) an `rfc` or AMP version reference.

## Index

Thirty-four vectors, grouped by protocol surface. The `Test` column names the
Python test file that covers the same surface (and, in most cases, the
behaviour the vector encodes); cross-implementation runners should re-implement
equivalent assertions against the JSON.

| Vector | Protocol Surface | Test |
|--------|------------------|------|
| addressing.json | Agent address parsing (AMP URIs) | tests/test_wire.py |
| agent_lifecycle.json | Agent lifecycle status + `agent.deactivation_notice` body (v0.1.3) | tests/test_agent_lifecycle.py |
| audit_attestation.json | `AuditAttestationBody` / `body.type = audit.attestation` (v0.1.8) | tests/test_audit_attestation.py |
| backpressure.json | `stream.ack` / `stream.pause` / `stream.resume` events (v0.1.2) | tests/test_backpressure.py |
| body_types.json | Body type validation across all body kinds | tests/test_protocol.py |
| certifications.json | `CertificationLink` in `agent.json` (v0.1.9) — SOC2, ISO27001, etc. | tests/test_certifications.py |
| challenge.json | `task.challenge` + `task.challenge_response` (v0.1.2) | tests/test_challenge.py |
| consent_revoke.json | `DataConsentRevokeBody` / `body.type = data.consent_revoke` (v0.1.6) | tests/test_consent_revoke.py |
| context_schema.json | Context schema URN parse + match | tests/test_context_schema.py |
| cost_receipt.json | `CostReceipt`, `CostReceiptChain`, `task.complete.cost_receipt` (v0.1.3) | tests/test_cost_receipt.py |
| data_residency.json | `DataResidency`, `validate_residency_region`, `check_residency_violation` (v0.1.6) | tests/test_data_residency.py |
| delegation_chain.json | Delegation chain validation | tests/delegation/test_cost_receipt_signatures.py |
| encryption.json | `EncryptedBody` + `Content-Encryption` header (v0.1.9) | tests/test_encryption.py |
| envelope.json | Message envelope validation | tests/test_protocol.py |
| erasure_propagation.json | `ErasurePropagationStatusBody` / `erasure.propagation_status` (v0.1.6) | tests/test_erasure_propagation.py |
| handshake.json | Complete handshake sequence | tests/test_handshake.py |
| headers.json | Standard AMP headers (set + examples) | tests/test_client.py |
| identity_link.json | `IdentityLinkProofBody` / `identity.link_proof` (v0.1.8) | tests/test_identity_link.py |
| identity_migration.json | `IdentityMigrationBody` + `AgentJson.moved_to` (v0.1.8) | tests/test_identity_migration.py |
| jurisdiction.json | `JurisdictionInfo`, `validate_jurisdiction_code`, conflict checks (v0.1.6) | tests/test_jurisdiction.py |
| key_revocation.json | `key.revocation` body (v0.1.2) — all 3 revocation reasons | tests/test_key_revocation.py |
| priority.json | `Priority` enum (v0.1.5) — 5 valid values + invalids | tests/test_priority.py |
| registry_federation.json | `RegistryFederationRequest` / `Response` (v0.1.8) | tests/test_registry_federation.py |
| registry_search.json | `RegistrySearchRequest` / `Match` / `Result` (v0.1.4) | tests/test_registry_search.py |
| stream_channel.json | Stream channel open / close / multiplexing events (v0.1.7) | tests/test_stream_channel.py |
| stream_checkpoint.json | Stream checkpoint + reconnection events (v0.1.7) | tests/test_stream_checkpoint.py |
| task_redirect.json | `TaskRedirectBody` + `X-Load-Level` header (v0.1.4) | tests/test_task_redirect.py |
| task_revoke.json | `TaskRevokeBody` — cascade / revoke_children flags (v0.1.5) | tests/test_task_revoke.py |
| tool_consent.json | `tool.consent_request` + `tool.consent_grant` (v0.1.2) | tests/test_tool_consent.py |
| tracing.json | `TraceContext` + `inject_trace_headers` (v0.1.5) | tests/test_tracing.py |
| trust_proof.json | `TrustProofBody` / `trust.proof` ZKP proofs (v0.1.9) | tests/test_trust_proof.py |
| trust_scoring.json | Trust score calculation | tests/test_trust_score.py |
| trust_upgrade.json | `trust.upgrade_request` + `trust.upgrade_response` (v0.1.2) | tests/test_trust_upgrade.py |
| visibility.json | Visibility + contact policy (filters) | tests/test_visibility.py |

## Using these vectors from a non-Python implementation

1. Load the JSON file.
2. For each entry in `vectors` (or `parse_vectors` / `match_vectors`), feed
   `input` into the equivalent parser / validator in your language.
3. Assert the observed output matches `expected` (or `valid` boolean where the
   vector is a negative case).
4. If a case lists an `rfc` / AMP version, gate the assertion on your
   implementation's supported version.

## Adding a new vector

- Place the file here as `<surface>.json`.
- Include a top-level `description` and AMP version the vectors target.
- Add a row to the Index above (keep rows alphabetised).
- Exercise it from the matching Python test so regressions in the reference
  implementation surface immediately.
