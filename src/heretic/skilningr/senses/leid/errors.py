"""
Leið sense errors — re-exports from the Skilningr error hierarchy.

Ref: heretic.skilningr.errors (authoritative definitions)
"""

from heretic.skilningr.errors import (  # noqa: F401
    LeidClickElementNotFoundError,
    LeidConnectionError,
    LeidError,
    LeidHttpError,
    LeidPlaywrightUnavailableError,
    LeidPressOnElementNotFoundError,
    LeidResponseTooLargeError,
    LeidSessionExpiredError,
    LeidSessionLimitError,
    LeidTimeoutError,
    LeidTypeElementNotFoundError,
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
    "LeidSessionLimitError",
    "LeidSessionExpiredError",
    "LeidClickElementNotFoundError",
    "LeidTypeElementNotFoundError",
    "LeidPressOnElementNotFoundError",
]
