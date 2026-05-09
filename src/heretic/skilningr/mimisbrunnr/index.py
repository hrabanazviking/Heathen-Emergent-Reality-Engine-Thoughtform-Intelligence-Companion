"""
Mímisbrunnr keyword index — line-level full-text search over downloaded sources.

KeywordIndex builds and searches a lightweight keyword index over the
plain-text source files in the Mímisbrunnr data_dir. The index is
intentionally simple at v0.7: no vector embeddings, no stemming, no
language model — just case-folded substring matching with line-level
context windows. This is the fastest path to a useful tool for the
agent with zero heavy dependencies.

The v0.7 index design:
    - Build: iterate every downloaded .txt file line by line; store
      the (source_id, line_number, line_text) tuples in a compact
      in-memory structure that is serialised to disk as a JSON-lines
      file (<data_dir>/keyword_index.jsonl).
    - Search: load the index (or use a cached in-memory copy if
      build() was already called); iterate all entries; return the
      top max_results hits scored by substring frequency, each
      returned as a SearchHit dataclass.
    - The index is rebuilt on each call to build(). Incremental
      updates are a v0.8 concern.

DESIGN CONTRACT (Forge implements the bodies):
    - build() raises LibraryIndexError if no sources have been
      downloaded (no .txt files found in data_dir).
    - search() raises LibraryIndexError if the index has not been
      built and no pre-built index file exists on disk.
    - Neither build() nor search() downloads any text — that is
      Downloader's responsibility.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Index
     src/heretic/skilningr/mimisbrunnr/errors.py (LibraryIndexError)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
            typically the matching line plus up to 2 lines of context.
            Forge determines the exact window size.
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

    Usage (Forge implements bodies):
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

    def build(self, data_dir: Path) -> None:
        """Build (or rebuild) the keyword index from downloaded sources.

        Iterates every *.txt file in data_dir, tokenises it line by line,
        and writes a serialised index to data_dir/keyword_index.jsonl.
        Any existing index file is replaced.

        Args:
            data_dir: The Mímisbrunnr data directory containing the
                      downloaded .txt source files.

        Raises:
            LibraryIndexError: if no downloaded .txt files are found
                in data_dir (nothing to index).
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "KeywordIndex.build is a Forge implementation target. "
            "Body: scan data_dir for *.txt; tokenise line-by-line; "
            "write (source_id, line_no, line_text) tuples to "
            "data_dir/keyword_index.jsonl."
        )

    def search(self, query: str, max_results: int = 20) -> list[SearchHit]:
        """Search the keyword index for lines matching query.

        Performs case-folded substring matching. Returns up to max_results
        hits ordered by relevance (frequency of match within context).

        Args:
            query:       The search string. Case-insensitive substring
                         match. Leading/trailing whitespace is stripped.
            max_results: Maximum number of SearchHit results to return.
                         Must be > 0. Default 20 (mirrors LibraryConfig).

        Returns:
            Ordered list of SearchHit instances, best match first.
            Empty list if no matches are found.

        Raises:
            LibraryIndexError: if the index has not been built and no
                pre-built index file exists on disk.
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "KeywordIndex.search is a Forge implementation target. "
            "Body: load keyword_index.jsonl; iterate entries; "
            "case-fold substring match on query; return top max_results "
            "as SearchHit instances."
        )
