"""
Library sense errors — re-exports from the Mímisbrunnr error hierarchy.

This module provides a single import point for Library-specific errors
so that callers within the library sense subpackage (client.py, sense.py)
can write:

    from heretic.skilningr.senses.library.errors import (
        LibraryError,
        LibraryDownloadError,
        IntegrityError,
        ManifestError,
        ConsentRefused,
        LibraryIndexError,
    )

without reaching up to heretic.skilningr.mimisbrunnr.errors directly.
This preserves the sense subpackage's encapsulation — callers outside
the subpackage should import from heretic.skilningr.mimisbrunnr.

Ref: heretic.skilningr.mimisbrunnr.errors (authoritative definitions)
"""

from heretic.skilningr.mimisbrunnr.errors import (  # noqa: F401
    ConsentRefused,
    IntegrityError,
    LibraryDownloadError,
    LibraryError,
    LibraryIndexError,
    ManifestError,
)

__all__ = [
    "LibraryError",
    "LibraryDownloadError",
    "IntegrityError",
    "ManifestError",
    "ConsentRefused",
    "LibraryIndexError",
]
