"""
MinniClient — sandboxed filesystem operations for the Minni sense.

MinniClient executes the three Minni tool operations — read_file, write_file,
list_directory — with strict sandbox enforcement at every boundary. All paths
are validated against MinniConfig.allowed_roots before any I/O occurs.

SANDBOX INVARIANT (DO NOT WEAKEN):
    Every method calls sandbox.path_within_allowed_roots() as its first action.
    If the check fails, it raises MinniSandboxViolation immediately — no I/O
    is attempted. This call cannot be bypassed, short-circuited, or moved later
    in the call sequence without violating the security model.

Design:
    - Synchronous (no async — pathlib I/O is not async-native; the sense calls
      these methods from an async dispatch context using asyncio.to_thread in
      the Forge implementation, pending Wave 2).
    - Raises Minni-specific exceptions (MinniError subclasses) for all failure
      modes. The sense orchestrator (sense.py) catches these and translates them
      into structured tool_result error dicts — they are never re-raised to L1.
    - All methods are NotImplementedError stubs awaiting Forge implementation
      in Wave 2 of v0.6.2.

Ref: src/heretic/skilningr/senses/minni/INTERFACE.md
     src/heretic/skilningr/sandbox.py (path_within_allowed_roots)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Minni sandbox invariants)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from heretic.skilningr.config_model import MinniConfig
from heretic.skilningr.sandbox import path_within_allowed_roots
from heretic.skilningr.senses.minni.errors import (
    MinniFileNotFoundError,
    MinniFileTooLargeError,
    MinniPermissionError,
    MinniSandboxViolation,
)

logger = logging.getLogger(__name__)


class MinniClient:
    """Sandboxed local filesystem client for the Minni sense.

    All operations enforce the allowed_roots sandbox boundary via
    sandbox.path_within_allowed_roots() before any I/O is attempted.

    Usage:
        client = MinniClient(config, logger)
        content = client.read_file("~/heretic_workspace/notes.md")
        client.write_file("~/heretic_workspace/output.txt", "hello")
        entries = client.list_directory("~/heretic_workspace", recurse=False)
    """

    def __init__(
        self,
        config: MinniConfig,
        log: logging.Logger | None = None,
    ) -> None:
        """Initialise the Minni client.

        Args:
            config: MinniConfig — contains allowed_roots, size limits, and flags.
            log:    Optional logger. Defaults to module logger.
        """
        self._config = config
        self._log = log if log is not None else logging.getLogger(__name__)

    def _validate_path(self, path: str) -> Path:
        """Validate that *path* is within allowed_roots and return the resolved Path.

        This is the sandbox enforcement gateway for all three operations.
        Must be called before any filesystem I/O.

        Args:
            path: The candidate path string from the agent tool call.

        Returns:
            The resolved absolute Path object (guaranteed within allowed_roots).

        Raises:
            MinniSandboxViolation: if path is outside all allowed_roots.
        """
        allowed, result = path_within_allowed_roots(path, self._config.allowed_roots)
        if not allowed:
            self._log.warning("Minni sandbox violation: %s", result)
            raise MinniSandboxViolation(
                f"Filesystem access denied: {result}"
            )
        # result is the resolved path string when allowed=True
        return Path(result)  # type: ignore[arg-type]

    def read_file(self, path: str) -> dict[str, Any]:
        """Read text content from a sandboxed file.

        Args:
            path: Path to the file. Must resolve to within allowed_roots.

        Returns:
            dict with keys:
                path (str): resolved absolute path
                content (str): UTF-8 file content
                size_bytes (int): file size in bytes
                encoding (str): always "utf-8" in v0.6.2

        Raises:
            MinniSandboxViolation: path outside allowed_roots.
            MinniFileNotFoundError: file does not exist.
            MinniFileTooLargeError: file exceeds max_read_bytes.
            MinniPermissionError: OS denied read access.
        """
        # Forge implements this body in Wave 2. The sandbox gateway is scaffolded
        # here so the validation path is already wired and testable.
        raise NotImplementedError(
            "MinniClient.read_file: Forge implements this in Wave 2 of v0.6.2."
        )

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write text content to a sandboxed file.

        Creates the file (and any missing parent directories within allowed_roots)
        if it does not exist. Overwrites existing content entirely.

        Args:
            path:    Path to write. Must resolve to within allowed_roots.
            content: UTF-8 text content to write.

        Returns:
            dict with keys:
                path (str): resolved absolute path written
                bytes_written (int): actual bytes written
                created (bool): True if file was newly created, False if overwritten

        Raises:
            MinniSandboxViolation: path outside allowed_roots.
            MinniFileTooLargeError: content exceeds max_write_bytes.
            MinniPermissionError: OS denied write access.
        """
        raise NotImplementedError(
            "MinniClient.write_file: Forge implements this in Wave 2 of v0.6.2."
        )

    def list_directory(self, path: str, recurse: bool = False) -> dict[str, Any]:
        """List the contents of a sandboxed directory.

        Args:
            path:    Path to the directory. Must resolve to within allowed_roots.
            recurse: If True, list the full directory tree recursively.
                     If False (default), list only immediate children.

        Returns:
            dict with keys:
                path (str): resolved absolute directory path
                entries (list[dict]): list of entry dicts, each with:
                    name (str): filename or directory name
                    type (str): "file" or "directory"
                    size_bytes (int | None): file size in bytes; None for directories
                    path (str): absolute path to this entry
                recurse (bool): echoes the recurse argument
                total_entries (int): number of entries returned

        Raises:
            MinniSandboxViolation: path outside allowed_roots.
            MinniFileNotFoundError: directory does not exist.
            MinniPermissionError: OS denied directory listing.
        """
        raise NotImplementedError(
            "MinniClient.list_directory: Forge implements this in Wave 2 of v0.6.2."
        )
