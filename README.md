# Agent Mesh Protocol - Agent to Agent Communication

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/version-0.1.1-green.svg)](CHANGELOG.md)

The universal agent-to-agent communication protocol. Any agent, any runtime, any platform.

```
pip install ampro
```

## What Is This?

Agent Protocol defines **how agents talk to each other** -- not how they're built. A Raspberry Pi agent, a cloud-hosted AI, and an enterprise bot all speak the same wire format.

The protocol answers four questions:
- **Can I reach you?** -- `agent://` addressing
- **Can I trust you?** -- 4-tier trust (internal/owner/verified/external)
- **What can you do?** -- 8 capability groups, 6 progressive levels
- **How do we talk?** -- `POST /agent/message` with typed body schemas

## Quick Start -- Minimum Viable Agent (30 Lines)

```python
from flask import Flask, request, jsonify
from uuid import uuid4

app = Flask(__name__)

@app.route('/.well-known/agent.json')
def agent_json():
    return jsonify({
        "protocol_version": "1.0.0",
        "identifiers": ["agent://my-agent.local"],
        "endpoint": "https://my-agent.local/agent/message",
        "capabilities": {"groups": ["messaging"], "level": 1},
        "constraints": {"max_concurrent_tasks": 1}
    })

@app.route('/agent/message', methods=['POST'])
def message():
    msg = request.json
    return jsonify({
        "sender": "agent://my-agent.local",
        "recipient": msg["sender"],
        "id": str(uuid4()),
        "body_type": "task.response",
        "headers": {"Protocol-Version": "1.0.0", "In-Reply-To": msg["id"]},
        "body": {"text": "Hello from my agent!"}
    })
```

That's a fully protocol-compliant Level 1 agent.

## Addressing -- `agent://`

Three forms, one scheme:

```python
from ampro import parse_agent_uri

# Direct host
addr = parse_agent_uri("agent://bakery.com")

# Registry slug
addr = parse_agent_uri("agent://sunny-bakery@registry.example.com")

# Decentralized identity
addr = parse_agent_uri("agent://did:key:z6MkhaXgBZDvot...")
```

## Trust -- 4 Tiers

```python
from ampro import TrustTier, TrustConfig

config = TrustConfig.from_tier(TrustTier.EXTERNAL)
print(config.check_auth)           # True
print(config.check_rate_limit)     # True
print(config.check_content_filter) # True

# EXTERNAL cannot delegate
print(TrustTier.EXTERNAL.can_delegate)  # False
print(TrustTier.VERIFIED.can_delegate)  # True
```

## Capabilities -- 8 Groups, 6 Levels

```python
from ampro import CapabilityGroup, CapabilitySet

caps = CapabilitySet(groups={
    CapabilityGroup.MESSAGING,
    CapabilityGroup.TOOLS,
    CapabilityGroup.STREAMING,
})
print(f"Level: {caps.level}")  # Level: 3
```

## Body Types -- 23 Typed Schemas

```python
from ampro import validate_body

# Validated against Pydantic schema
body = validate_body("task.create", {
    "description": "Check cake availability",
    "priority": "high",
})
print(body.description)  # "Check cake availability"
```

## Delegation -- Signed Chains with Budget

```python
from ampro import DelegationLink, parse_chain_budget

remaining, max_budget = parse_chain_budget("remaining=3.50USD;max=5.00USD")
print(f"${remaining} of ${max_budget} remaining")
```

## Security -- Built In

- Message dedup (5-minute window)
- Nonce replay prevention
- Per-sender rate limiting
- Concurrency caps (50% per sender)
- Poison message tracking
- Chain-Budget enforcement
- JWKS caching with revocation

## Compliance -- GDPR Ready

```python
from ampro import ErasureRequest, ContentClassification

# PII classification
assert ContentClassification.PII == "pii"

# Cross-platform erasure
req = ErasureRequest(
    subject_id="user-123",
    subject_proof="signed-proof",
    scope="all",
    reason="user_request",
    deadline="2026-05-08T00:00:00Z",
)
```

## Protocol vs Platform

| Protocol (this package) | Platform (your business) |
|---|---|
| `agent://` addressing | Agent creation & onboarding |
| `POST /agent/message` | Agent configuration |
| Trust tiers & auth | Memory system |
| Delegation chains | AI model selection |
| Streaming & events | UI / dashboard |
| Compliance & erasure | Internal orchestration |

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) — detailed protocol architecture
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Examples](examples/)

## License

[Apache License 2.0](LICENSE)
