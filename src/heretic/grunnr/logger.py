"""
Grunnr logger — structured logging contract for all HERETIC layers.

Every layer obtains its logger via ``get_logger(name)``. No layer uses print()
(per RULES.AI.md). No layer configures logging directly — all logging setup is
owned by Grunnr and happens once, at Kynding, before any other layer initialises.

Log channels of note (referenced in LAYER_INTERFACES.md):
    heretic.lifecycle  — lifecycle state transitions (emitted by Lifecycle)
    heretic.bifrost    — agent connection events
    heretic.grunnr     — config loading, path resolution, subprocess supervision

Structured logging format:
    Each log record carries at minimum: timestamp (ISO 8601), level, logger name,
    message. In structured mode (log_format: json in config) a JSON record is emitted;
    in human mode a readable line is emitted. Forge will implement both formatters.

    The contract: ``get_logger(name)`` always returns a standard library
    ``logging.Logger`` instance. Callers use the standard Python logging API
    (logger.info, logger.warning, logger.error, logger.debug). This keeps the
    interface stable even if the backend formatter changes.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Return a Logger for the given name.

    This is the only way layers should obtain loggers. The root HERETIC logger
    is configured by ``configure_logging()`` at startup; child loggers inherit
    its handlers and level unless overridden.

    Args:
        name: Logger name. Use the module's __name__ convention:
              e.g. ``get_logger(__name__)`` inside grunnr.config gives
              ``logging.getLogger("heretic.grunnr.config")``.

    Returns:
        A standard library Logger. Never None, never raises.
    """
    # Namespace all HERETIC loggers under "heretic." so the root handler applies.
    if not name.startswith("heretic.") and name != "heretic":
        name = f"heretic.{name}"
    return logging.getLogger(name)


# Python's logging module has no TRACE level. We define it as DEBUG-5 so that
# callers who set log_level: trace get the most verbose output without inventing
# a new level the stdlib does not know about.
_TRACE_LEVEL = logging.DEBUG - 5
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _level_from_string(level_str: str) -> int:
    """Map a HERETIC log level string to a Python logging constant.

    Supported: trace (→ DEBUG-5), debug, info, warn, warning, error, critical.
    Unknown strings default to INFO with no exception — fault tolerance over crash.
    """
    mapping = {
        "trace": _TRACE_LEVEL,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    return mapping.get(level_str.lower(), logging.INFO)


def configure_logging(
    level: str = "info",
    log_file: Optional[str] = None,
) -> None:
    """Configure the root HERETIC logger.

    Called once by Grunnr during Kynding, before any other layer initialises.
    Idempotent — safe to call multiple times; subsequent calls are no-ops after
    the first successful configuration (handlers are not duplicated).

    Args:
        level: Log level string from GrunnrConfig (trace|debug|info|warn|error).
               'trace' maps to DEBUG-5 — Python has no native TRACE level.
        log_file: Optional path (relative to CWD or home — never absolute) where
                  a RotatingFileHandler will also write. If None, stderr only.
    """
    root_logger = logging.getLogger("heretic")

    # Idempotent guard — do not add duplicate handlers on repeated calls
    if root_logger.handlers:
        return

    numeric_level = _level_from_string(level)
    root_logger.setLevel(numeric_level)
    # Prevent log records from propagating to the stdlib root logger,
    # which might have its own handlers that would duplicate output.
    root_logger.propagate = False

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Stream handler — always present; writes to stderr so stdout stays clean
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Rotating file handler — only when log_file is configured
    if log_file:
        try:
            log_path = Path(log_file).expanduser()
            # Resolve relative paths against home to avoid CWD-dependency
            if not log_path.is_absolute():
                log_path = Path.home() / log_path
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB per file
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError as exc:
            # File logging failure must not crash the process — degrade gracefully
            root_logger.warning(
                "Could not open log file %r: %s. Continuing with stderr only.",
                log_file, exc
            )
