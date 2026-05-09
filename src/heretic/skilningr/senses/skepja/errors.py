"""
Skepja sense errors — re-exports from the Skilningr error hierarchy.

This module provides a single import point for Skepja-specific errors so that
callers within the skepja subpackage (client.py, sense.py) can write:

    from heretic.skilningr.senses.skepja.errors import (
        SkepjaError,
        CommandNotAllowedError,
        CommandParseError,
        CommandTimeoutError,
        CommandExecutionError,
    )

without reaching up to heretic.skilningr.errors directly.

Ref: heretic.skilningr.errors (authoritative definitions)
"""

from heretic.skilningr.errors import (  # noqa: F401
    CommandExecutionError,
    CommandNotAllowedError,
    CommandParseError,
    CommandTimeoutError,
    SkepjaError,
)

__all__ = [
    "SkepjaError",
    "CommandNotAllowedError",
    "CommandParseError",
    "CommandTimeoutError",
    "CommandExecutionError",
]
