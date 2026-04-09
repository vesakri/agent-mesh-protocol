"""
Agent Protocol — Protocol Versioning.

Tracks supported protocol versions, validates client version requests,
and formats HTTP Sunset headers per RFC 7231.

This module is PURE — no platform-specific imports (app.*, etc.).
Designed for extraction as part of `pip install agent-protocol`.
"""

from __future__ import annotations

from datetime import datetime


# All protocol versions this server can speak.
SUPPORTED_VERSIONS: list[str] = ["1.0.0", "0.1.0"]

# The version returned when the client does not specify one.
CURRENT_VERSION: str = "1.0.0"


def check_version(requested: str | None) -> str:
    """
    Validate a client-requested protocol version.

    Args:
        requested: The version string from the ``Accept-Version`` header,
                   or ``None`` if the client did not specify one.

    Returns:
        A valid version string (``CURRENT_VERSION`` when *requested* is None).

    Raises:
        ValueError: If *requested* is not in ``SUPPORTED_VERSIONS``.
    """
    if requested is None:
        return CURRENT_VERSION
    if requested not in SUPPORTED_VERSIONS:
        raise ValueError(
            f"Unsupported protocol version '{requested}'. "
            f"Supported: {', '.join(SUPPORTED_VERSIONS)}"
        )
    return requested


def format_sunset_header(deprecated_at: datetime) -> str:
    """
    Format a ``Sunset`` response header value per RFC 7231.

    The format is the HTTP-date (IMF-fixdate) production:
        ``Sun, 06 Nov 1994 08:49:37 GMT``

    Args:
        deprecated_at: The deprecation timestamp (will be treated as UTC).

    Returns:
        An RFC 7231 HTTP-date string.
    """
    # strftime %a/%b are locale-independent in CPython for the en_US names
    # used by HTTP-date, but we format explicitly to be safe.
    _DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    _MONTHS = [
        "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    day_name = _DAYS[deprecated_at.weekday()]
    month_name = _MONTHS[deprecated_at.month]

    return (
        f"{day_name}, {deprecated_at.day:02d} {month_name} "
        f"{deprecated_at.year:04d} {deprecated_at.hour:02d}:"
        f"{deprecated_at.minute:02d}:{deprecated_at.second:02d} GMT"
    )


def negotiate_version(accept_version: str | None) -> str:
    """
    Negotiate protocol version from Accept-Version preference list.

    The client sends comma-separated versions in preference order.
    Server picks the highest version it supports from the list.
    Returns CURRENT_VERSION if accept_version is None.
    Raises ValueError if no version matches.
    """
    if accept_version is None:
        return CURRENT_VERSION

    requested = [v.strip() for v in accept_version.split(",") if v.strip()]
    if not requested:
        return CURRENT_VERSION

    for version in requested:
        if version in SUPPORTED_VERSIONS:
            return version

    raise ValueError(
        f"No supported version in requested list {requested}. "
        f"Supported: {SUPPORTED_VERSIONS}"
    )
