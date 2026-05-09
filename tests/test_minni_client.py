"""
Tests for MinniClient — sandboxed filesystem operations.

Covers:
    - Sandbox gateway (_validate_path)
    - read_file: happy path, not-found, too-large, permission error, UTF-8 replace
    - write_file: happy path (create), overwrite, too-large, parent sandbox violation,
                  atomic write (tmp cleanup on error)
    - list_directory: flat listing, recursive, not-found, not-a-directory

All tests use tmp_path fixture — no real filesystem writes outside pytest's temp dir.

Ref: src/heretic/skilningr/senses/minni/client.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from heretic.skilningr.config_model import MinniConfig
from heretic.skilningr.senses.minni.client import MinniClient
from heretic.skilningr.senses.minni.errors import (
    MinniFileNotFoundError,
    MinniFileTooLargeError,
    MinniPermissionError,
    MinniSandboxViolation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client(tmp_path: Path, **kwargs) -> MinniClient:
    """Return a MinniClient sandboxed to tmp_path."""
    config = MinniConfig(allowed_roots=[str(tmp_path)], **kwargs)
    return MinniClient(config)


# ---------------------------------------------------------------------------
# Sandbox gateway — _validate_path
# ---------------------------------------------------------------------------

class TestMinniClientSandboxGateway:

    def test_validate_path_within_root_accepted(self, tmp_path):
        """_validate_path accepts a path within allowed_roots."""
        client = make_client(tmp_path)
        target = str(tmp_path / "notes.md")
        resolved = client._validate_path(target)
        assert resolved.is_absolute()
        assert str(tmp_path) in str(resolved)

    def test_validate_path_outside_root_raises(self, tmp_path):
        """_validate_path raises MinniSandboxViolation for paths outside roots."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        config = MinniConfig(allowed_roots=[str(workspace)])
        client = MinniClient(config)
        with pytest.raises(MinniSandboxViolation):
            client._validate_path(str(tmp_path / "secret.txt"))

    def test_validate_path_traversal_blocked(self, tmp_path):
        """_validate_path rejects traversal that escapes the sandbox."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        config = MinniConfig(allowed_roots=[str(workspace)])
        client = MinniClient(config)
        # ../escape path
        traversal = str(workspace / ".." / "secret.txt")
        with pytest.raises(MinniSandboxViolation):
            client._validate_path(traversal)

    def test_validate_path_root_itself_accepted(self, tmp_path):
        """_validate_path accepts the root directory itself."""
        client = make_client(tmp_path)
        resolved = client._validate_path(str(tmp_path))
        assert resolved.is_absolute()

    def test_validate_path_empty_allowed_roots_raises(self, tmp_path):
        """_validate_path raises when allowed_roots is empty."""
        config = MinniConfig(allowed_roots=[])
        client = MinniClient(config)
        with pytest.raises(MinniSandboxViolation):
            client._validate_path(str(tmp_path / "notes.md"))


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

class TestMinniClientReadFile:

    def test_read_within_sandbox(self, tmp_path):
        """read_file returns content for a file within allowed_roots."""
        f = tmp_path / "notes.md"
        f.write_text("hello world", encoding="utf-8")
        client = make_client(tmp_path)
        result = client.read_file(str(f))
        assert result["content"] == "hello world"
        assert result["size_bytes"] == len("hello world".encode("utf-8"))
        assert result["path"] == str(f)
        assert result["encoding"] == "utf-8"

    def test_read_file_not_found_raises(self, tmp_path):
        """read_file raises MinniFileNotFoundError for missing files."""
        client = make_client(tmp_path)
        with pytest.raises(MinniFileNotFoundError):
            client.read_file(str(tmp_path / "nonexistent.txt"))

    def test_read_file_too_large_raises(self, tmp_path):
        """read_file raises MinniFileTooLargeError when file exceeds max_read_bytes."""
        f = tmp_path / "big.txt"
        f.write_text("x" * 100, encoding="utf-8")
        config = MinniConfig(allowed_roots=[str(tmp_path)], max_read_bytes=10)
        client = MinniClient(config)
        with pytest.raises(MinniFileTooLargeError):
            client.read_file(str(f))

    def test_read_file_outside_sandbox_raises(self, tmp_path):
        """read_file raises MinniSandboxViolation for paths outside allowed_roots."""
        workspace = tmp_path / "ws"
        workspace.mkdir()
        secret = tmp_path / "secret.txt"
        secret.write_text("private", encoding="utf-8")
        config = MinniConfig(allowed_roots=[str(workspace)])
        client = MinniClient(config)
        with pytest.raises(MinniSandboxViolation):
            client.read_file(str(secret))

    def test_read_file_utf8_errors_replaced(self, tmp_path):
        """read_file decodes with errors='replace' — does not crash on invalid bytes."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\xff\xfe hello world")
        client = make_client(tmp_path)
        result = client.read_file(str(f))
        # Should not raise; content should contain replacement characters or text
        assert isinstance(result["content"], str)

    def test_read_file_directory_raises(self, tmp_path):
        """read_file raises MinniFileNotFoundError when path is a directory."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        client = make_client(tmp_path)
        with pytest.raises(MinniFileNotFoundError, match="not a file"):
            client.read_file(str(subdir))

    def test_read_file_permission_error_mapped(self, tmp_path):
        """read_file maps OS PermissionError to MinniPermissionError."""
        f = tmp_path / "locked.txt"
        f.write_text("data", encoding="utf-8")
        client = make_client(tmp_path)
        with patch.object(Path, "read_bytes", side_effect=PermissionError("denied")):
            with pytest.raises(MinniPermissionError):
                client.read_file(str(f))


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

class TestMinniClientWriteFile:

    def test_write_creates_new_file(self, tmp_path):
        """write_file creates a new file and returns created=True."""
        client = make_client(tmp_path)
        target = str(tmp_path / "output.txt")
        result = client.write_file(target, "hello forge")
        assert result["created"] is True
        assert result["bytes_written"] == len("hello forge".encode("utf-8"))
        assert Path(target).read_text(encoding="utf-8") == "hello forge"

    def test_write_overwrites_existing_file(self, tmp_path):
        """write_file overwrites an existing file and returns created=False."""
        f = tmp_path / "existing.txt"
        f.write_text("old content", encoding="utf-8")
        client = make_client(tmp_path)
        result = client.write_file(str(f), "new content")
        assert result["created"] is False
        assert f.read_text(encoding="utf-8") == "new content"

    def test_write_creates_parent_directories(self, tmp_path):
        """write_file creates missing parent directories within the sandbox."""
        client = make_client(tmp_path)
        target = str(tmp_path / "deep" / "nested" / "file.txt")
        result = client.write_file(target, "deep content")
        assert Path(target).exists()
        assert result["created"] is True

    def test_write_content_too_large_raises(self, tmp_path):
        """write_file raises MinniFileTooLargeError for oversized content."""
        config = MinniConfig(allowed_roots=[str(tmp_path)], max_write_bytes=5)
        client = MinniClient(config)
        with pytest.raises(MinniFileTooLargeError):
            client.write_file(str(tmp_path / "big.txt"), "too much content here")

    def test_write_outside_sandbox_raises(self, tmp_path):
        """write_file raises MinniSandboxViolation for paths outside allowed_roots."""
        workspace = tmp_path / "ws"
        workspace.mkdir()
        config = MinniConfig(allowed_roots=[str(workspace)])
        client = MinniClient(config)
        with pytest.raises(MinniSandboxViolation):
            client.write_file(str(tmp_path / "evil.txt"), "escape")

    def test_write_atomic_no_corruption_on_error(self, tmp_path):
        """write_file atomic rename: original file is not corrupted if write fails mid-way."""
        f = tmp_path / "original.txt"
        f.write_text("safe content", encoding="utf-8")
        client = make_client(tmp_path)
        # Simulate os.replace failing
        with patch("os.replace", side_effect=OSError("disk full")):
            with pytest.raises(MinniPermissionError):
                client.write_file(str(f), "new content")
        # Original content must be intact
        assert f.read_text(encoding="utf-8") == "safe content"

    def test_write_returns_correct_path(self, tmp_path):
        """write_file returns the resolved absolute path in the result dict."""
        client = make_client(tmp_path)
        target = str(tmp_path / "result.txt")
        result = client.write_file(target, "test")
        assert os.path.isabs(result["path"])


# ---------------------------------------------------------------------------
# list_directory
# ---------------------------------------------------------------------------

class TestMinniClientListDirectory:

    def test_list_directory_flat(self, tmp_path):
        """list_directory returns immediate children when recurse=False."""
        (tmp_path / "a.txt").write_text("a", encoding="utf-8")
        (tmp_path / "b.txt").write_text("b", encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        client = make_client(tmp_path)
        result = client.list_directory(str(tmp_path), recurse=False)
        assert result["recurse"] is False
        names = {e["name"] for e in result["entries"]}
        assert "a.txt" in names
        assert "b.txt" in names
        assert "subdir" in names
        assert result["total_entries"] == 3

    def test_list_directory_recurse(self, tmp_path):
        """list_directory recurses into subdirectories when recurse=True."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.txt").write_text("r", encoding="utf-8")
        (subdir / "nested.txt").write_text("n", encoding="utf-8")
        client = make_client(tmp_path)
        result = client.list_directory(str(tmp_path), recurse=True)
        assert result["recurse"] is True
        names = {e["name"] for e in result["entries"]}
        assert "root.txt" in names
        assert "nested.txt" in names

    def test_list_directory_not_found_raises(self, tmp_path):
        """list_directory raises MinniFileNotFoundError for missing directories."""
        client = make_client(tmp_path)
        with pytest.raises(MinniFileNotFoundError):
            client.list_directory(str(tmp_path / "nonexistent"), recurse=False)

    def test_list_directory_file_path_raises(self, tmp_path):
        """list_directory raises MinniFileNotFoundError when path is a file."""
        f = tmp_path / "file.txt"
        f.write_text("data", encoding="utf-8")
        client = make_client(tmp_path)
        with pytest.raises(MinniFileNotFoundError, match="not a directory"):
            client.list_directory(str(f), recurse=False)

    def test_list_directory_outside_sandbox_raises(self, tmp_path):
        """list_directory raises MinniSandboxViolation for paths outside sandbox."""
        workspace = tmp_path / "ws"
        workspace.mkdir()
        config = MinniConfig(allowed_roots=[str(workspace)])
        client = MinniClient(config)
        with pytest.raises(MinniSandboxViolation):
            client.list_directory(str(tmp_path), recurse=False)

    def test_list_directory_entry_types(self, tmp_path):
        """list_directory correctly classifies entries as file or directory."""
        (tmp_path / "f.txt").write_text("x", encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        client = make_client(tmp_path)
        result = client.list_directory(str(tmp_path), recurse=False)
        entry_map = {e["name"]: e["type"] for e in result["entries"]}
        assert entry_map["f.txt"] == "file"
        assert entry_map["subdir"] == "directory"

    def test_list_directory_file_size_bytes(self, tmp_path):
        """list_directory reports size_bytes for files and None for directories."""
        content = "hello"
        (tmp_path / "sized.txt").write_text(content, encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        client = make_client(tmp_path)
        result = client.list_directory(str(tmp_path), recurse=False)
        entry_map = {e["name"]: e for e in result["entries"]}
        assert entry_map["sized.txt"]["size_bytes"] == len(content.encode("utf-8"))
        assert entry_map["subdir"]["size_bytes"] is None


# ---------------------------------------------------------------------------
# Symlink sandbox tests
# ---------------------------------------------------------------------------

class TestMinniClientSymlinks:

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="symlink creation requires elevated permissions on Windows",
    )
    def test_minni_read_file_via_symlink_to_outside_root_is_rejected(self, tmp_path):
        """read_file rejects a symlink inside allowed_roots that points outside.

        Layer 1 (path_within_allowed_roots via Path.resolve()) follows the symlink
        to its physical target. The target is outside allowed_roots, so
        MinniSandboxViolation is raised before any I/O is attempted.
        """
        outside_dir = tmp_path.parent / "outside_minni_sandbox"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "private.txt"
        outside_file.write_text("private content", encoding="utf-8")

        link_path = tmp_path / "escape_link.txt"
        try:
            os.symlink(str(outside_file), str(link_path))
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation failed on this platform/configuration")

        client = make_client(tmp_path)
        with pytest.raises(MinniSandboxViolation):
            client.read_file(str(link_path))

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="symlink creation requires elevated permissions on Windows",
    )
    def test_minni_read_file_via_symlink_to_inside_root_succeeds(self, tmp_path):
        """read_file succeeds for a symlink that lives inside AND points inside allowed_roots.

        Both the symlink's path and its resolved physical target are within
        allowed_roots, so the sandbox check passes and the file is read normally.
        """
        real_file = tmp_path / "real.txt"
        real_file.write_text("real content", encoding="utf-8")

        link_path = tmp_path / "link_to_real.txt"
        try:
            os.symlink(str(real_file), str(link_path))
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation failed on this platform/configuration")

        client = make_client(tmp_path)
        result = client.read_file(str(link_path))
        assert result["content"] == "real content"
