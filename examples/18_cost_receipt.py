"""
18 — Cost Receipts (Per-Hop Cost Attribution)

Demonstrates end-to-end cost tracking across a three-agent delegation
chain. Each agent attaches a signed cost receipt to its response,
enabling full cost visibility from gateway to leaf.

Run:
    pip install agent-protocol
    python examples/18_cost_receipt.py
"""

from datetime import datetime, timezone, timedelta

from ampro import (
    AgentMessage,
    CostReceipt,
    CostReceiptChain,
    TaskCompleteBody,
    validate_body,
)

# ---------------------------------------------------------------------------
# Setup: Three-agent delegation chain
# ---------------------------------------------------------------------------

GATEWAY = "agent://gateway.example.com"
SPECIALIST = "agent://specialist.example.com"
TOOL_AGENT = "agent://tool-runner.example.com"
TASK_ID = "task-cost-demo-001"

print("=== Delegation Chain ===\n")
print(f"  {GATEWAY}")
print(f"    -> {SPECIALIST}")
print(f"         -> {TOOL_AGENT}")

now = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Step 1: Tool Agent completes work — issues a cost receipt
# ---------------------------------------------------------------------------

print(f"\n=== Step 1: Tool Agent Completes Work ===\n")

tool_receipt = CostReceipt(
    agent_id=TOOL_AGENT,
    task_id=TASK_ID,
    cost_usd=0.003,
    currency="USD",
    breakdown={
        "llm_inference": 0.001,
        "tool_execution": 0.002,
    },
    token_usage={
        "input": 450,
        "output": 120,
    },
    duration_seconds=1.2,
    issued_at=now.isoformat(),
)

print(f"  Agent:     {tool_receipt.agent_id}")
print(f"  Cost:      ${tool_receipt.cost_usd:.4f}")
print(f"  Breakdown: llm=${tool_receipt.breakdown['llm_inference']:.3f}, "
      f"tool=${tool_receipt.breakdown['tool_execution']:.3f}")
print(f"  Tokens:    {tool_receipt.token_usage['input']}in / {tool_receipt.token_usage['output']}out")
print(f"  Duration:  {tool_receipt.duration_seconds}s")

# ---------------------------------------------------------------------------
# Step 2: Specialist adds its own receipt, builds the chain
# ---------------------------------------------------------------------------

print(f"\n=== Step 2: Specialist Adds Its Receipt ===\n")

specialist_receipt = CostReceipt(
    agent_id=SPECIALIST,
    task_id=TASK_ID,
    cost_usd=0.012,
    currency="USD",
    breakdown={
        "llm_inference": 0.010,
        "tool_execution": 0.002,
    },
    token_usage={
        "input": 2100,
        "output": 850,
    },
    duration_seconds=3.8,
    issued_at=(now + timedelta(seconds=2)).isoformat(),
)

chain = CostReceiptChain()
chain.add_receipt(tool_receipt)
chain.add_receipt(specialist_receipt)

print(f"  Agent:     {specialist_receipt.agent_id}")
print(f"  Cost:      ${specialist_receipt.cost_usd:.4f}")
print(f"  Tokens:    {specialist_receipt.token_usage['input']}in / {specialist_receipt.token_usage['output']}out")
print(f"  Duration:  {specialist_receipt.duration_seconds}s")
print(f"\n  Chain so far:")
print(f"    Receipts: {len(chain.receipts)}")
print(f"    Running total: ${chain.total_cost_usd:.4f}")

# ---------------------------------------------------------------------------
# Step 3: Gateway receives chain, adds its own receipt
# ---------------------------------------------------------------------------

print(f"\n=== Step 3: Gateway Adds Its Receipt ===\n")

gateway_receipt = CostReceipt(
    agent_id=GATEWAY,
    task_id=TASK_ID,
    cost_usd=0.005,
    currency="USD",
    breakdown={
        "llm_inference": 0.004,
        "routing_overhead": 0.001,
    },
    token_usage={
        "input": 800,
        "output": 200,
    },
    duration_seconds=0.5,
    issued_at=(now + timedelta(seconds=4)).isoformat(),
)

chain.add_receipt(gateway_receipt)

print(f"  Agent:     {gateway_receipt.agent_id}")
print(f"  Cost:      ${gateway_receipt.cost_usd:.4f}")
print(f"  Duration:  {gateway_receipt.duration_seconds}s")

# ---------------------------------------------------------------------------
# Per-hop breakdown and total
# ---------------------------------------------------------------------------

print(f"\n=== Per-Hop Cost Breakdown ===\n")

print(f"  {'Hop':5s} {'Agent':40s} {'Cost':>10s} {'Duration':>10s}")
print(f"  {'---':5s} {'-----':40s} {'----':>10s} {'--------':>10s}")

for i, receipt in enumerate(chain.receipts):
    print(f"  {i + 1:<5d} {receipt.agent_id:40s} ${receipt.cost_usd:>8.4f} {receipt.duration_seconds:>8.1f}s")

print(f"  {'':5s} {'':40s} {'--------':>10s} {'--------':>10s}")
total_duration = sum(r.duration_seconds for r in chain.receipts if r.duration_seconds)
print(f"  {'':5s} {'TOTAL':40s} ${chain.total_cost_usd:>8.4f} {total_duration:>8.1f}s")

# ---------------------------------------------------------------------------
# Step 4: Wrap in task.complete with cost_receipt field
# ---------------------------------------------------------------------------

print(f"\n=== Step 4: TaskCompleteBody with Cost Receipt ===\n")

completion = TaskCompleteBody(
    task_id=TASK_ID,
    result={"summary": "Analysis complete", "findings": 3},
    cost_usd=chain.total_cost_usd,
    duration_seconds=total_duration,
    cost_receipt=chain.model_dump(),
    metadata={"hops": len(chain.receipts)},
)

complete_msg = AgentMessage(
    sender=GATEWAY,
    recipient="agent://orchestrator.example.com",
    body_type="task.complete",
    headers={
        "Protocol-Version": "0.1.3",
        "Session-Id": "sess-cost-demo-001",
    },
    body=completion.model_dump(),
)

print(f"  Body type:    {complete_msg.body_type}")
print(f"  Task ID:      {completion.task_id}")
print(f"  Total cost:   ${completion.cost_usd:.4f}")
print(f"  Duration:     {completion.duration_seconds}s")
print(f"  Hops:         {completion.metadata['hops']}")

# Validate the body round-trips correctly
validated = validate_body("task.complete", complete_msg.body)
print(f"\n  Validated:    {type(validated).__name__}")
print(f"  Has receipt:  {validated.cost_receipt is not None}")

# Extract the chain from the validated body
receipt_chain = CostReceiptChain.model_validate(validated.cost_receipt)
print(f"  Chain hops:   {len(receipt_chain.receipts)}")
print(f"  Chain total:  ${receipt_chain.total_cost_usd:.4f}")

# ---------------------------------------------------------------------------
# Token usage summary
# ---------------------------------------------------------------------------

print(f"\n=== Token Usage Summary ===\n")

total_input = sum(r.token_usage.get("input", 0) for r in chain.receipts if r.token_usage)
total_output = sum(r.token_usage.get("output", 0) for r in chain.receipts if r.token_usage)

for receipt in chain.receipts:
    if receipt.token_usage:
        print(f"  {receipt.agent_id}:")
        print(f"    Input:  {receipt.token_usage['input']:>6d} tokens")
        print(f"    Output: {receipt.token_usage['output']:>6d} tokens")

print(f"\n  Total: {total_input} input + {total_output} output = {total_input + total_output} tokens")
