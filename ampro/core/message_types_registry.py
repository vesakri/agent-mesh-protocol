"""Registry of canonical body.type values from the Agent Mesh Protocol spec.

The 17 canonical body types cover creating work, lifecycle updates,
and responding. Extension types use reverse-domain prefixes
(e.g. ``com.example.custom_action``).
"""

# The 17 canonical body.type values
CANONICAL_BODY_TYPES = frozenset({
    # Creating work (POST)
    "message",
    "task.create",
    "task.assign",
    "task.delegate",
    "task.spawn",
    "task.quote",       # Future: requires cost estimation pipeline (see docstring)
    "notification",
    # Lifecycle updates (PATCH)
    "task.progress",
    "task.input_required",
    "task.escalate",
    "task.reroute",
    "task.transfer",
    "task.acknowledge",
    "task.reject",
    "task.complete",
    "task.error",
    # Responding (PUT)
    "task.response",
})

# HTTP verb → valid body.type mapping
POST_TYPES = frozenset({
    "message", "task.create", "task.assign", "task.delegate",
    "task.spawn", "task.quote", "notification",
})

PATCH_TYPES = frozenset({
    "task.progress", "task.input_required", "task.escalate",
    "task.reroute", "task.transfer", "task.acknowledge",
    "task.reject", "task.complete", "task.error",
})

PUT_TYPES = frozenset({"task.response"})
