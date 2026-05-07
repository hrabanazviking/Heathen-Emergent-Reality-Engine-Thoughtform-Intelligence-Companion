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


def configure_logging(
    level: str = "info",
    log_file: Optional[str] = None,
) -> None:
    """Configure the root HERETIC logger.

    Called once by Grunnr during Kynding, before any other layer initialises.
    Subsequent calls are safe (idempotent beyond the first handler attachment).

    Args:
        level: Log level string from GrunnrConfig (trace|debug|info|warn|error).
               'trace' maps to DEBUG-5; all others map to standard Python levels.
        log_file: Optional path (relative to home or CWD — never absolute) to
                  write structured JSON log records. If None, logs to stderr only.

    Raises:
        NotImplementedError: Forge will implement the full handler setup including
                             JSON formatting, rotating file handler, and level mapping.
    """
    raise NotImplementedError(
        "Forge will implement: logger.configure_logging — "
        "map level string to Python logging constant, "
        "attach StreamHandler(stderr) with a structured formatter, "
        "optionally attach a RotatingFileHandler if log_file is given "
        "(path resolved via grunnr.paths, never absolute), "
        "set propagation=False on the root heretic logger."
    )
