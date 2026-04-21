# AMP Security Model

> Status: pre-1.0. This document captures what the **protocol** guarantees,
> what it explicitly does **not** guarantee, and what a host platform MUST
> provide to make an AMP deployment safe to run in production. Everything
> below is RFC 2119 normative when written in **MUST / SHOULD / MAY**.

AMP is a wire protocol for agent-to-agent communication. A protocol
defines *envelopes, types, and verification rules* — not operational
concerns like key storage, certificate issuance, or network hygiene.
Those are the host platform's job. The protocol draws a firm line
between the two, and this document is where the line is documented.

---

## What the protocol guarantees

1. **Message integrity.** Every signed envelope is bound to its
   content-digest (RFC 9530) and covered components (RFC 9421). Any
   tampering flips the signature to invalid.

2. **Sender authentication.** If the caller registers a
   `PublicKeyResolver`, signatures are verified against the resolved
   key bytes using Ed25519. No resolver ⇒ fail closed.

3. **Replay protection.** `verify_request` rejects signatures whose
   `created` timestamp is outside a bounded freshness window (default
   300 s). Callers that need per-request uniqueness pass a
   `NonceTracker`; reused nonces fail closed. See
   `ampro/security/rfc9421.py`.

4. **Revocation propagation.** `ampro.trust.resolver.get_public_key`
   consults the registered `RevocationStore` before returning bytes,
   on every call — cache hits included. A key the host marks revoked
   stops verifying immediately. See `ampro/security/key_revocation.py`.

5. **Structural validation.** Envelopes, addresses, trust proofs,
   delegation chains, cost receipts, erasure responses, and registry
   syncs all use typed Pydantic models with length caps and
   content-constraint validators. Malformed input is rejected before
   it reaches application code.

6. **Deterministic wire binding.** The test vectors under
   `tests/vectors/` pin the canonical byte representation of every
   protocol artefact, so independent implementations (Go / Rust / TS)
   can agree on what bytes to sign.

---

## What the protocol explicitly does NOT guarantee

Each item below is a deliberate design choice — not a bug and not a
roadmap item. Deployers MUST read this list before shipping AMP to
production.

### 1. Trust anchoring (self-attesting origin)

A signed envelope proves *"the holder of the private key matching
`sig_kid` sent this"*. It does **not** prove *"this `sig_kid` belongs
to the principal the sender claims to be"*. That binding comes from
the `PublicKeyResolver` the host registers, and the protocol takes it
on faith.

Production deployments SHOULD back the resolver with one of:

- **DNS-anchored JWKS** (resolver fetches from
  `https://<domain>/.well-known/amp/jwks.json`, verifies TLS chain).
- **Certificate Transparency-style log** (resolver refuses keys not
  present in an append-only log witnessed by independent auditors).
- **did:web / did:key with rotation proofs** — see
  `ampro.identity.migration` for the protocol-level primitive.
- **Private key directory** (org-scoped, operated by a party the
  relying agent trusts directly).

Until one of these is in place, an attacker who controls the resolver
controls the entire trust graph. The protocol ships no opinion on
which mechanism you pick — that's an ecosystem decision.

### 2. Key storage, rotation, and hardware isolation

The protocol accepts a 32-byte Ed25519 private key and signs with it.
It does not say where that key should live. In particular:

- Keeping a long-lived private key in process memory is **fine for
  demos, unsafe for production**. Process memory is readable by
  anything running as the same UID, survives core dumps, and can leak
  through swap.
- Production deployments SHOULD back the signer with an HSM, a TEE
  (e.g. AWS Nitro, GCP Confidential VMs), a KMS with per-request
  signing (AWS KMS, GCP Cloud KMS), or at minimum a kernel keyring
  with restricted process access.
- Rotation frequency is a host policy. The protocol provides
  `KeyRevocationBody` + `KeyRevocationBroadcastBody` so a rotated key
  can be announced across the mesh; using them is up to the host.

### 3. Encryption at the protocol layer

AMP does not encrypt envelope payloads by default. Confidentiality in
transit is delegated to the underlying transport — typically TLS 1.3.
This is a conscious choice so that:

- Intermediaries (relays, load balancers) can route without
  decrypting.
- Operators can MITM their own traffic for debugging and audit with
  their own TLS termination.
- The protocol does not become another key-management surface.

When confidentiality *must* survive a compromised transport — e.g.
delegation to an untrusted relay — callers use `EncryptedBody` from
`ampro.security.encryption` to wrap the payload with an ephemeral
symmetric key negotiated via `EncryptionKeyOfferBody` /
`EncryptionKeyAcceptBody`. This is opt-in, per-message, and the
`SessionContext.session_requires_encryption` flag lets a session
enforce that every envelope be encrypted (anti-downgrade).

Deployers MUST either:
- run AMP exclusively over TLS 1.3 with verified peer certificates, or
- set `session_requires_encryption=True` and negotiate encryption at
  session start.

### 4. Denial of service

The protocol provides primitives — `RateLimiter`, `ConcurrencyLimiter`,
`NonceTracker`, `InMemoryDedupStore` — all with bounded memory. It
does **not** orchestrate them. Wiring rate limits onto a specific
handler, choosing quotas, and shedding load under pressure are host
responsibilities.

### 5. Cross-jurisdiction compliance

`ampro.compliance` ships typed models for adequacy decisions, data
residency, retention policy, and erasure responses. It does **not**
know your jurisdictions' current rules. The host is responsible for
populating `AdequacyDecision` records and keeping them current as
regulators change positions.

### 6. Side channels

Ed25519 via `cryptography` is constant-time for the private-key
operation. The protocol does **not** otherwise attempt side-channel
hardening: string comparisons in header parsing are not constant-time,
and revoked-key lookups are not blinded. Hosts that care about
timing attacks should run AMP behind a reverse proxy that normalises
response timing.

---

## Host platform checklist

A platform shipping AMP to production MUST provide:

- [ ] A `PublicKeyResolver` whose trust root is **externally verifiable**
      (DNS + TLS, CT log, did:web, etc.). Never ship with an in-memory
      directory in production.
- [ ] A `RevocationStore` backed by durable shared storage (KV / DB)
      so every verifier converges on the revoked set within a bounded
      staleness window.
- [ ] A signing surface (HSM / KMS / keyring) that the Python process
      can call — not a raw `bytes` object passed around in memory.
- [ ] TLS 1.3 at every hop, with verified peer certificates, **or**
      session-level encryption via `session_requires_encryption=True`.
- [ ] Rate limits wired onto every ingress handler, sized to the
      platform's tenancy model.
- [ ] A logging pipeline that captures rejected signatures, revocation
      hits, and rate-limit trips so operators can detect attacks.

The protocol does its share. The platform MUST do its share.

---

## Reporting a vulnerability

See `SECURITY.md` in the repository root. Coordinated disclosure,
90-day embargo window, GPG key for encrypted reports.
