# Agent Mesh Protocol — Examples

## Quick Start

```bash
pip install agent-protocol
```

## Examples

| # | File | What it demonstrates | Level |
|---|------|---------------------|-------|
| 01 | `01_minimum_viable_agent.py` | 30-line Flask agent — the simplest possible | Beginner |
| 02 | `02_fastapi_agent.py` | FastAPI with tools, streaming, body validation | Intermediate |
| 03 | `03_trust_and_auth.py` | 4 trust tiers, multi-method auth parsing | Intermediate |
| 04 | `04_addressing.py` | `agent://` URI scheme — 3 forms, normalization | Beginner |
| 05 | `05_body_schemas.py` | 23 typed body schemas with validation | Intermediate |
| 06 | `06_delegation_chains.py` | Ed25519 signed chains, budget, loop detection | Advanced |
| 07 | `07_security.py` | Dedup, nonce, rate limiting, concurrency, poison message | Intermediate |
| 08 | `08_compliance.py` | GDPR: PII classification, audit hash-chain, erasure | Intermediate |
| 09 | `09_capability_negotiation.py` | 8 groups, 6 levels, version negotiation | Beginner |

## Running

Most examples are standalone scripts:

```bash
python examples/04_addressing.py
python examples/05_body_schemas.py
```

Server examples need a framework:

```bash
pip install flask
python examples/01_minimum_viable_agent.py

# Or with FastAPI:
pip install fastapi uvicorn
uvicorn examples.02_fastapi_agent:app --port 8000
```
