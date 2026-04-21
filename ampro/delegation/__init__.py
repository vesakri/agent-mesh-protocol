"""Delegation chains, cost receipts, and tracing."""

from ampro.delegation.chain import (
    DelegationChain,
    DelegationLink,
    check_visited_agents_limit,
    check_visited_agents_loop,
    normalize_agent_uri,
    parse_chain_budget,
    parse_visited_agents,
    sign_delegation,
    validate_chain,
    validate_scope_narrowing,
)
from ampro.delegation.cost_receipt import (
    CostReceipt,
    CostReceiptChain,
    CostReceiptVerificationError,
)
from ampro.delegation.tracing import (
    TraceContext,
    extract_trace_context,
    generate_span_id,
    generate_trace_id,
    inject_trace_headers,
    sign_trace_context,
    verify_trace_context,
)

__all__ = [
    # Chain
    "DelegationLink", "DelegationChain",
    "validate_chain", "validate_scope_narrowing", "sign_delegation",
    "parse_chain_budget", "parse_visited_agents", "normalize_agent_uri",
    "check_visited_agents_loop", "check_visited_agents_limit",
    # Cost receipts
    "CostReceipt", "CostReceiptChain", "CostReceiptVerificationError",
    # Tracing
    "TraceContext", "generate_trace_id", "generate_span_id",
    "inject_trace_headers", "extract_trace_context",
    "sign_trace_context", "verify_trace_context",
]
