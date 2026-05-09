"""
heretic.skilningr.senses.library — L5.9 Library sense subpackage.

The Library sense ("Mímisbrunnr") gives the agent access to the Norse
text corpus: five public-domain sagas and Eddas downloaded from Project
Gutenberg, stored locally, and searchable via a lightweight keyword index.

Public API:

    from heretic.skilningr.senses.library import (
        LibrarySense,
        LibraryClient,
        LIBRARY_TOOL_DEFINITIONS,
    )

Module map:
    config_model.py — LibraryConfig (re-exported from skilningr.config_model)
    errors.py       — Library error types (re-exports from mimisbrunnr.errors)
    client.py       — LibraryClient (corpus accessor — search, get_text, list_sources)
    tools.py        — LIBRARY_TOOL_DEFINITIONS (3 OpenAI tool schemas, locked at v0.7)
    sense.py        — LibrarySense (orchestrator; registered in ToolDispatcher as "library")
    INTERFACE.md    — Full Library sense contract

Backend subsystem:
    heretic.skilningr.mimisbrunnr — manifest, downloader, store, index, consent

Ref: src/heretic/skilningr/senses/library/INTERFACE.md
     src/heretic/skilningr/mimisbrunnr/__init__.py (backend public API)
     docs/architecture/LAYER_INTERFACES.md §L5.9 Mímisbrunnr
"""

from heretic.skilningr.senses.library.client import LibraryClient  # noqa: F401
from heretic.skilningr.senses.library.sense import LibrarySense  # noqa: F401
from heretic.skilningr.senses.library.tools import LIBRARY_TOOL_DEFINITIONS  # noqa: F401

__all__ = [
    "LibrarySense",
    "LibraryClient",
    "LIBRARY_TOOL_DEFINITIONS",
]
