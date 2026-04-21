# AMP Protocol Contracts

Normative semantic contracts the protocol defines. Read alongside
`docs/WIRE-BINDING.md` (HTTP binding).

This document covers contract-level behaviour that transcends any
single body schema: error classification, schema evolution rules,
event ordering, federation sync, multi-jurisdiction precedence, and
cache invalidation. Each section uses RFC 2119 language (MUST,
SHOULD, MAY) for normative requirements.

## 1. Error handling strategy

AMP errors fall into three tiers; implementations MUST preserve the
distinction so that middleware, observability pipelines, and retry
policies can route each tier correctly.

| Tier | When | Example | Expected handling |
|------|------|---------|-------------------|
| **Envelope silent** | Unknown body_type, unknown header | old receiver sees new message | Receiver MUST ignore; forward compatibility |
| **Body validation** | Body schema fails | `task.create` missing `description` | Raise `ValidationError`; return RFC 7807 response with HTTP 400 |
| **Addressing / trust** | Malformed URI, revoked key | `agent://invalid` or expired JWT | Raise `AmpError`-family exception; return 400 or 401 |

**Envelope silent** errors do NOT raise. They are the backbone of
forward compatibility: a v0.3 receiver seeing a v0.4 envelope with
unknown headers or an unknown `body_type` MUST drop-or-ignore
gracefully, never 500. Senders SHOULD NOT rely on receivers
processing unknown types.

**Body validation** errors MUST produce RFC 7807 problem responses
(`application/problem+json`) with HTTP 400. The `detail` field
SHOULD identify the offending body type and field.

**Addressing / trust** errors MUST produce HTTP 400 (malformed
address) or HTTP 401 (authentication/authorization). Implementations
SHOULD unify these under a base exception class (see
`ampro.errors.AmpError`) so middleware can catch all protocol
failures uniformly.

## 2. Schema evolution

AMP uses forward-compatible schemas. Every body type uses
`model_config = {"extra": "ignore"}` — unknown fields are tolerated.

**Allowed without version bump (MINOR-safe):**
- Adding optional fields to a body
- Adding new body types (receivers MUST ignore unknown types)
- Adding new headers (receivers MUST ignore unknown headers)
- Adding new streaming event types
- Adding new enum values (receivers MUST treat unknown enum values
  as a neutral default or reject with a body-validation error;
  see the per-field docs)

**NOT allowed without MAJOR version bump:**
- Adding a required field to an existing body
- Removing a body type, header, or field
- Changing the semantic meaning of an existing field
- Changing the wire format (JSON type) of an existing field
- Narrowing the domain of an enum or `Literal`

Receivers MUST tolerate unknown keys. Senders SHOULD NOT emit
unknown keys unless they are documented as extensions (see the
`X-AMP-Ext-*` header convention in `docs/WIRE-BINDING.md`).

The authoritative protocol version is exposed on every envelope as
`protocol_version`. Consumers SHOULD log mismatches but MUST NOT
reject based on version alone unless the MAJOR component differs.

## 3. Event ordering across channels

Within a single channel, events are delivered in `seq` order
(monotonic, server-assigned). Gaps in `seq` signal lost frames;
receivers MUST treat a gap as a fatal channel error and re-sync
from the last acknowledged checkpoint.

Across channels, there is **no global ordering guarantee** unless
both events carry a `cross_channel_seq` value scoped to the session.

Receivers that need causal ordering MUST:
- Set `cross_channel_seq` on every event they emit, OR
- Use session-level checkpoints to synchronize channels

Implementations SHOULD document their ordering guarantees in their
`agent.json` under `capabilities.streaming.ordering`. Values:
`per_channel` (default), `session_wide`, or `none`.

## 4. Federation sync semantics

Registries federate via pull-based sync (`registry.federation_sync`):

- Consumer polls source registry with `since` timestamp + optional
  cursor
- Source returns delta: list of agent-record changes + next cursor
- Consumer applies changes to its local view
- Conflicts resolved via `resolve_federation_conflict` precedence
  (trust → recency → deterministic URI)

Eventual consistency is the model. No strong consistency
guarantees between registries. Implementations SHOULD surface the
last successful sync timestamp on every registry query so callers
can reason about staleness.

See `ampro.registry.federation.RegistryFederationSyncBody` for the
on-wire shape, and `docs/WIRE-BINDING.md#federation` for the HTTP
binding.

## 5. Multi-jurisdiction precedence

When an agent operates in multiple jurisdictions (primary +
additional), the strictest-rule principle applies:

- Data originating in `primary` → primary jurisdiction rules
- Data originating in an `additional` jurisdiction → union of
  (additional ∩ primary) rules, with the strictest requirement
  winning
- Unknown origin → primary

The helper `ampro.compliance.jurisdiction.applicable_rules(info,
data_region)` returns the ordered list of jurisdictions whose rules
apply; implementations SHOULD compute the union of their
constraints and apply the strictest.

Implementations SHOULD surface the applicable jurisdiction set on
every message carrying personal data via headers:

- `Jurisdiction-Primary: DE`
- `Jurisdiction-Additional: FR, IT`
- `Jurisdiction-Data-Region: FR` (origin of the data being
  transmitted)

Cross-border transfers (sender primary ≠ receiver primary) MUST be
evaluated against a registered transfer mechanism (adequacy
decision, BCR, SCC, derogation). See
`ampro.compliance.jurisdiction.check_cross_border_transfer` and
`register_adequacy_registry`. The default `NoOpAdequacyRegistry`
rejects all cross-border transfers, so host platforms MUST install a
concrete registry before enabling cross-border routing.

## 6. Cache invalidation

`agent.json` is cached per `Cache-Control` TTL. Protocol additions in
v0.3.x add push-style invalidation on top of TTL-based polling:

- `agent.metadata_invalidate` body: push notification that a cached
  copy is stale. Receivers MUST drop the cached copy on receipt.
  See `ampro.agent.schema::AgentMetadataInvalidateBody`.
- `KeyRevocationBroadcastBody`: push notification that a public key
  is revoked. Receivers MUST drop cached keys on receipt and
  fail-closed on any in-flight verification that depended on the
  revoked key.
- Compliance-driven invalidations (e.g. after an erasure
  propagation) MAY reuse the same push flow; see
  `ampro.compliance.erasure_propagation::ErasurePropagationStatusBody`
  for the retry semantics these notifications interact with.

Push-based invalidations are best-effort. TTL-based polling remains
the authoritative fallback: implementations MUST continue to honour
`Cache-Control: max-age` on every cached agent descriptor.

## 7. Retry and idempotency

Receivers MUST treat envelopes as idempotent keyed by
`envelope.id`. A duplicate envelope with the same id MUST produce
the same observable result as the first delivery. Senders retrying
after a network failure MUST reuse the original envelope id.

Retries MUST use exponential backoff with jitter. The compliance
module exposes a canonical helper
(`ampro.compliance.erasure_propagation.compute_next_retry`); other
modules SHOULD follow the same shape. Retry budgets are
per-envelope: implementations SHOULD cap total retries at 30 and
mark the envelope `final` on exhaustion.

## 8. References

- `docs/WIRE-BINDING.md` — HTTP binding for the contracts above.
- `docs/SPEC.md` — canonical body and envelope schemas.
- `docs/PROTOCOL-ROADMAP.md` — scheduled contract changes.
- `docs/EDGE-CASES.md` — edge cases and corner behaviours that
  depend on the contracts above.
