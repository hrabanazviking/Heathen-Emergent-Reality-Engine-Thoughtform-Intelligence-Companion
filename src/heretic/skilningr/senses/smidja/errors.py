"""
Smiðja sense errors — re-exports from the Skilningr error hierarchy.

This module provides a single import point for Smiðja-specific errors so that
callers within the smidja subpackage (client.py, sense.py) can write:

    from heretic.skilningr.senses.smidja.errors import (
        SmidjaError,
        BrunhandUnreachableError,
        BrunhandTimeoutError,
        BrunhandAuthError,
        BrunhandSessionLockedError,
    )

without reaching up to heretic.skilningr.errors directly. This preserves
the sense subpackage's encapsulation — callers outside the subpackage should
import from heretic.skilningr.errors or heretic.skilningr.

Ref: heretic.skilningr.errors (authoritative definitions)
"""

from heretic.skilningr.errors import (  # noqa: F401
    BrunhandAuthError,
    BrunhandSessionLockedError,
    BrunhandTimeoutError,
    BrunhandUnreachableError,
    SmidjaError,
)

__all__ = [
    "SmidjaError",
    "BrunhandUnreachableError",
    "BrunhandTimeoutError",
    "BrunhandAuthError",
    "BrunhandSessionLockedError",
]
