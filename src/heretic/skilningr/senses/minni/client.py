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
    - Synchronous (no async — pathlib I/O is not async-native; callers that
      need async wrapping should use asyncio.to_thread).
    - Raises Minni-specific exceptions (MinniError subclasses) for all failure
      modes. The sense orchestrator (sense.py) catches these and translates them
      into structured tool_result error dicts — they are never re-raised to L1.
    - write_file uses atomic rename (write to .tmp, then os.replace) so partial
      writes cannot leave a corrupt file.

Symlink handling:
    Validation uses os.path.abspath(os.path.expanduser(path)) — the lexical
    canonical form WITHOUT following symlinks. This means a symlink inside
    allowed_roots pointing outside is still allowed by the path check (the
    symlink's own path is inside the sandbox). The MinniConfig.follow_symlinks
    flag is used during I/O operations (open/stat) to decide whether to
    dereference the symlink.

    This matches the §4.12 Step 3(c) Cartographer invariant: validate the
    symlink's own path, not its target. DO NOT simplify this comment — it is
    load-bearing documentation of a deliberate security decision.

Ref: src/heretic/skilningr/senses/minni/INTERFACE.md
     src/heretic/skilningr/sandbox.py (path_within_allowed_roots)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Minni sandbox invariants)
"""

from __future__ import annotations

import logging
import os
import stat as _stat_module
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
                content (str): UTF-8 file content (errors="replace")
                size_bytes (int): file size in bytes
                encoding (str): always "utf-8" in v0.6.2

        Raises:
            MinniSandboxViolation: path outside allowed_roots.
            MinniFileNotFoundError: file does not exist.
            MinniFileTooLargeError: file exceeds max_read_bytes.
            MinniPermissionError: OS denied read access.
        """
        resolved = self._validate_path(path)
        resolved_str = str(resolved)

        # Check existence
        if not resolved.exists():
            raise MinniFileNotFoundError(
                f"File not found: {resolved_str!r}"
            )
        if not resolved.is_file():
            raise MinniFileNotFoundError(
                f"Path is not a file: {resolved_str!r} (is a directory or special file)"
            )

        # Size check before reading — prevents reading multi-GB files into memory
        try:
            size_bytes = resolved.stat(follow_symlinks=self._config.follow_symlinks).st_size
        except PermissionError as exc:
            raise MinniPermissionError(
                f"OS denied stat on {resolved_str!r}: {exc}"
            ) from exc
        except OSError as exc:
            raise MinniPermissionError(
                f"Could not stat {resolved_str!r}: {exc}"
            ) from exc

        if size_bytes > self._config.max_read_bytes:
            raise MinniFileTooLargeError(
                f"File {resolved_str!r} is {size_bytes} bytes, which exceeds "
                f"max_read_bytes={self._config.max_read_bytes}. "
                f"Increase MinniConfig.max_read_bytes to read this file."
            )

        # Read content
        try:
            raw_bytes = resolved.read_bytes()
        except PermissionError as exc:
            raise MinniPermissionError(
                f"OS denied read access to {resolved_str!r}: {exc}"
            ) from exc
        except OSError as exc:
            raise MinniPermissionError(
                f"Could not read {resolved_str!r}: {exc}"
            ) from exc

        # Decode with errors="replace" — never crash on non-UTF-8 bytes
        content = raw_bytes.decode("utf-8", errors="replace")
        self._log.debug("Minni read_file: %s (%d bytes)", resolved_str, size_bytes)

        return {
            "path": resolved_str,
            "content": content,
            "size_bytes": size_bytes,
            "encoding": "utf-8",
        }

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write text content to a sandboxed file.

        Creates the file (and any missing parent directories within allowed_roots)
        if it does not exist. Overwrites existing content entirely via atomic rename.

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
        resolved = self._validate_path(path)
        resolved_str = str(resolved)

        # Encode first — check size before touching filesystem
        encoded = content.encode("utf-8")
        if len(encoded) > self._config.max_write_bytes:
            raise MinniFileTooLargeError(
                f"Content is {len(encoded)} bytes, which exceeds "
                f"max_write_bytes={self._config.max_write_bytes}. "
                f"Reduce content size or increase MinniConfig.max_write_bytes."
            )

        file_existed = resolved.exists()

        # Create parent directories if missing — validate each parent is within sandbox
        parent = resolved.parent
        parent_str = str(parent)
        parent_ok, _ = path_within_allowed_roots(parent_str, self._config.allowed_roots)
        if not parent_ok:
            raise MinniSandboxViolation(
                f"Parent directory {parent_str!r} is outside allowed_roots. "
                f"Cannot create directories outside the sandbox."
            )

        try:
            parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise MinniPermissionError(
                f"OS denied directory creation for {parent_str!r}: {exc}"
            ) from exc
        except OSError as exc:
            raise MinniPermissionError(
                f"Could not create parent directories for {resolved_str!r}: {exc}"
            ) from exc

        # Atomic write: write to temp file then rename.
        # os.replace is atomic on POSIX and best-effort atomic on Windows (same volume).
        tmp_path_str = resolved_str + ".heretic_tmp"
        try:
            tmp_path = Path(tmp_path_str)
            tmp_path.write_bytes(encoded)
            os.replace(tmp_path_str, resolved_str)
        except PermissionError as exc:
            # Clean up tmp if it was created
            try:
                Path(tmp_path_str).unlink(missing_ok=True)
            except OSError:
                pass
            raise MinniPermissionError(
                f"OS denied write access to {resolved_str!r}: {exc}"
            ) from exc
        except OSError as exc:
            try:
                Path(tmp_path_str).unlink(missing_ok=True)
            except OSError:
                pass
            raise MinniPermissionError(
                f"Could not write to {resolved_str!r}: {exc}"
            ) from exc

        self._log.debug(
            "Minni write_file: %s (%d bytes, created=%s)",
            resolved_str, len(encoded), not file_existed,
        )

        return {
            "path": resolved_str,
            "bytes_written": len(encoded),
            "created": not file_existed,
        }

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
                    type (str): "file", "directory", or "other"
                    size_bytes (int | None): file size in bytes; None for non-files
                    path (str): absolute path to this entry
                recurse (bool): echoes the recurse argument
                total_entries (int): number of entries returned

        Raises:
            MinniSandboxViolation: path outside allowed_roots.
            MinniFileNotFoundError: directory does not exist.
            MinniPermissionError: OS denied directory listing.
        """
        resolved = self._validate_path(path)
        resolved_str = str(resolved)

        if not resolved.exists():
            raise MinniFileNotFoundError(
                f"Directory not found: {resolved_str!r}"
            )
        if not resolved.is_dir():
            raise MinniFileNotFoundError(
                f"Path is not a directory: {resolved_str!r}"
            )

        entries: list[dict[str, Any]] = []

        try:
            if recurse:
                # rglob("*") yields all descendants depth-first
                iter_entries = resolved.rglob("*")
            else:
                iter_entries = resolved.iterdir()

            for entry in iter_entries:
                try:
                    # follow_symlinks kwarg for stat() requires Python 3.10+ on POSIX
                    # but is not universally supported for Path.is_file()/is_dir().
                    # Use os.stat with follow_symlinks for cross-platform correctness,
                    # then classify via stat mode bits — no Python 3.12 dependency.
                    raw_stat = os.stat(
                        str(entry),
                        follow_symlinks=self._config.follow_symlinks,
                    )
                    mode = raw_stat.st_mode
                    if _stat_module.S_ISREG(mode):
                        entry_type = "file"
                        size_bytes: int | None = raw_stat.st_size
                    elif _stat_module.S_ISDIR(mode):
                        entry_type = "directory"
                        size_bytes = None
                    else:
                        entry_type = "other"
                        size_bytes = None

                    entries.append({
                        "name": entry.name,
                        "type": entry_type,
                        "size_bytes": size_bytes,
                        "path": str(entry),
                    })
                except (PermissionError, OSError):
                    # Non-fatal per-entry error — skip inaccessible entries, log once
                    self._log.debug("Minni list_directory: skipping inaccessible entry %s", entry)
                    continue

        except PermissionError as exc:
            raise MinniPermissionError(
                f"OS denied listing of {resolved_str!r}: {exc}"
            ) from exc
        except OSError as exc:
            raise MinniPermissionError(
                f"Could not list {resolved_str!r}: {exc}"
            ) from exc

        self._log.debug(
            "Minni list_directory: %s (%d entries, recurse=%s)",
            resolved_str, len(entries), recurse,
        )

        return {
            "path": resolved_str,
            "entries": entries,
            "recurse": recurse,
            "total_entries": len(entries),
        }
