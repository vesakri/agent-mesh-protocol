# Agent Mesh Protocol — v0.2.0 Security Audit (Retrospective)

> **Audited version**: v0.2.0 (2026-04-10)
> **Audit scope**: All 72 modules across all subpackages.
> **Status**: **All P0/P1 findings closed in v0.2.1. All 66 CRITICAL+HIGH findings closed in v0.2.3.** See `CHANGELOG.md` §0.2.1 and §0.2.3 for per-finding remediation.
>
> This document is retained as a historical record of the protocol's
> security-review process and as context for the retrospective
> findings summarised in `docs/SECURITY-AUDIT-V2.md`. It does **not**
> describe current (post-v0.2.3) protocol behaviour.

---

## Executive Summary (v0.2.0 snapshot)

At the time of this audit, the protocol's runtime security components
(trust resolution, session binding, dedup, rate limiting) had
exploitable vulnerabilities. Type definitions and models were
well-structured; runtime enforcement needed hardening. Findings are
listed below; see the re-audit (`SECURITY-AUDIT-V2.md`) for fix
effectiveness and the CHANGELOG for the final resolution in v0.2.3.

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Crypto & Auth | 5 | 4 | 3 | 2 |
| Injection & SSRF | 3 | 2 | 3 | 1 |
| Memory & DoS | 4 | 5 | 3 | 0 |
| Code Quality | 1 | 3 | 5 | 3 |
| **Total** | **13** | **14** | **14** | **6** |

---

## CRITICAL EXPLOITABLE CHAINS

### Chain 1: DID Proof Forgery → Full Auth Bypass
1. Attacker sends `Authorization: DID <forged-jwt-with-did:key:z6Mk...>`
2. `trust/resolver.py:_resolve_did()` accepts with ZERO signature verification
3. Attacker gains VERIFIED trust tier
4. Full access to all VERIFIED-tier operations

**Files**: `ampro/trust/resolver.py:109-111`, `ampro/identity/cross_verification.py:69-76`

### Chain 2: Memory Exhaustion → Server DoS (15 min)
1. Open 20K SSE streams (unique task_ids) → 400MB in stream bus
2. Open connections, never read → 2GB in asyncio queues
3. Send unique nonces → 3.6GB in nonce tracker
4. Rotate sender IDs → 5GB in rate limiter
5. **Total: 10+ GB in <15 minutes at 5K req/s**

**Files**: `ampro/streaming/bus.py`, `ampro/security/nonce_tracker.py`, `ampro/security/rate_limiter.py`, `ampro/security/dedup.py`

### Chain 3: SSRF via IPv6 Zone ID
1. Submit callback URL: `https://[::1%25eth0]/.well-known/agent.json`
2. Zone ID causes ValueError in ipaddress.ip_address()
3. Exception caught and silently ignored
4. URL passes validation → SSRF to localhost

**File**: `ampro/transport/attachment.py:51-54`

### Chain 4: Key Revocation Forgery → Account Lockout
1. Submit `KeyRevocationBody(agent_id="agent://victim", signature="fake")`
2. Signature field is NEVER validated by the module
3. Downstream code without validation revokes victim's key
4. Victim locked out

**File**: `ampro/security/key_revocation.py:64-66`

### Chain 5: RFC 9421 Signature Base Injection
1. Craft URL with newlines: `https://example.com/api\n"@authority": attacker`
2. URL inserted into signature base at `rfc9421.py:96` without escaping
3. Injects fake component into signature base
4. Attacker re-signs modified base → forged valid signature

**File**: `ampro/security/rfc9421.py:96`

---

## Detailed Findings

### 1. CRYPTO & AUTH

| # | Issue | Severity | File |
|---|-------|----------|------|
| C1 | DID proof accepted without signature verification | CRITICAL | trust/resolver.py:109-111 |
| C2 | Empty shared_secret produces predictable HMAC | CRITICAL | session/binding.py:60-86 |
| C3 | HMAC nonce concatenation lacks delimiter (collision) | CRITICAL | session/binding.py:81 |
| C4 | Key revocation signature never validated | CRITICAL | security/key_revocation.py:64-66 |
| C5 | JWKS revocation uses non-standard custom field | CRITICAL | transport/jwks_cache.py:39-42 |
| C6 | Trust resolver fails open to EXTERNAL (silent downgrade) | HIGH | trust/resolver.py:62-74 |
| C7 | API key store timing side-channel on dict lookup | HIGH | transport/api_key_store.py:29 |
| C8 | Same-org bypass: caller_org_id == target_org_id → INTERNAL | HIGH | trust/resolver.py:33-34 |
| C9 | Cross-verification did:key returns verified with no validation | HIGH | identity/cross_verification.py:69-76 |
| C10 | Nonce reuse across sessions possible (no uniqueness requirement) | MEDIUM | session/handshake.py |
| C11 | Clock skew 60s enables replay window | MEDIUM | trust/tiers.py:58 |
| C12 | DID base64 parsing has no length check (memory) | MEDIUM | trust/resolver.py:97-101 |
| C13 | Bearer token whitespace-only passes validation | LOW | identity/auth_methods.py:47-49 |
| C14 | API keys stored unhashed in memory | LOW | transport/api_key_store.py |

### 2. INJECTION & SSRF

| # | Issue | Severity | File |
|---|-------|----------|------|
| I1 | IPv6 zone ID bypasses SSRF validation | CRITICAL | transport/attachment.py:51-54 |
| I2 | IPv6 loopback ::1 vs [::1] string mismatch | CRITICAL | transport/attachment.py:37 |
| I3 | DNS rebinding: validate URL once, fetch later | CRITICAL | transport/callback.py:47-68 |
| I4 | RFC 9421 URL newline injection in signature base | HIGH | security/rfc9421.py:96 |
| I5 | Unvalidated moved_to, endpoint, consent_url fields | HIGH | agent/schema.py, registry/types.py, body_schemas.py |
| I6 | Malformed URL with None hostname bypasses validation | MEDIUM | transport/attachment.py:44-55 |
| I7 | Registry resolve URL no SSRF check | MEDIUM | core/addressing.py |
| I8 | Cross-verification fetches arbitrary agent.json URLs | MEDIUM | identity/cross_verification.py:91 |
| I9 | Chain budget regex potential ReDoS | LOW | delegation/chain.py:317 |

### 3. MEMORY & DoS

| # | Issue | Severity | File | Impact |
|---|-------|----------|------|--------|
| D1 | Dedup store unbounded | CRITICAL | security/dedup.py | 3GB @ 50K req/s |
| D2 | Nonce tracker unbounded (1hr window) | CRITICAL | security/nonce_tracker.py | 3.6GB @ 5K req/s |
| D3 | Stream bus unbounded + no cleanup | CRITICAL | streaming/bus.py | 5GB @ 100K streams |
| D4 | Slow consumer → unbounded asyncio queue | CRITICAL | streaming/bus.py:40-42 | 2GB @ 1K connections |
| D5 | Rate limiter unbounded per sender | HIGH | security/rate_limiter.py | 5GB @ 10M senders |
| D6 | Concurrency limiter no timeout (Slowloris) | HIGH | security/concurrency_limiter.py | Task slot starvation |
| D7 | Sender tracker unbounded | HIGH | security/sender_tracker.py | 150MB @ 1M senders |
| D8 | Scope narrowing O(n*m) algorithm | HIGH | delegation/chain.py:149-151 | CPU DoS |
| D9 | Backpressure advisory only (not enforced) | HIGH | streaming/backpressure.py | Server emits forever |
| D10 | Capability string parsing unbounded | MEDIUM | core/message_middleware.py:45 | 50MB parse |
| D11 | HandshakeStateMachine not thread-safe | MEDIUM | session/handshake.py:247-267 | Invalid state |
| D12 | ApiKeyStore.is_blocked() race condition | MEDIUM | transport/api_key_store.py:31-39 | KeyError crash |

### 4. CODE QUALITY

| # | Issue | Severity | File |
|---|-------|----------|------|
| Q1 | Duplicate JurisdictionInfo in two modules | HIGH | compliance/jurisdiction.py vs compliance/types.py |
| Q2 | TrustScore.tier is str, should be TrustTier enum | HIGH | trust/score.py:45 |
| Q3 | Multiple tier/status fields are str not enum | HIGH | session/handshake.py:84, trust/upgrade.py |
| Q4 | All 11 subpackage __init__.py are empty stubs | MEDIUM | all subpackages |
| Q5 | 12+ hardcoded constants need configuration | MEDIUM | multiple files |
| Q6 | Trust score factor values not validated (0-200) | MEDIUM | trust/score.py:47 |
| Q7 | No upper bound on SessionConfig.max_messages | MEDIUM | session/types.py:44 |
| Q8 | Inconsistent error message format | MEDIUM | multiple files |
| Q9 | AgentAddress.raw not validated on construction | MEDIUM | core/addressing.py:29 |
| Q10 | Error messages inconsistent (ValueError vs ValidationError) | LOW | multiple |
| Q11 | ChallengeReason used as str not enum in body | LOW | security/challenge.py |
| Q12 | Priority enum exists but body_schemas uses Literal | LOW | core/priority.py vs body_schemas.py |

---

## Fix Priority

### P0: Must fix before any deployment
1. DID proof signature verification (C1)
2. Empty shared_secret rejection (C2)
3. HMAC delimiter (C3)
4. Bounded dedup/nonce/rate limiter (D1, D2, D5)
5. IPv6 SSRF bypass (I1, I2)
6. Stream bus bounded queue + cleanup (D3, D4)

### P1: Must fix before multi-agent deployment
7. Key revocation signature validation (C4)
8. DNS rebinding prevention (I3)
9. RFC 9421 URL injection (I4)
10. Thread-safe state machine (D11)
11. Concurrency limiter timeout (D6)
12. URL field validation (I5)

### P2: Should fix before scale deployment
13. JWKS revocation standard compliance (C5)
14. Trust resolver fail-closed (C6)
15. Duplicate JurisdictionInfo consolidation (Q1)
16. Type safety (TrustTier enum usage) (Q2, Q3)
17. Subpackage __init__.py exports (Q4)
18. Configuration extraction (Q5)
