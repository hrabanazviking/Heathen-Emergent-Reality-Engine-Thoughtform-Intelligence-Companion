"""
Tests for LibraryClient — sense-level corpus access client.

Covers:
    - search delegates to KeywordIndex.search and returns list of dicts
    - search result dicts have required keys
    - search respects max_results cap
    - search case-insensitive
    - search raises LibraryError when index not built
    - get_text returns dict with required keys
    - get_text returns correct text slice
    - get_text raises LibraryError for unknown source_id
    - get_text raises LibraryError for un-downloaded source
    - get_text raises LibraryError when start_line > total_lines
    - get_text clamps start_line to 1 minimum
    - list_sources returns all 5 starter-pack sources
    - list_sources downloaded flag reflects actual state
    - list_sources sha256 is None for not-yet-downloaded source
    - list_sources sha256 is populated from local manifest
    - LibraryClient MUST NOT import httpx (offline invariant)

Ref: src/heretic/skilningr/senses/library/client.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from heretic.skilningr.config_model import LibraryConfig
from heretic.skilningr.mimisbrunnr.index import KeywordIndex
from heretic.skilningr.mimisbrunnr.store import update_local_manifest
from heretic.skilningr.senses.library.client import LibraryClient
from heretic.skilningr.senses.library.errors import LibraryError


# ---------------------------------------------------------------------------
# Offline invariant test (Cartographer thread #1)
# ---------------------------------------------------------------------------

class TestOfflineInvariant:
    """LibraryClient must never import httpx — structural offline enforcement."""

    def test_client_module_does_not_import_httpx(self) -> None:
        """httpx must not be an actual import in client.py.

        The offline invariant: only Downloader may import httpx.
        We check the module's actual namespace — if 'httpx' is a bound
        module object in the globals, the invariant is violated.
        """
        import heretic.skilningr.senses.library.client as client_module
        import types
        module_globals = vars(client_module)
        # Check if httpx is bound as an actual module in the namespace
        assert "httpx" not in module_globals, (
            "LibraryClient module has 'httpx' in its globals. "
            "This breaks the offline invariant. "
            "Only Downloader is permitted to import httpx."
        )

    def test_httpx_not_in_client_module_globals(self) -> None:
        """No httpx module object should appear in the client module's globals."""
        import heretic.skilningr.senses.library.client as client_module
        import types
        module_globals = vars(client_module)
        # httpx module object must not be a value in the module namespace
        for name, value in module_globals.items():
            if isinstance(value, types.ModuleType) and value.__name__ == "httpx":
                pytest.fail(
                    f"httpx module found as {name!r} in LibraryClient globals. "
                    "Offline invariant violated."
                )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_data_dir(tmp_path: Path) -> Path:
    """data_dir with a pre-built index over a prose_edda_brodeur.txt stub."""
    content = (
        "Odin hung on Yggdrasil for nine nights.\n"
        "He sacrificed himself to himself.\n"
        "From the Well of Mimir he drank wisdom.\n"
        "Thor wielded Mjolnir.\n"
        "Freya wept tears of gold.\n"
    )
    (tmp_path / "prose_edda_brodeur.txt").write_text(content, encoding="utf-8")
    idx = KeywordIndex(tmp_path)
    idx.build(tmp_path)
    return tmp_path


@pytest.fixture
def client_with_data(simple_data_dir: Path) -> LibraryClient:
    return LibraryClient(LibraryConfig(enabled=True, max_results=20), simple_data_dir)


@pytest.fixture
def client_empty(tmp_path: Path) -> LibraryClient:
    """Client with an empty data_dir (no sources downloaded, no index)."""
    return LibraryClient(LibraryConfig(enabled=True, max_results=20), tmp_path)


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

class TestLibraryClientSearch:
    """Tests for LibraryClient.search()."""

    def test_search_returns_list(self, client_with_data: LibraryClient) -> None:
        results = client_with_data.search("Odin", max_results=5)
        assert isinstance(results, list)

    def test_search_results_have_required_keys(
        self, client_with_data: LibraryClient
    ) -> None:
        results = client_with_data.search("Odin", max_results=5)
        for hit in results:
            assert "source_id" in hit
            assert "line_number" in hit
            assert "context_text" in hit
            assert "match_position" in hit

    def test_search_finds_match(self, client_with_data: LibraryClient) -> None:
        results = client_with_data.search("Yggdrasil")
        assert len(results) >= 1

    def test_search_respects_max_results(self, client_with_data: LibraryClient) -> None:
        results = client_with_data.search("the", max_results=2)
        assert len(results) <= 2

    def test_search_case_insensitive(self, client_with_data: LibraryClient) -> None:
        results_lower = client_with_data.search("odin")
        results_upper = client_with_data.search("ODIN")
        assert len(results_lower) == len(results_upper)

    def test_search_returns_empty_for_no_match(
        self, client_with_data: LibraryClient
    ) -> None:
        results = client_with_data.search("Beowulf_xyz_not_in_corpus")
        assert results == []

    def test_search_raises_library_error_when_no_index(
        self, client_empty: LibraryClient
    ) -> None:
        with pytest.raises(LibraryError):
            client_empty.search("Odin")

    def test_search_config_max_results_caps_results(self, tmp_path: Path) -> None:
        """config.max_results must cap results even if max_results arg is higher."""
        content = "\n".join(f"Odin line {i}" for i in range(50))
        (tmp_path / "prose_edda_brodeur.txt").write_text(content, encoding="utf-8")
        idx = KeywordIndex(tmp_path)
        idx.build(tmp_path)
        # Config max_results = 5
        client = LibraryClient(
            LibraryConfig(enabled=True, max_results=5), tmp_path
        )
        results = client.search("Odin", max_results=100)
        assert len(results) <= 5


# ---------------------------------------------------------------------------
# get_text()
# ---------------------------------------------------------------------------

class TestLibraryClientGetText:
    """Tests for LibraryClient.get_text()."""

    def test_get_text_returns_dict(
        self, client_with_data: LibraryClient
    ) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 1, 3)
        assert isinstance(result, dict)

    def test_get_text_has_required_keys(
        self, client_with_data: LibraryClient
    ) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 1, 3)
        assert "source_id" in result
        assert "start_line" in result
        assert "num_lines" in result
        assert "text" in result
        assert "total_lines_in_file" in result

    def test_get_text_correct_content(
        self, client_with_data: LibraryClient
    ) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 1, 1)
        assert "Odin" in result["text"]

    def test_get_text_correct_line_count(
        self, client_with_data: LibraryClient
    ) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 1, 3)
        assert result["num_lines"] == 3

    def test_get_text_line_3(self, client_with_data: LibraryClient) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 3, 1)
        # Line 3 is "From the Well of Mimir he drank wisdom."
        assert "Mimir" in result["text"]

    def test_get_text_clamps_start_line_to_1(
        self, client_with_data: LibraryClient
    ) -> None:
        """start_line < 1 should be clamped to 1."""
        result = client_with_data.get_text("prose_edda_brodeur", 0, 1)
        assert result["start_line"] == 1

    def test_get_text_raises_for_unknown_source_id(
        self, client_with_data: LibraryClient
    ) -> None:
        with pytest.raises(LibraryError, match="Unknown source_id"):
            client_with_data.get_text("does_not_exist_xyz", 1, 5)

    def test_get_text_raises_for_undownloaded_source(
        self, tmp_path: Path
    ) -> None:
        """get_text must raise LibraryError if the source file doesn't exist."""
        client = LibraryClient(LibraryConfig(enabled=True), tmp_path)
        with pytest.raises(LibraryError, match="not been downloaded"):
            client.get_text("poetic_edda_bellows", 1, 5)

    def test_get_text_raises_when_start_line_beyond_file(
        self, client_with_data: LibraryClient
    ) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 1, 1)
        total_lines = result["total_lines_in_file"]
        with pytest.raises(LibraryError, match="beyond the end"):
            client_with_data.get_text("prose_edda_brodeur", total_lines + 100, 1)

    def test_get_text_at_end_of_file_returns_partial(
        self, client_with_data: LibraryClient
    ) -> None:
        result = client_with_data.get_text("prose_edda_brodeur", 4, 100)
        # File has 5 lines; starting at 4 with 100 requested → should return 2
        assert result["num_lines"] == 2


# ---------------------------------------------------------------------------
# list_sources()
# ---------------------------------------------------------------------------

class TestLibraryClientListSources:
    """Tests for LibraryClient.list_sources()."""

    def test_list_sources_returns_exactly_five(
        self, client_empty: LibraryClient
    ) -> None:
        sources = client_empty.list_sources()
        assert len(sources) == 5

    def test_list_sources_has_required_keys(
        self, client_empty: LibraryClient
    ) -> None:
        sources = client_empty.list_sources()
        for s in sources:
            assert "id" in s
            assert "title" in s
            assert "url" in s
            assert "license" in s
            assert "expected_size_bytes" in s
            assert "downloaded" in s
            assert "sha256" in s

    def test_list_sources_downloaded_false_when_not_present(
        self, client_empty: LibraryClient
    ) -> None:
        sources = client_empty.list_sources()
        for s in sources:
            assert s["downloaded"] is False

    def test_list_sources_downloaded_true_when_present(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "prose_edda_brodeur.txt").write_text(
            "content", encoding="utf-8"
        )
        client = LibraryClient(LibraryConfig(enabled=True), tmp_path)
        sources = client.list_sources()
        downloaded = {s["id"]: s["downloaded"] for s in sources}
        assert downloaded["prose_edda_brodeur"] is True
        assert downloaded["erik_red_saga"] is False

    def test_list_sources_sha256_none_for_not_downloaded(
        self, client_empty: LibraryClient
    ) -> None:
        sources = client_empty.list_sources()
        for s in sources:
            assert s["sha256"] is None

    def test_list_sources_sha256_from_local_manifest(
        self, tmp_path: Path
    ) -> None:
        update_local_manifest(
            tmp_path, "prose_edda_brodeur", sha256="deadbeef1234"
        )
        client = LibraryClient(LibraryConfig(enabled=True), tmp_path)
        sources = client.list_sources()
        edda = next(s for s in sources if s["id"] == "prose_edda_brodeur")
        assert edda["sha256"] == "deadbeef1234"

    def test_list_sources_all_five_ids_present(
        self, client_empty: LibraryClient
    ) -> None:
        expected = {
            "prose_edda_brodeur",
            "poetic_edda_bellows",
            "heimskringla_laing",
            "volsunga_saga_morris",
            "erik_red_saga",
        }
        sources = client_empty.list_sources()
        actual = {s["id"] for s in sources}
        assert actual == expected
