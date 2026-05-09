"""
SkepjaClient — sandboxed subprocess execution for the Skepja sense.

SkepjaClient executes shell commands through a strict two-gate sandbox:
    1. sandbox.command_in_allowlist() — rejects any executable not on the
       operator allowlist before subprocess.run() is ever called.
    2. subprocess.run(shell=False) — prevents shell injection by treating
       the command as a token list, not a shell expression.

SANDBOX INVARIANT (DO NOT WEAKEN):
    command_in_allowlist() is called BEFORE subprocess.run(). This gate cannot
    be bypassed, reordered, or short-circuited.

    shell=False is INVARIANT. Any call to subprocess.run() in this module
    MUST pass shell=False. Shell metacharacters (|, >, &&, ;) have no special
    meaning — they become literal arguments to the executable.

CROSS-PLATFORM NOTE (Architect's flag):
    shlex.split() in POSIX mode parses differently from Windows cmd.exe conventions.
    We use posix=(os.name != "nt") so that on Windows, shlex uses non-POSIX mode,
    which preserves Windows-style quoting behaviour more accurately.
    The allowlist check is case-sensitive on all platforms — operators must configure
    allowlist entries using the exact executable name for the target OS
    (e.g. "python" on Unix, "python.exe" on Windows if the extension is needed).

Environment:
    When inherit_env=False (default), the subprocess receives only PATH from
    the host environment — no API keys, tokens, or other secrets leak.
    When inherit_env=True, the full os.environ copy is passed; this is the
    operator's explicit opt-in.

Output:
    stdout and stderr are each individually capped at max_output_bytes.
    The "truncated" key in the result dict is True if either stream was capped.

Ref: src/heretic/skilningr/senses/skepja/INTERFACE.md
     src/heretic/skilningr/sandbox.py (command_in_allowlist)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Skepja sandbox invariants)
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.sandbox import command_in_allowlist
from heretic.skilningr.senses.skepja.errors import (
    CommandExecutionError,
    CommandNotAllowedError,
    CommandParseError,
    CommandTimeoutError,
)

logger = logging.getLogger(__name__)


class SkepjaClient:
    """Sandboxed subprocess client for the Skepja sense.

    All run_command calls enforce the command_allowlist via
    sandbox.command_in_allowlist() before any subprocess is spawned.
    shell=False is invariant.

    Usage:
        client = SkepjaClient(config)
        result = client.run_command("git status")
        cwd    = client.get_working_directory()
    """

    def __init__(
        self,
        config: SkepjaConfig,
        log: logging.Logger | None = None,
    ) -> None:
        """Initialise the Skepja client.

        Args:
            config: SkepjaConfig — contains allowlist, working_directory, timeouts.
            log:    Optional logger. Defaults to module logger.
        """
        self._config = config
        self._log = log if log is not None else logging.getLogger(__name__)

    def _validate_command(self, command: str) -> list[str]:
        """Validate that *command* is permitted and return the parsed token list.

        This is the allowlist enforcement gateway. Must be called before any
        subprocess invocation.

        Args:
            command: Raw command string from the agent tool call.

        Returns:
            List of string tokens ready for subprocess.run().

        Raises:
            CommandNotAllowedError: executable not in allowlist.
            CommandParseError: command could not be parsed by shlex.
        """
        allowed, result = command_in_allowlist(command, self._config.command_allowlist)
        if not allowed:
            self._log.warning("Skepja allowlist rejection: %s", result)
            raise CommandNotAllowedError(
                f"Command not permitted: {result}"
            )
        # Use posix=False on Windows for correct Windows quoting semantics.
        # This is the Architect's cross-platform flag — do not remove.
        use_posix = os.name != "nt"
        try:
            return shlex.split(command, posix=use_posix)
        except ValueError as exc:
            raise CommandParseError(
                f"Could not parse command {command!r}: {exc}"
            ) from exc

    def _resolve_working_directory(self) -> str:
        """Resolve and validate the configured working directory.

        Returns:
            Absolute path string to the working directory.

        Raises:
            CommandExecutionError: working_directory does not exist.
        """
        resolved = str(Path(self._config.working_directory).expanduser().resolve())
        if not Path(resolved).exists():
            raise CommandExecutionError(
                f"Skepja working_directory {resolved!r} does not exist. "
                f"Create the directory or update SkepjaConfig.working_directory."
            )
        if not Path(resolved).is_dir():
            raise CommandExecutionError(
                f"Skepja working_directory {resolved!r} is not a directory."
            )
        return resolved

    def _build_env(self) -> dict[str, str] | None:
        """Build the subprocess environment dict.

        Returns:
            Full os.environ copy when inherit_env=True.
            Minimal dict with only PATH when inherit_env=False (default).
        """
        if self._config.inherit_env:
            return dict(os.environ)
        # Minimal environment: only PATH so basic executables can be found.
        # No API keys, tokens, or other secrets from the host environment.
        return {"PATH": os.environ.get("PATH", "")}

    def run_command(self, command: str) -> dict[str, Any]:
        """Execute an allowlisted command as a subprocess.

        Args:
            command: Raw command string. Executable must be in command_allowlist.

        Returns:
            dict with keys:
                command (str): the original command string
                args (list[str]): parsed token list passed to subprocess
                exit_code (int): process exit code (0 = success)
                stdout (str): captured stdout (truncated to max_output_bytes)
                stderr (str): captured stderr (truncated to max_output_bytes)
                timed_out (bool): True if the process was killed due to timeout
                truncated (bool): True if stdout or stderr was capped
                working_directory (str): resolved working directory used

        Raises:
            CommandNotAllowedError: executable not in allowlist.
            CommandParseError: command could not be parsed.
            CommandTimeoutError: subprocess did not finish within timeout_seconds.
            CommandExecutionError: working directory invalid or subprocess failed to start.
        """
        # Gate 1 — allowlist check
        args = self._validate_command(command)

        # Resolve working directory — may raise CommandExecutionError
        working_directory = self._resolve_working_directory()

        # Build environment
        env = self._build_env()

        self._log.debug(
            "Skepja run_command: %r (cwd=%s, timeout=%ds, inherit_env=%s)",
            command, working_directory, self._config.timeout_seconds,
            self._config.inherit_env,
        )

        # Gate 2 — subprocess execution with shell=False INVARIANT
        timed_out = False
        try:
            proc = subprocess.run(
                args,
                cwd=working_directory,
                capture_output=True,
                timeout=self._config.timeout_seconds,
                shell=False,  # INVARIANT — never change this
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            # Capture whatever partial output was available
            stdout_raw = (exc.stdout or b"")
            stderr_raw = (exc.stderr or b"")
            stdout_str = stdout_raw.decode("utf-8", errors="replace")
            stderr_str = stderr_raw.decode("utf-8", errors="replace")
            self._log.warning(
                "Skepja command %r timed out after %ds", command,
                self._config.timeout_seconds,
            )
            raise CommandTimeoutError(
                f"Command {command!r} timed out after {self._config.timeout_seconds}s. "
                f"Partial stdout: {stdout_str[:200]!r}"
            ) from exc
        except FileNotFoundError as exc:
            raise CommandExecutionError(
                f"Executable not found on PATH: {args[0]!r}. "
                f"The allowlist permitted {args[0]!r} but it is not installed or "
                f"not on PATH in the subprocess environment. "
                f"Original error: {exc}"
            ) from exc
        except (PermissionError, OSError) as exc:
            raise CommandExecutionError(
                f"OS error launching command {command!r}: {exc}"
            ) from exc

        # Capture and truncate output
        max_bytes = self._config.max_output_bytes
        stdout_raw = proc.stdout or b""
        stderr_raw = proc.stderr or b""

        stdout_truncated = len(stdout_raw) > max_bytes
        stderr_truncated = len(stderr_raw) > max_bytes

        stdout_str = stdout_raw[:max_bytes].decode("utf-8", errors="replace")
        stderr_str = stderr_raw[:max_bytes].decode("utf-8", errors="replace")
        truncated = stdout_truncated or stderr_truncated

        self._log.debug(
            "Skepja run_command complete: exit_code=%d, stdout=%d bytes, stderr=%d bytes",
            proc.returncode, len(stdout_raw), len(stderr_raw),
        )

        return {
            "command": command,
            "args": args,
            "exit_code": proc.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "timed_out": timed_out,
            "truncated": truncated,
            "working_directory": working_directory,
        }

    def get_working_directory(self) -> dict[str, Any]:
        """Return the resolved working directory for Skepja commands.

        Returns:
            dict with keys:
                working_directory (str): resolved absolute path of the working dir
                exists (bool): whether the directory currently exists on disk
        """
        resolved = str(Path(self._config.working_directory).expanduser().resolve())
        exists = Path(resolved).exists() and Path(resolved).is_dir()
        return {
            "working_directory": resolved,
            "exists": exists,
        }
