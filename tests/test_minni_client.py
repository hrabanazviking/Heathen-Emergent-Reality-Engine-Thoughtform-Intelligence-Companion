"""
Placeholder tests for MinniClient — sandboxed filesystem operations.

Client implementation is Wave 2 (Forge). These placeholders define the expected
behaviours including sandbox enforcement, size capping, and error types.

Ref: src/heretic/skilningr/senses/minni/client.py
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import MinniConfig
from heretic.skilningr.senses.minni.client import MinniClient
from heretic.skilningr.senses.minni.errors import (
    MinniSandboxViolation,
)


class TestMinniClientSandboxGateway:

    def test_validate_path_within_root_accepted(self, tmp_path):
        """_validate_path accepts a path within allowed_roots."""
        config = MinniConfig(allowed_roots=[str(tmp_path)])
        client = MinniClient(config)
        target = str(tmp_path / "notes.md")
        resolved = client._validate_path(target)
        assert resolved.is_absolute()

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


@pytest.mark.skip(reason="Wave 2 — MinniClient.read_file not yet implemented by Forge")
class TestMinniClientReadFile:

    def test_read_within_sandbox(self, tmp_path):
        pass

    def test_read_file_not_found_raises(self, tmp_path):
        pass

    def test_read_file_too_large_raises(self, tmp_path):
        pass


@pytest.mark.skip(reason="Wave 2 — MinniClient.write_file not yet implemented by Forge")
class TestMinniClientWriteFile:

    def test_write_creates_file(self, tmp_path):
        pass

    def test_write_outside_sandbox_raises(self, tmp_path):
        pass

    def test_write_content_too_large_raises(self, tmp_path):
        pass


@pytest.mark.skip(reason="Wave 2 — MinniClient.list_directory not yet implemented by Forge")
class TestMinniClientListDirectory:

    def test_list_directory_within_sandbox(self, tmp_path):
        pass

    def test_list_directory_recurse(self, tmp_path):
        pass
