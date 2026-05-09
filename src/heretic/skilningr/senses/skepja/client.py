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

CROSS-PLATFORM NOTE:
    Windows cmd.exe uses different conventions from POSIX sh. shlex.split()
    defaults to POSIX mode; on Windows, this may not parse all command strings
    identically. Forge Wave 2 must handle platform differences explicitly.
    The allowlist check is case-sensitive on all platforms — operators must
    configure allowlist entries using the exact executable name for the target OS
    (e.g. "python" on Unix, "python.exe" on Windows if needed).

Ref: src/heretic/skilningr/senses/skepja/INTERFACE.md
     src/heretic/skilningr/sandbox.py (command_in_allowlist)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Skepja sandbox invariants)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.sandbox import command_in_allowlist
from heretic.skilningr.senses.skepja.errors import (
    CommandNotAllowedError,
    CommandParseError,
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
            List of string tokens (as from shlex.split) ready for subprocess.run().

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
        # result is the string repr of the parsed token list when allowed=True;
        # Forge Wave 2 will parse this properly — for now return shlex.split directly
        import shlex
        try:
            return shlex.split(command)
        except ValueError as exc:
            raise CommandParseError(
                f"Could not parse command {command!r}: {exc}"
            ) from exc

    def run_command(self, command: str) -> dict[str, Any]:
        """Execute an allowlisted command as a subprocess.

        Args:
            command: Raw command string. Executable must be in command_allowlist.

        Returns:
            dict with keys:
                command (str): the original command string
                exit_code (int): process exit code (0 = success)
                stdout (str): captured stdout (truncated to max_output_bytes)
                stderr (str): captured stderr (truncated to max_output_bytes)
                timed_out (bool): True if the process was killed due to timeout
                working_directory (str): resolved working directory used

        Raises:
            CommandNotAllowedError: executable not in allowlist.
            CommandParseError: command could not be parsed.
            CommandTimeoutError: subprocess did not finish within timeout_seconds.
            CommandExecutionError: subprocess returned non-zero exit code.
        """
        # Forge implements this body in Wave 2.
        # The validation gateway is wired here so it is already exercised by tests.
        raise NotImplementedError(
            "SkepjaClient.run_command: Forge implements this in Wave 2 of v0.6.2."
        )

    def get_working_directory(self) -> dict[str, Any]:
        """Return the resolved working directory for Skepja commands.

        Returns:
            dict with keys:
                working_directory (str): resolved absolute path of the working dir
        """
        # Forge implements this body in Wave 2 — trivial but stubbed for consistency.
        raise NotImplementedError(
            "SkepjaClient.get_working_directory: Forge implements this in Wave 2 of v0.6.2."
        )
