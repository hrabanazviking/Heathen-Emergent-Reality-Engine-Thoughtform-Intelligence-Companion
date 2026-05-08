"""
Entry point for `python -m heretic`.

Invokes the HERETIC CLI. This file exists so the package can be run as a module,
which is required for development-mode invocations and for Tauri sidecar spawning.

Usage:
    python -m heretic [command] [options]
    python -m heretic --help
"""

from __future__ import annotations

from heretic.cli import main

if __name__ == "__main__":
    main()
