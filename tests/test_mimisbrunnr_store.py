"""
Tests for Mímisbrunnr store module — ensure_storage_directory is implemented.
Other store functions are NotImplementedError stubs (placeholder tests).

Covers:
    - ensure_storage_directory creates the directory
    - ensure_storage_directory is idempotent (calling twice is safe)
    - ensure_storage_directory creates nested paths
    - resolve_source_path raises NotImplementedError (scaffold placeholder)
    - load_local_manifest raises NotImplementedError (scaffold placeholder)
    - is_source_downloaded raises NotImplementedError (scaffold placeholder)

Ref: src/heretic/skilningr/mimisbrunnr/store.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from heretic.skilningr.mimisbrunnr.store import (
    ensure_storage_directory,
    is_source_downloaded,
    load_local_manifest,
    resolve_source_path,
)


class TestEnsureStorageDirectory:
    """ensure_storage_directory is fully implemented — test it properly."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """ensure_storage_directory must create the target directory."""
        target = tmp_path / "mimisbrunnr"
        assert not target.exists()
        ensure_storage_directory(target)
        assert target.is_dir()

    def test_idempotent_when_already_exists(self, tmp_path: Path) -> None:
        """Calling ensure_storage_directory on an existing dir must not raise."""
        target = tmp_path / "mimisbrunnr"
        ensure_storage_directory(target)
        # Second call must be safe
        ensure_storage_directory(target)
        assert target.is_dir()

    def test_creates_nested_paths(self, tmp_path: Path) -> None:
        """ensure_storage_directory must create intermediate parent directories."""
        target = tmp_path / "a" / "b" / "c" / "mimisbrunnr"
        assert not target.exists()
        ensure_storage_directory(target)
        assert target.is_dir()


class TestStoreStubs:
    """Placeholder tests — these will be replaced by Forge when stubs are implemented."""

    @pytest.mark.skip(reason="Forge implementation target — resolve_source_path body not yet written")
    def test_resolve_source_path_returns_expected_path(self, tmp_path: Path) -> None:
        """resolve_source_path should return data_dir / '<source_id>.txt'."""
        result = resolve_source_path(tmp_path, "prose_edda_brodeur")
        assert result == tmp_path / "prose_edda_brodeur.txt"

    @pytest.mark.skip(reason="Forge implementation target — load_local_manifest body not yet written")
    def test_load_local_manifest_returns_empty_when_absent(self, tmp_path: Path) -> None:
        """load_local_manifest should return {} when no manifest file exists."""
        result = load_local_manifest(tmp_path)
        assert result == {}

    @pytest.mark.skip(reason="Forge implementation target — is_source_downloaded body not yet written")
    def test_is_source_downloaded_false_when_file_absent(self, tmp_path: Path) -> None:
        """is_source_downloaded should return False when the .txt file is absent."""
        result = is_source_downloaded(tmp_path, "prose_edda_brodeur")
        assert result is False

    @pytest.mark.skip(reason="Forge implementation target — is_source_downloaded body not yet written")
    def test_is_source_downloaded_true_when_file_present(self, tmp_path: Path) -> None:
        """is_source_downloaded should return True when the .txt file exists and is non-empty."""
        source_file = tmp_path / "prose_edda_brodeur.txt"
        source_file.write_text("sample content", encoding="utf-8")
        result = is_source_downloaded(tmp_path, "prose_edda_brodeur")
        assert result is True
