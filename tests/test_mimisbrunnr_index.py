"""
Tests for Mímisbrunnr keyword index — KeywordIndex class.

Covers:
    - build creates keyword_index.jsonl
    - build raises LibraryIndexError when no .txt files present
    - build indexes multiple source files
    - build excludes blank lines from index
    - build truncates long lines to _MAX_LINE_CONTENT (200) chars
    - no .heretic_tmp left after successful build
    - search returns SearchHit with correct source_id and line_number
    - search is case-insensitive
    - search respects max_results cap
    - search returns empty list when no matches
    - search raises LibraryIndexError when no index on disk
    - search returns match_position pointing to first match character
    - search includes context from preceding and following lines
    - rebuild via build() refreshes in-memory cache

Ref: src/heretic/skilningr/mimisbrunnr/index.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from heretic.skilningr.mimisbrunnr.errors import LibraryIndexError
from heretic.skilningr.mimisbrunnr.index import KeywordIndex, SearchHit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_source(data_dir: Path, source_id: str, content: str) -> Path:
    """Write a source .txt file in data_dir and return the path."""
    path = data_dir / f"{source_id}.txt"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# build() tests
# ---------------------------------------------------------------------------

class TestKeywordIndexBuild:
    """Tests for KeywordIndex.build()."""

    def test_build_creates_jsonl_file(self, tmp_path: Path) -> None:
        _write_source(tmp_path, "prose_edda_brodeur", "Odin went to Yggdrasil.\nHe drank from the well.")
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        assert (tmp_path / "keyword_index.jsonl").exists()

    def test_build_raises_when_no_txt_files(self, tmp_path: Path) -> None:
        idx = KeywordIndex(tmp_path)
        with pytest.raises(LibraryIndexError, match="No downloaded .txt"):
            idx.build(tmp_path)

    def test_build_multiple_sources(self, tmp_path: Path) -> None:
        _write_source(tmp_path, "prose_edda_brodeur", "Odin spoke.\nThor listened.")
        _write_source(tmp_path, "erik_red_saga", "Erik sailed west.\nHe found land.")
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)

        index_path = tmp_path / "keyword_index.jsonl"
        entries = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
        source_ids = {e["source_id"] for e in entries}
        assert "prose_edda_brodeur" in source_ids
        assert "erik_red_saga" in source_ids

    def test_build_excludes_blank_lines(self, tmp_path: Path) -> None:
        content = "Odin spoke.\n\n\nThor listened.\n   \n"
        _write_source(tmp_path, "prose_edda_brodeur", content)
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)

        index_path = tmp_path / "keyword_index.jsonl"
        entries = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
        # Only 2 non-blank lines
        assert len(entries) == 2

    def test_build_truncates_long_lines(self, tmp_path: Path) -> None:
        long_line = "A" * 500
        _write_source(tmp_path, "prose_edda_brodeur", long_line)
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)

        index_path = tmp_path / "keyword_index.jsonl"
        entries = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
        assert len(entries) == 1
        assert len(entries[0]["content"]) <= 200

    def test_build_no_heretic_tmp_left_on_disk(self, tmp_path: Path) -> None:
        _write_source(tmp_path, "prose_edda_brodeur", "Odin.\nThor.")
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        tmp_files = list(tmp_path.glob("*.heretic_tmp"))
        assert tmp_files == []

    def test_build_records_correct_line_numbers(self, tmp_path: Path) -> None:
        content = "Line one.\nLine two.\nLine three."
        _write_source(tmp_path, "prose_edda_brodeur", content)
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)

        index_path = tmp_path / "keyword_index.jsonl"
        entries = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
        line_numbers = [e["line_number"] for e in entries]
        assert line_numbers == [1, 2, 3]

    def test_build_refreshes_in_memory_cache(self, tmp_path: Path) -> None:
        """After build(), search() should use the new cache without disk re-read."""
        _write_source(tmp_path, "prose_edda_brodeur", "Odin.\nFreya.")
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        hits = idx.search("Odin")
        assert len(hits) == 1

        # Rebuild with new content — cache must refresh
        _write_source(tmp_path, "prose_edda_brodeur", "Loki.\nThor.")
        idx.build(tmp_path)
        hits = idx.search("Loki")
        assert len(hits) == 1
        # Old content gone from cache
        hits_old = idx.search("Odin")
        assert len(hits_old) == 0


# ---------------------------------------------------------------------------
# search() tests
# ---------------------------------------------------------------------------

class TestKeywordIndexSearch:
    """Tests for KeywordIndex.search()."""

    @pytest.fixture
    def built_index(self, tmp_path: Path) -> KeywordIndex:
        content = (
            "Odin hung on Yggdrasil for nine days.\n"
            "He sacrificed himself to himself.\n"
            "From the Well of Mímir he drank wisdom.\n"
            "Thor wielded Mjolnir against the giants.\n"
            "Freya wept golden tears for Odin.\n"
        )
        _write_source(tmp_path, "prose_edda_brodeur", content)
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        return idx

    def test_search_returns_search_hit_instances(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("Odin")
        assert all(isinstance(h, SearchHit) for h in hits)

    def test_search_finds_exact_match(self, built_index: KeywordIndex) -> None:
        hits = built_index.search("Yggdrasil")
        assert len(hits) == 1
        assert hits[0].source_id == "prose_edda_brodeur"

    def test_search_case_insensitive_lowercase(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("odin")
        assert len(hits) >= 1

    def test_search_case_insensitive_uppercase(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("ODIN")
        assert len(hits) >= 1

    def test_search_case_insensitive_mixed(
        self, built_index: KeywordIndex
    ) -> None:
        hits_lower = built_index.search("odin")
        hits_upper = built_index.search("ODIN")
        hits_exact = built_index.search("Odin")
        assert len(hits_lower) == len(hits_upper) == len(hits_exact)

    def test_search_returns_empty_for_no_match(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("Beowulf")
        assert hits == []

    def test_search_respects_max_results(
        self, tmp_path: Path
    ) -> None:
        # Create a source with 20 matching lines
        content = "\n".join(f"Odin speaks line {i}" for i in range(20))
        _write_source(tmp_path, "prose_edda_brodeur", content)
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        hits = idx.search("Odin", max_results=3)
        assert len(hits) <= 3

    def test_search_returns_correct_source_id(
        self, tmp_path: Path
    ) -> None:
        _write_source(tmp_path, "prose_edda_brodeur", "Odin is wise.")
        _write_source(tmp_path, "erik_red_saga", "Erik sailed west.")
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        hits = idx.search("Erik")
        assert len(hits) == 1
        assert hits[0].source_id == "erik_red_saga"

    def test_search_returns_correct_line_number(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("Well of Mímir")
        assert len(hits) == 1
        # Line 3 has "From the Well of Mímir he drank wisdom."
        assert hits[0].line_number == 3

    def test_search_match_position_points_to_query(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("Yggdrasil")
        assert len(hits) == 1
        hit = hits[0]
        # match_position should be within context_text
        assert 0 <= hit.match_position < len(hit.context_text)
        # The character at match_position in context_text (case-insensitive) should start query
        assert hit.context_text[hit.match_position:].lower().startswith("yggdrasil")

    def test_search_context_text_contains_match_line(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("Yggdrasil")
        assert len(hits) == 1
        assert "Yggdrasil" in hits[0].context_text

    def test_search_raises_library_index_error_when_no_index(
        self, tmp_path: Path
    ) -> None:
        """search() without a prior build() and no index file must raise."""
        idx = KeywordIndex(tmp_path)
        with pytest.raises(LibraryIndexError, match="No keyword index"):
            idx.search("Odin")

    def test_search_loads_index_from_disk_without_build(
        self, tmp_path: Path
    ) -> None:
        """search() should load index from disk if file exists but cache is cold."""
        content = "Odin is wise.\nThor is strong."
        _write_source(tmp_path, "prose_edda_brodeur", content)

        # Build with one instance
        idx1 = KeywordIndex(tmp_path)
        idx1.build(tmp_path)

        # Search with a fresh instance — no cache
        idx2 = KeywordIndex(tmp_path)
        hits = idx2.search("Thor")
        assert len(hits) == 1

    def test_search_empty_query_returns_empty_list(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("")
        assert hits == []

    def test_search_whitespace_query_returns_empty_list(
        self, built_index: KeywordIndex
    ) -> None:
        hits = built_index.search("   ")
        assert hits == []
