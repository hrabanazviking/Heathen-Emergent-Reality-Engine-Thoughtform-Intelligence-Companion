"""
Mímisbrunnr keyword index — line-level full-text search over downloaded sources.

KeywordIndex builds and searches a lightweight keyword index over the
plain-text source files in the Mímisbrunnr data_dir. The index is
intentionally simple at v0.7: no vector embeddings, no stemming, no
language model — just case-folded substring matching with line-level
context windows. This is the fastest path to a useful tool for the
agent with zero heavy dependencies.

The v0.7 index design:
    - Build: iterate every downloaded .txt file line by line; write a
      keyword_index.jsonl file (<data_dir>/keyword_index.jsonl) with
      one JSON object per non-empty line:
          {"source_id": "prose_edda_brodeur", "line_number": 42,
           "content": "<first 200 chars of the line>"}
    - Search: load the index (streaming via json.loads per line);
      case-insensitive substring match against content; return top
      max_results hits as SearchHit dataclasses, each with:
          source_id, line_number, context_text, match_position
    - The index is rebuilt from scratch on each call to build().
      Incremental updates are a v0.8 concern.

DESIGN CONTRACT:
    - build() raises LibraryIndexError if no .txt files are found.
    - search() raises LibraryIndexError if no keyword_index.jsonl exists
      and no in-memory cache is present.
    - Neither build() nor search() downloads any text.
    - build() does NOT recurse into subdirectories — flat layout only.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Index
     src/heretic/skilningr/mimisbrunnr/errors.py (LibraryIndexError)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from heretic.skilningr.mimisbrunnr.errors import LibraryIndexError

logger = logging.getLogger(__name__)

# Maximum content length stored per line in the index
_MAX_LINE_CONTENT = 200

# Index filename within data_dir
_INDEX_FILENAME = "keyword_index.jsonl"

# Context window: lines before and after the match line
_CONTEXT_WINDOW = 1


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SearchHit:
    """A single search result from KeywordIndex.search().

    Attributes:
        source_id (str):
            The LibrarySource identifier (e.g. 'prose_edda_brodeur').
        line_number (int):
            1-based line number within the source file where the match
            was found.
        context_text (str):
            A short excerpt of text centred on the matching line —
            the matching line plus up to 1 line before and after.
            Lines are joined with newlines.
        match_position (int):
            0-based character offset of the first match within
            context_text. Allows callers to highlight the match.
    """

    source_id: str
    line_number: int
    context_text: str
    match_position: int


# ---------------------------------------------------------------------------
# Index class
# ---------------------------------------------------------------------------

class KeywordIndex:
    """Lightweight line-level keyword index over Mímisbrunnr source texts.

    Usage:
        index = KeywordIndex(data_dir)
        index.build(data_dir)
        hits = index.search("Odin", max_results=20)
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialise the KeywordIndex.

        Args:
            data_dir: The Mímisbrunnr data directory where source .txt
                      files and the keyword_index.jsonl file live.
        """
        self._data_dir = data_dir
        # In-memory cache: list of (source_id, line_number, content) tuples
        # None means "not loaded yet" — load lazily from disk on search().
        self._cache: list[dict] | None = None

    def build(self, data_dir: Path) -> None:
        """Build (or rebuild) the keyword index from downloaded sources.

        Iterates every *.txt file in data_dir (non-recursive — flat layout
        only), tokenises line by line, and writes a JSONL index to
        data_dir/keyword_index.jsonl. Any existing index file is replaced
        atomically via .heretic_tmp + os.replace.

        After a successful build, the in-memory cache is refreshed from
        the newly written file.

        Args:
            data_dir: The Mímisbrunnr data directory containing the
                      downloaded .txt source files.

        Raises:
            LibraryIndexError: if no downloaded .txt files are found
                in data_dir (nothing to index).
        """
        # Collect .txt files (non-recursive) — exclude keyword_index.jsonl etc.
        txt_files = sorted(data_dir.glob("*.txt"))

        if not txt_files:
            raise LibraryIndexError(
                f"No downloaded .txt source files found in {data_dir}. "
                "Download at least one source before building the index. "
                "Use 'heretic library download <source_id>' to fetch a source."
            )

        index_path = data_dir / _INDEX_FILENAME
        tmp_path = index_path.with_suffix(".heretic_tmp")

        total_lines = 0
        entries_written = 0

        try:
            with tmp_path.open("w", encoding="utf-8") as fh:
                for txt_file in txt_files:
                    # Derive source_id from the stem (filename without .txt)
                    source_id = txt_file.stem

                    try:
                        lines = txt_file.read_text(encoding="utf-8", errors="replace").splitlines()
                    except OSError as exc:
                        logger.warning(
                            "KeywordIndex.build: could not read %s: %s — skipping.",
                            txt_file,
                            exc,
                        )
                        continue

                    for line_number, line_text in enumerate(lines, start=1):
                        total_lines += 1
                        # Strip the line for display but preserve the original
                        stripped = line_text.strip()
                        if not stripped:
                            # Skip blank lines — no useful content to index
                            continue

                        content = stripped[:_MAX_LINE_CONTENT]
                        entry = {
                            "source_id": source_id,
                            "line_number": line_number,
                            "content": content,
                        }
                        fh.write(json.dumps(entry, ensure_ascii=False))
                        fh.write("\n")
                        entries_written += 1

        except OSError as exc:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise LibraryIndexError(
                f"Failed to write keyword index to {tmp_path}: {exc}"
            ) from exc

        # Atomic rename
        try:
            os.replace(str(tmp_path), str(index_path))
        except OSError as exc:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise LibraryIndexError(
                f"Atomic rename failed for keyword index: {exc}"
            ) from exc

        logger.info(
            "KeywordIndex built: %d sources, %d total lines, %d index entries → %s",
            len(txt_files),
            total_lines,
            entries_written,
            index_path,
        )

        # Refresh in-memory cache from the freshly written file
        self._cache = self._load_index_from_disk(index_path)

    def search(self, query: str, max_results: int = 20) -> list[SearchHit]:
        """Search the keyword index for lines matching query.

        Performs case-folded substring matching. Returns up to max_results
        hits in the order they appear in the index (first-match-first).

        Args:
            query:       The search string. Case-insensitive substring
                         match. Leading/trailing whitespace is stripped.
            max_results: Maximum number of SearchHit results to return.
                         Must be > 0. Default 20.

        Returns:
            Ordered list of SearchHit instances.
            Empty list if no matches are found.

        Raises:
            LibraryIndexError: if the index has not been built and no
                pre-built keyword_index.jsonl exists on disk.
        """
        if max_results < 1:
            max_results = 1

        query_folded = query.strip().lower()
        if not query_folded:
            return []

        # Load index (from cache or disk)
        if self._cache is None:
            index_path = self._data_dir / _INDEX_FILENAME
            if not index_path.exists():
                raise LibraryIndexError(
                    f"No keyword index found at {index_path}. "
                    "Run 'heretic library rebuild-index' to build the index "
                    "after downloading sources."
                )
            self._cache = self._load_index_from_disk(index_path)

        # Build a line lookup for context: {source_id: {line_number: content}}
        # We build this lazily per source_id as hits accumulate.
        line_lookup: dict[str, dict[int, str]] = {}
        for entry in self._cache:
            sid = entry["source_id"]
            ln = entry["line_number"]
            if sid not in line_lookup:
                line_lookup[sid] = {}
            line_lookup[sid][ln] = entry["content"]

        hits: list[SearchHit] = []

        for entry in self._cache:
            if len(hits) >= max_results:
                break

            content = entry["content"]
            content_folded = content.lower()

            if query_folded not in content_folded:
                continue

            source_id = entry["source_id"]
            line_number = entry["line_number"]
            match_pos_in_content = content_folded.index(query_folded)

            # Build context window: 1 line before + match line + 1 line after
            lines_for_context: list[str] = []
            context_start_line = line_number  # default: just the match line

            source_lines = line_lookup.get(source_id, {})

            prev_content = source_lines.get(line_number - 1)
            if prev_content:
                lines_for_context.append(prev_content)
                context_start_line = line_number - 1

            lines_for_context.append(content)

            next_content = source_lines.get(line_number + 1)
            if next_content:
                lines_for_context.append(next_content)

            context_text = "\n".join(lines_for_context)

            # Adjust match_position relative to start of context_text
            if prev_content:
                # Match is in the second line of context_text
                match_position = len(prev_content) + 1 + match_pos_in_content
            else:
                match_position = match_pos_in_content

            hits.append(SearchHit(
                source_id=source_id,
                line_number=line_number,
                context_text=context_text,
                match_position=match_position,
            ))

        return hits

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _load_index_from_disk(index_path: Path) -> list[dict]:
        """Load keyword_index.jsonl into a list of entry dicts.

        Args:
            index_path: Path to the keyword_index.jsonl file.

        Returns:
            List of index entry dicts.

        Raises:
            LibraryIndexError: on read or parse failure.
        """
        entries: list[dict] = []
        try:
            with index_path.open("r", encoding="utf-8") as fh:
                for line_num, raw_line in enumerate(fh, start=1):
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        entry = json.loads(raw_line)
                        entries.append(entry)
                    except json.JSONDecodeError as exc:
                        logger.warning(
                            "KeywordIndex: skipping corrupt index line %d: %s",
                            line_num,
                            exc,
                        )
        except OSError as exc:
            raise LibraryIndexError(
                f"Could not read keyword index from {index_path}: {exc}"
            ) from exc

        return entries
