"""
Leið sense errors — re-exports from the Skilningr error hierarchy.

Ref: heretic.skilningr.errors (authoritative definitions)
"""

from heretic.skilningr.errors import (  # noqa: F401
    LeidConnectionError,
    LeidError,
    LeidHttpError,
    LeidPlaywrightUnavailableError,
    LeidResponseTooLargeError,
    LeidTimeoutError,
    UrlNotAllowedError,
)

__all__ = [
    "LeidError",
    "UrlNotAllowedError",
    "LeidTimeoutError",
    "LeidResponseTooLargeError",
    "LeidHttpError",
    "LeidConnectionError",
    "LeidPlaywrightUnavailableError",
]
