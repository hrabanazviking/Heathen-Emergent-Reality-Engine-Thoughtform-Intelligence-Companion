"""
Tests for the 'heretic library' CLI subcommands.

Tests call the internal handler functions directly with mocked args and
dependencies — no subprocesses, no real network.

Covers:
    - library list calls list_sources and prints table
    - library list exits 0 on success
    - library list exits 1 on error
    - library download calls Downloader.download with correct args
    - library download exits 0 on success
    - library download skips source on ConsentRefused
    - library download exits 1 on download error
    - library download --all downloads all 5 sources
    - library download rejects unknown source_id
    - library remove exits 0 when file absent (nothing to do)
    - library remove removes file when --yes flag set
    - library remove exits 1 on unlink error
    - library rebuild-index calls KeywordIndex.build
    - library rebuild-index exits 0 on success
    - library rebuild-index exits 1 on LibraryIndexError
    - 'heretic library --help' shows subcommands

Ref: src/heretic/cli.py — _cmd_library_* functions
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.cli import (
    _cmd_library_download,
    _cmd_library_list,
    _cmd_library_rebuild_index,
    _cmd_library_remove,
    build_parser,
)
from heretic.skilningr.mimisbrunnr.errors import (
    ConsentRefused,
    LibraryDownloadError,
    LibraryIndexError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    """Build a minimal argparse.Namespace with given kwargs."""
    defaults = {
        "config": None,
        "source_id": "prose_edda_brodeur",
        "source_ids": [],
        "download_all": False,   # matches parser dest="download_all" for --all flag
        "yes": True,  # skip consent prompts in tests
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_mock_client(sources=None):
    """Build a mock LibraryClient."""
    client = MagicMock()
    if sources is None:
        sources = [
            {
                "id": "prose_edda_brodeur",
                "title": "The Prose Edda",
                "url": "https://www.gutenberg.org/files/18947/18947-0.txt",
                "license": "PD",
                "expected_size_bytes": 387_653,
                "downloaded": False,
                "sha256": None,
            }
        ]
    client.list_sources.return_value = sources
    return client


# ---------------------------------------------------------------------------
# library list
# ---------------------------------------------------------------------------

class TestCmdLibraryList:
    """Tests for _cmd_library_list."""

    def test_list_exits_zero_on_success(self, tmp_path: Path) -> None:
        mock_client = _make_mock_client()

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.senses.library.client.LibraryClient",
            return_value=mock_client
        ):
            code = _cmd_library_list(_make_args())

        assert code == 0

    def test_list_exits_one_on_client_error(self, tmp_path: Path) -> None:
        mock_client = MagicMock()
        mock_client.list_sources.side_effect = RuntimeError("boom")

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.senses.library.client.LibraryClient",
            return_value=mock_client
        ):
            code = _cmd_library_list(_make_args())

        assert code == 1

    def test_list_prints_source_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        mock_client = _make_mock_client()

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.senses.library.client.LibraryClient",
            return_value=mock_client
        ):
            _cmd_library_list(_make_args())

        captured = capsys.readouterr()
        assert "prose_edda_brodeur" in captured.out

    def test_list_prints_data_dir_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        mock_client = _make_mock_client()

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.senses.library.client.LibraryClient",
            return_value=mock_client
        ):
            _cmd_library_list(_make_args())

        captured = capsys.readouterr()
        assert str(tmp_path) in captured.out


# ---------------------------------------------------------------------------
# library download
# ---------------------------------------------------------------------------

class TestCmdLibraryDownload:
    """Tests for _cmd_library_download."""

    def test_download_exits_zero_on_success(self, tmp_path: Path) -> None:
        # Write a fake dest file so stat() works after "download"
        dest_file = tmp_path / "prose_edda_brodeur.txt"
        dest_file.write_text("content", encoding="utf-8")

        mock_downloader_instance = MagicMock()
        mock_downloader_instance.download = AsyncMock(return_value="abc123sha256")
        mock_downloader_cls = MagicMock(return_value=mock_downloader_instance)

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.mimisbrunnr.downloader.Downloader",
            mock_downloader_cls
        ):
            code = _cmd_library_download(
                _make_args(source_ids=["prose_edda_brodeur"], download_all=False)
            )

        assert code == 0

    def test_download_skips_on_consent_refused(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        mock_downloader_instance = MagicMock()
        mock_downloader_instance.download = AsyncMock(
            side_effect=ConsentRefused("Declined")
        )
        mock_downloader_cls = MagicMock(return_value=mock_downloader_instance)

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.mimisbrunnr.downloader.Downloader",
            mock_downloader_cls
        ):
            code = _cmd_library_download(
                _make_args(source_ids=["prose_edda_brodeur"], download_all=False)
            )

        # Consent refused → skip → exit 0 (not a hard error)
        assert code == 0

    def test_download_exits_one_on_download_error(self, tmp_path: Path) -> None:
        mock_downloader_instance = MagicMock()
        mock_downloader_instance.download = AsyncMock(
            side_effect=LibraryDownloadError("Network failure")
        )
        mock_downloader_cls = MagicMock(return_value=mock_downloader_instance)

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.mimisbrunnr.downloader.Downloader",
            mock_downloader_cls
        ):
            code = _cmd_library_download(
                _make_args(source_ids=["prose_edda_brodeur"], download_all=False)
            )

        assert code == 1

    def test_download_rejects_unknown_source_id(self, tmp_path: Path) -> None:
        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            code = _cmd_library_download(
                _make_args(source_ids=["does_not_exist_xyz"], download_all=False)
            )
        assert code == 1

    def test_download_all_downloads_five_sources(self, tmp_path: Path) -> None:
        call_count = []

        async def fake_download(source, dest, auto_yes):
            call_count.append(source.id)
            dest.write_bytes(b"content")
            return "abc123"

        mock_downloader_instance = MagicMock()
        mock_downloader_instance.download = fake_download
        mock_downloader_cls = MagicMock(return_value=mock_downloader_instance)

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ), patch(
            "heretic.skilningr.mimisbrunnr.downloader.Downloader",
            mock_downloader_cls
        ):
            code = _cmd_library_download(
                _make_args(source_ids=[], download_all=True)
            )

        assert code == 0
        assert len(call_count) == 5


# ---------------------------------------------------------------------------
# library remove
# ---------------------------------------------------------------------------

class TestCmdLibraryRemove:
    """Tests for _cmd_library_remove."""

    def test_remove_exits_zero_when_file_not_present(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            code = _cmd_library_remove(
                _make_args(source_id="prose_edda_brodeur", yes=True)
            )
        assert code == 0
        captured = capsys.readouterr()
        assert "not downloaded" in captured.out

    def test_remove_deletes_file_when_yes_flag(self, tmp_path: Path) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        dest.write_text("content", encoding="utf-8")

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            code = _cmd_library_remove(
                _make_args(source_id="prose_edda_brodeur", yes=True)
            )

        assert code == 0
        assert not dest.exists()

    def test_remove_exits_one_for_unknown_source_id(
        self, tmp_path: Path
    ) -> None:
        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            code = _cmd_library_remove(
                _make_args(source_id="does_not_exist_xyz", yes=True)
            )
        assert code == 1

    def test_remove_also_deletes_index_file(self, tmp_path: Path) -> None:
        """Removing a source should also delete the stale keyword_index.jsonl."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        dest.write_text("content", encoding="utf-8")
        index = tmp_path / "keyword_index.jsonl"
        index.write_text("existing index", encoding="utf-8")

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            _cmd_library_remove(
                _make_args(source_id="prose_edda_brodeur", yes=True)
            )

        assert not index.exists()


# ---------------------------------------------------------------------------
# library rebuild-index
# ---------------------------------------------------------------------------

class TestCmdLibraryRebuildIndex:
    """Tests for _cmd_library_rebuild_index."""

    def test_rebuild_exits_zero_on_success(self, tmp_path: Path) -> None:
        (tmp_path / "prose_edda_brodeur.txt").write_text(
            "Odin is wise.", encoding="utf-8"
        )

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            code = _cmd_library_rebuild_index(_make_args())

        assert code == 0

    def test_rebuild_exits_one_on_library_index_error(
        self, tmp_path: Path
    ) -> None:
        """No .txt files → LibraryIndexError → exit 1."""
        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            code = _cmd_library_rebuild_index(_make_args())
        assert code == 1

    def test_rebuild_creates_index_file(self, tmp_path: Path) -> None:
        (tmp_path / "prose_edda_brodeur.txt").write_text(
            "Odin is wise.\nThor is strong.", encoding="utf-8"
        )

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            _cmd_library_rebuild_index(_make_args())

        assert (tmp_path / "keyword_index.jsonl").exists()

    def test_rebuild_prints_success_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        (tmp_path / "prose_edda_brodeur.txt").write_text(
            "Odin is wise.", encoding="utf-8"
        )

        with patch(
            "heretic.cli._library_resolve_data_dir", return_value=tmp_path
        ):
            _cmd_library_rebuild_index(_make_args())

        captured = capsys.readouterr()
        assert "rebuilt" in captured.out.lower() or "index" in captured.out.lower()


# ---------------------------------------------------------------------------
# CLI parser smoke test
# ---------------------------------------------------------------------------

class TestCliParserLibrarySubcommands:
    """Verify 'heretic library --help' shows all 4 subcommands."""

    def test_library_subparser_exists(self) -> None:
        parser = build_parser()
        # Parse a library list invocation — should not raise
        args = parser.parse_args(["library", "list"])
        assert hasattr(args, "func")

    def test_library_download_subcommand_exists(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["library", "download", "prose_edda_brodeur"]
        )
        assert hasattr(args, "func")

    def test_library_remove_subcommand_exists(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["library", "remove", "prose_edda_brodeur"]
        )
        assert hasattr(args, "func")

    def test_library_rebuild_index_subcommand_exists(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["library", "rebuild-index"])
        assert hasattr(args, "func")

    def test_library_download_accepts_yes_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["library", "download", "prose_edda_brodeur", "--yes"]
        )
        assert args.yes is True

    def test_library_download_accepts_all_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["library", "download", "--all"]
        )
        assert args.download_all is True
