"""
LibraryClient — agent-facing access to the Mímisbrunnr text corpus.

LibraryClient is the sense-level abstraction that translates tool calls
(library.search, library.get_text, library.list_sources) into operations
on the Mímisbrunnr subsystem (mimisbrunnr.index.KeywordIndex, store,
manifest). It does NOT own the index or the storage — it delegates to
the mimisbrunnr subpackage.

DESIGN CONTRACT (Forge implements the bodies):
    - search: delegates to KeywordIndex.search(); returns a list of
      dicts suitable for JSON serialisation by the LibrarySense.
    - get_text: reads a specific line range from a downloaded source
      file. Raises LibraryError if the source is not downloaded or the
      line range is out of bounds.
    - list_sources: returns the NORSE_STARTER_PACK source list annotated
      with download status (is_source_downloaded) for each source.

All methods are synchronous. LibrarySense wraps them in asyncio.to_thread
where necessary.

Ref: src/heretic/skilningr/senses/library/INTERFACE.md
     src/heretic/skilningr/mimisbrunnr/ (backend subsystem)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from heretic.skilningr.config_model import LibraryConfig
from heretic.skilningr.senses.library.errors import LibraryError

logger = logging.getLogger(__name__)


class LibraryClient:
    """Sense-level client for the Library (Mímisbrunnr) corpus.

    Usage (Forge implements bodies):
        client = LibraryClient(config, data_dir, log)
        results = client.search("Odin", max_results=10)
        text    = client.get_text("prose_edda_brodeur", 1, 50)
        sources = client.list_sources()
    """

    def __init__(
        self,
        config: LibraryConfig,
        data_dir: Path,
        log: logging.Logger | None = None,
    ) -> None:
        """Initialise the LibraryClient.

        Args:
            config:   LibraryConfig from HereticConfig.skilningr.library.
            data_dir: Resolved absolute path to the Mímisbrunnr data dir.
            log:      Optional logger. Defaults to module logger.
        """
        self._config = config
        self._data_dir = data_dir
        self._log = log if log is not None else logging.getLogger(__name__)

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search the keyword index for lines matching query.

        Args:
            query:       Case-insensitive search string.
            max_results: Maximum number of results to return.

        Returns:
            List of dicts, each with keys:
                source_id (str): the source identifier
                line_number (int): 1-based line number
                context_text (str): surrounding text excerpt
                match_position (int): 0-based char offset of first match

        Raises:
            LibraryError: if the index is not built or search fails.
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "LibraryClient.search is a Forge implementation target. "
            "Body: instantiate KeywordIndex(self._data_dir); call "
            "index.search(query, max_results); convert SearchHit list "
            "to list[dict] and return."
        )

    def get_text(
        self,
        source_id: str,
        start_line: int = 1,
        num_lines: int = 50,
    ) -> dict[str, Any]:
        """Return a line range from a downloaded source file.

        Args:
            source_id:  The source identifier (e.g. 'prose_edda_brodeur').
            start_line: 1-based line number of the first line to return.
            num_lines:  Number of lines to return (default 50).

        Returns:
            dict with keys:
                source_id (str): echoes the requested source_id
                start_line (int): echoes start_line
                num_lines (int): actual lines returned (may be < num_lines
                                 at end of file)
                text (str): the extracted text block

        Raises:
            LibraryError: if the source is not downloaded, source_id is
                unknown, or start_line is out of range.
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "LibraryClient.get_text is a Forge implementation target. "
            "Body: resolve path via store.resolve_source_path; verify "
            "is_source_downloaded; open and slice the requested line "
            "range; return as a structured dict."
        )

    def list_sources(self) -> list[dict[str, Any]]:
        """List all sources in the Norse starter pack with download status.

        Returns:
            List of dicts, one per LibrarySource, with keys:
                id (str): source identifier
                title (str): human-readable title
                url (str): download URL
                license (str): license statement
                expected_size_bytes (int): size from manifest
                downloaded (bool): True if source file exists on disk
                sha256 (str | None): verified hash, or None if not yet
                                     computed or source not downloaded

        Raises:
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "LibraryClient.list_sources is a Forge implementation target. "
            "Body: iterate NORSE_STARTER_PACK.sources; for each, call "
            "store.is_source_downloaded and store.load_local_manifest; "
            "build and return the list of status dicts."
        )
