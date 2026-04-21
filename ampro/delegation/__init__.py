"""Delegation chains, cost receipts, and tracing."""

from ampro.delegation.chain import (
    DelegationLink, DelegationChain,
    validate_chain, validate_scope_narrowing, sign_delegation,
    parse_chain_budget, parse_visited_agents, normalize_agent_uri,
    check_visited_agents_loop, check_visited_agents_limit,
)
from ampro.delegation.cost_receipt import CostReceipt, CostReceiptChain, CostReceiptVerificationError
from ampro.delegation.tracing import (
    TraceContext, generate_trace_id, generate_span_id,
    inject_trace_headers, extract_trace_context,
    sign_trace_context, verify_trace_context,
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
