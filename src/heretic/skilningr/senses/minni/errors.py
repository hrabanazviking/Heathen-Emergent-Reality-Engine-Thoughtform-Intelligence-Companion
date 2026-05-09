"""
Minni sense errors — re-exports from the Skilningr error hierarchy.

This module provides a single import point for Minni-specific errors so that
callers within the minni subpackage (client.py, sense.py) can write:

    from heretic.skilningr.senses.minni.errors import (
        MinniError,
        MinniSandboxViolation,
        MinniFileNotFoundError,
        MinniFileTooLargeError,
        MinniPermissionError,
    )

without reaching up to heretic.skilningr.errors directly. This preserves
the sense subpackage's encapsulation — callers outside the subpackage should
import from heretic.skilningr.errors or heretic.skilningr.

Ref: heretic.skilningr.errors (authoritative definitions)
"""

from heretic.skilningr.errors import (  # noqa: F401
    MinniError,
    MinniFileNotFoundError,
    MinniFileTooLargeError,
    MinniPermissionError,
    MinniSandboxViolation,
)

__all__ = [
    "MinniError",
    "MinniSandboxViolation",
    "MinniFileNotFoundError",
    "MinniFileTooLargeError",
    "MinniPermissionError",
]
