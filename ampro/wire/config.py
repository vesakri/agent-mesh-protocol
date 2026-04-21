"""
AMP Wire Binding -- Configuration Defaults.

These are the RECOMMENDED defaults from the wire binding spec.
Implementations MAY override any of these values.

Usage::

    from ampro.wire.config import WireConfig, DEFAULTS

    # Use defaults
    cfg = DEFAULTS
    print(cfg.max_message_bytes)  # 10_485_760

    # Override specific values
    custom = WireConfig(rate_limit_rpm=120, max_concurrent_tasks=100)

PURE -- zero platform-specific imports.  Only pydantic and stdlib.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class WireConfig(BaseModel):
    """Configuration for an AMP wire binding implementation.

    All values have protocol-recommended defaults.  Implementations
    SHOULD document any deviations.
    """

    # --- Message handling ---
    max_message_bytes: int = Field(
        default=10_485_760,
        ge=1024,
        description="Maximum message size in bytes (default 10 MB)",
    )
    max_response_bytes: int = Field(
        default=5_242_880,
        ge=1024,
        description="Maximum response size in bytes (default 5 MB)",
    )

    # --- Rate limiting ---
    rate_limit_rpm: int = Field(
        default=60,
        ge=1,
        description="Requests per minute per sender",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        description="Rate limit sliding window in seconds",
    )
    rate_limiter_max_senders: int = Field(
        default=100_000,
        ge=100,
        description="Maximum tracked senders in rate limiter",
    )

    # --- Dedup ---
    dedup_window_seconds: int = Field(
        default=300,
        ge=1,
        description="Message deduplication window (default 5 min)",
    )
    dedup_max_entries: int = Field(
        default=100_000,
        ge=100,
        description="Maximum entries in the dedup store before eviction",
    )

    # --- Nonce ---
    # 5 minutes is the industry standard (OWASP, OAuth2).
    # Increase for slow networks.
    nonce_window_seconds: int = Field(
        default=300,
        ge=60,
        description="Nonce replay detection window (default 5 min)",
    )
    nonce_max_entries: int = Field(
        default=100_000,
        ge=100,
        description="Maximum entries in the nonce store before eviction",
    )

    # --- Sessions ---
    session_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="Default session time-to-live in seconds",
    )
    session_max_messages: int = Field(
        default=10_000,
        ge=1,
        description="Maximum messages allowed per session",
    )

    # --- Streaming (SSE) ---
    heartbeat_interval_seconds: int = Field(
        default=15,
        ge=1,
        description="Seconds between SSE heartbeat comments",
    )
    stream_buffer_size: int = Field(
        default=100,
        ge=1,
        description="Ring buffer size for event replay on reconnect",
    )
    stream_queue_size: int = Field(
        default=1000,
        ge=10,
        description="Maximum queued events per SSE stream",
    )
    max_active_streams: int = Field(
        default=10_000,
        ge=1,
        description="Maximum concurrent SSE streams",
    )
    max_streams_per_sender: int = Field(
        default=10,
        ge=1,
        description="Maximum concurrent SSE streams per sender",
    )

    # --- Delegation ---
    max_delegation_depth: int = Field(
        default=5,
        ge=1,
        description="Maximum number of hops in a delegation chain",
    )
    max_scopes_per_link: int = Field(
        default=100,
        ge=1,
        description="Maximum number of scopes in a single delegation link",
    )

    # --- Concurrency ---
    max_concurrent_tasks: int = Field(
        default=50,
        ge=1,
        description="Maximum tasks an agent processes concurrently",
    )

    # --- Callback delivery ---
    callback_max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum callback delivery attempts before giving up",
    )
    callback_retry_delays: list[int] = Field(
        default_factory=lambda: [1, 5, 25],
        description="Retry delays in seconds (exponential backoff)",
    )

    # --- Challenge (anti-abuse) ---
    challenge_expiry_seconds: int = Field(
        default=300,
        ge=10,
        description="Seconds before a challenge nonce expires",
    )

    # --- Agent.json caching ---
    agent_json_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="Cache TTL for fetched agent.json documents",
    )

    # --- Request timeouts ---
    default_timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Default request timeout for synchronous operations",
    )
    max_timeout_seconds: int = Field(
        default=300,
        ge=1,
        description="Maximum allowed timeout for any single operation",
    )

    model_config = {"extra": "allow", "frozen": True}

    @model_validator(mode="after")
    def validate_cross_fields(self) -> WireConfig:
        if self.max_timeout_seconds < self.default_timeout_seconds:
            raise ValueError(
                "max_timeout_seconds must be >= default_timeout_seconds"
            )
        if self.callback_max_retries > 0 and len(self.callback_retry_delays) < 1:
            raise ValueError(
                "callback_retry_delays must have at least 1 entry "
                "when callback_max_retries > 0"
            )
        return self


# The protocol-recommended defaults.
DEFAULTS = WireConfig()
