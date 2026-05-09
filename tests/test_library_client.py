"""
Placeholder tests for LibraryClient.

All test bodies are skipped at scaffold time — they represent the Forge
implementation contract. Unskip each when the corresponding client method
body is implemented.

Covers (pending Forge implementation):
    - search: returns list of dicts with required keys
    - search: respects max_results cap
    - search: case-insensitive match
    - get_text: returns correct text slice
    - get_text: raises LibraryError for unknown source_id
    - get_text: raises LibraryError for un-downloaded source
    - list_sources: returns all 5 starter-pack sources
    - list_sources: downloaded flag reflects actual state

Ref: src/heretic/skilningr/senses/library/client.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from heretic.skilningr.config_model import LibraryConfig
from heretic.skilningr.senses.library.client import LibraryClient


@pytest.mark.skip(reason="Forge implementation target — LibraryClient.search not yet implemented")
def test_search_returns_list_of_dicts(tmp_path: Path) -> None:
    """search() must return a list of dicts with source_id, line_number,
    context_text, match_position keys."""
    config = LibraryConfig(enabled=True)
    client = LibraryClient(config, tmp_path)
    results = client.search("Odin", max_results=5)
    assert isinstance(results, list)
    for hit in results:
        assert "source_id" in hit
        assert "line_number" in hit
        assert "context_text" in hit
        assert "match_position" in hit


@pytest.mark.skip(reason="Forge implementation target — LibraryClient.search not yet implemented")
def test_search_respects_max_results(tmp_path: Path) -> None:
    """search() must return no more than max_results hits."""
    config = LibraryConfig(enabled=True)
    client = LibraryClient(config, tmp_path)
    results = client.search("the", max_results=3)
    assert len(results) <= 3


@pytest.mark.skip(reason="Forge implementation target — LibraryClient.get_text not yet implemented")
def test_get_text_returns_dict_with_text_key(tmp_path: Path) -> None:
    """get_text() must return a dict with a 'text' key containing a string."""
    config = LibraryConfig(enabled=True)
    client = LibraryClient(config, tmp_path)
    result = client.get_text("prose_edda_brodeur", start_line=1, num_lines=10)
    assert isinstance(result, dict)
    assert "text" in result
    assert isinstance(result["text"], str)


@pytest.mark.skip(reason="Forge implementation target — LibraryClient.list_sources not yet implemented")
def test_list_sources_returns_all_five(tmp_path: Path) -> None:
    """list_sources() must return exactly 5 dicts (one per starter pack source)."""
    config = LibraryConfig(enabled=True)
    client = LibraryClient(config, tmp_path)
    sources = client.list_sources()
    assert len(sources) == 5


@pytest.mark.skip(reason="Forge implementation target — LibraryClient.list_sources not yet implemented")
def test_list_sources_includes_downloaded_flag(tmp_path: Path) -> None:
    """Each source dict from list_sources() must include a 'downloaded' bool key."""
    config = LibraryConfig(enabled=True)
    client = LibraryClient(config, tmp_path)
    sources = client.list_sources()
    for source in sources:
        assert "downloaded" in source
        assert isinstance(source["downloaded"], bool)
