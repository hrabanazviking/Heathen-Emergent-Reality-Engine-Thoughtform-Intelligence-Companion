"""
heretic.skilningr.mimisbrunnr — the Mímisbrunnr library subsystem.

Mímisbrunnr ("Mímir's well") is the knowledge-well beneath Yggdrasil.
This subpackage owns everything related to the Norse starter-pack text
corpus: the manifest of source URLs, the download gate, on-disk storage
layout, and the lightweight keyword index.

It is NOT a sense. It is the backend the Library sense (L5.9) draws from.
The Library sense (senses/library/) owns the tool schema, LibraryClient,
and LibrarySense orchestrator. Mímisbrunnr owns the corpus data layer
that the client calls into.

Public API:

    from heretic.skilningr.mimisbrunnr import (
        NORSE_STARTER_PACK,
        NorseStarterPackManifest,
        LibrarySource,
        Downloader,
        KeywordIndex,
        SearchHit,
    )

Module map:
    errors.py    — LibraryError hierarchy (LibraryDownloadError,
                   IntegrityError, ManifestError, ConsentRefused,
                   LibraryIndexError)
    manifest.py  — LibrarySource, NorseStarterPackManifest,
                   NORSE_STARTER_PACK constant (5 verified URLs)
    downloader.py— Downloader class (async download + integrity check stub)
    store.py     — path resolution, directory creation, local manifest I/O
    index.py     — KeywordIndex (build + search stubs), SearchHit dataclass
    consent.py   — prompt_for_download (operator approval gate)
    INTERFACE.md — full subsystem contract

Ref: src/heretic/skilningr/senses/library/INTERFACE.md (Library sense contract)
     docs/architecture/LAYER_INTERFACES.md §L5 Skilningr §L5.9 Mímisbrunnr
"""

from heretic.skilningr.mimisbrunnr.errors import (  # noqa: F401
    ConsentRefused,
    IntegrityError,
    LibraryDownloadError,
    LibraryError,
    LibraryIndexError,
    ManifestError,
)
from heretic.skilningr.mimisbrunnr.index import (  # noqa: F401
    KeywordIndex,
    SearchHit,
)
from heretic.skilningr.mimisbrunnr.manifest import (  # noqa: F401
    LibrarySource,
    NORSE_STARTER_PACK,
    NorseStarterPackManifest,
)
from heretic.skilningr.mimisbrunnr.downloader import Downloader  # noqa: F401

__all__ = [
    # Errors
    "LibraryError",
    "LibraryDownloadError",
    "IntegrityError",
    "ManifestError",
    "ConsentRefused",
    "LibraryIndexError",
    # Manifest
    "LibrarySource",
    "NorseStarterPackManifest",
    "NORSE_STARTER_PACK",
    # Index
    "KeywordIndex",
    "SearchHit",
    # Downloader
    "Downloader",
]
