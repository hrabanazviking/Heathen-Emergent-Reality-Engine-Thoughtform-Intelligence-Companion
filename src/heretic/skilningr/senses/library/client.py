"""
LibraryClient — agent-facing access to the Mímisbrunnr text corpus.

LibraryClient is the sense-level abstraction that translates tool calls
(library.search, library.get_text, library.list_sources) into operations
on the Mímisbrunnr subsystem (mimisbrunnr.index.KeywordIndex, store,
manifest). It does NOT own the index or the storage — it delegates to
the mimisbrunnr subpackage.

OFFLINE INVARIANT (Cartographer thread #1):
    LibraryClient MUST NOT import httpx — ever. httpx is the network
    boundary and lives exclusively in Downloader. LibraryClient is an
    offline reader/searcher. If you see an httpx import here, it is a
    bug — remove it immediately.

DESIGN CONTRACT:
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
from heretic.skilningr.mimisbrunnr import (
    NORSE_STARTER_PACK,
    KeywordIndex,
    LibraryIndexError,
)
from heretic.skilningr.mimisbrunnr import store as mimisbrunnr_store
from heretic.skilningr.senses.library.errors import LibraryError

logger = logging.getLogger(__name__)

# NOTE: httpx is deliberately NOT imported here.
# See "OFFLINE INVARIANT" in the module docstring above.


class LibraryClient:
    """Sense-level client for the Library (Mímisbrunnr) corpus.

    Usage:
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
        # Lazily-created KeywordIndex — reused across search calls
        self._index: KeywordIndex | None = None

    def _get_index(self) -> KeywordIndex:
        """Return a KeywordIndex, creating it once and caching it.

        Does not build the index — caller is responsible for ensuring
        build() has been called (via sense.open() autoindex_on_open,
        or explicitly).
        """
        if self._index is None:
            self._index = KeywordIndex(self._data_dir)
        return self._index

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search the keyword index for lines matching query.

        Delegates to KeywordIndex.search(). Returns results as a list
        of JSON-serialisable dicts.

        Args:
            query:       Case-insensitive search string.
            max_results: Maximum number of results to return.
                         Capped at config.max_results when > 0.

        Returns:
            List of dicts, each with keys:
                source_id (str): the source identifier
                line_number (int): 1-based line number
                context_text (str): surrounding text excerpt
                match_position (int): 0-based char offset of first match

        Raises:
            LibraryError: if the index is not built or search fails.
        """
        # Apply config cap
        effective_max = min(max_results, self._config.max_results)

        try:
            hits = self._get_index().search(query, max_results=effective_max)
        except LibraryIndexError as exc:
            raise LibraryError(str(exc)) from exc
        except Exception as exc:
            raise LibraryError(
                f"Unexpected error during library search: {type(exc).__name__}: {exc}"
            ) from exc

        return [
            {
                "source_id": hit.source_id,
                "line_number": hit.line_number,
                "context_text": hit.context_text,
                "match_position": hit.match_position,
            }
            for hit in hits
        ]

    def get_text(
        self,
        source_id: str,
        start_line: int = 1,
        num_lines: int = 50,
    ) -> dict[str, Any]:
        """Return a line range from a downloaded source file.

        Args:
            source_id:  The source identifier (e.g. 'prose_edda_brodeur').
                        Must be a known source id and must be downloaded.
            start_line: 1-based line number of the first line to return.
                        Clamped to 1 at minimum.
            num_lines:  Number of lines to return (default 50).
                        Clamped to 1 at minimum. At end of file, fewer
                        lines may be returned.

        Returns:
            dict with keys:
                source_id (str): echoes the requested source_id
                start_line (int): the actual start line used (clamped)
                num_lines (int): actual number of lines returned
                text (str): the extracted text block (lines joined with \n)
                total_lines_in_file (int): total line count of the source file

        Raises:
            LibraryError: if the source is not downloaded, source_id is
                unknown, start_line > total_lines, or file read fails.
        """
        # Validate source_id exists in manifest
        source = NORSE_STARTER_PACK.get_source(source_id)
        if source is None:
            raise LibraryError(
                f"Unknown source_id {source_id!r}. "
                f"Valid ids: {NORSE_STARTER_PACK.source_ids}"
            )

        # Validate source is downloaded
        try:
            if not mimisbrunnr_store.is_source_downloaded(self._data_dir, source_id):
                raise LibraryError(
                    f"Source {source_id!r} has not been downloaded yet. "
                    "Use 'heretic library download' to fetch it first."
                )
        except ValueError as exc:
            raise LibraryError(str(exc)) from exc

        # Resolve file path
        try:
            source_path = mimisbrunnr_store.resolve_source_path(
                self._data_dir, source_id
            )
        except ValueError as exc:
            raise LibraryError(str(exc)) from exc

        # Read the file
        try:
            text_content = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise LibraryError(
                f"Could not read source file for {source_id!r}: {exc}"
            ) from exc

        all_lines = text_content.splitlines()
        total_lines = len(all_lines)

        # Clamp start_line
        start_line = max(1, start_line)

        if start_line > total_lines:
            raise LibraryError(
                f"start_line {start_line} is beyond the end of {source_id!r} "
                f"(file has {total_lines} lines)."
            )

        # Clamp num_lines
        num_lines = max(1, num_lines)

        # Extract the slice (0-indexed)
        slice_start = start_line - 1
        slice_end = min(slice_start + num_lines, total_lines)
        extracted = all_lines[slice_start:slice_end]
        actual_num_lines = len(extracted)

        return {
            "source_id": source_id,
            "start_line": start_line,
            "num_lines": actual_num_lines,
            "text": "\n".join(extracted),
            "total_lines_in_file": total_lines,
        }

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
                sha256 (str | None): verified hash from local manifest,
                                     or None if not yet downloaded/recorded

        Raises:
            LibraryError: on unexpected errors reading local manifest.
        """
        try:
            local_manifest = mimisbrunnr_store.load_local_manifest(self._data_dir)
        except Exception as exc:
            self._log.warning(
                "LibraryClient.list_sources: could not read local manifest: %s "
                "— proceeding with empty manifest.", exc
            )
            local_manifest = {}

        result: list[dict[str, Any]] = []
        for source in NORSE_STARTER_PACK.sources:
            try:
                downloaded = mimisbrunnr_store.is_source_downloaded(
                    self._data_dir, source.id
                )
            except ValueError:
                downloaded = False

            manifest_entry = local_manifest.get(source.id, {})
            recorded_sha256 = manifest_entry.get("sha256") if manifest_entry else None

            result.append({
                "id": source.id,
                "title": source.title,
                "url": source.url,
                "license": source.license,
                "expected_size_bytes": source.expected_size_bytes,
                "downloaded": downloaded,
                "sha256": recorded_sha256,
            })

        return result
