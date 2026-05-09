"""
heretic.skilningr.senses.skepja — L5.2 Skepja sense subpackage.

Skepja ("shaping") is the terminal sense: sandboxed shell command execution
within an operator-defined allowlist. No command runs unless explicitly
permitted. An empty allowlist permits nothing.

Public API re-exported from this __init__ for clean external imports:

    from heretic.skilningr.senses.skepja import (
        SkepjaSense,
        SkepjaClient,
        SKEPJA_TOOL_DEFINITIONS,
    )

Module map:
    config_model.py — SkepjaConfig (re-exported from skilningr.config_model)
    errors.py       — Skepja error types (re-exports from heretic.skilningr.errors)
    client.py       — SkepjaClient (subprocess wrapper with allowlist enforcement)
    tools.py        — SKEPJA_TOOL_DEFINITIONS (2 OpenAI tool schemas, locked)
    sense.py        — SkepjaSense (orchestrator; registered in ToolDispatcher as "skepja")
    INTERFACE.md    — Full Skepja sense contract (sandbox invariants, tools, failure modes)

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     src/heretic/skilningr/senses/skepja/INTERFACE.md
"""

from heretic.skilningr.senses.skepja.client import SkepjaClient  # noqa: F401
from heretic.skilningr.senses.skepja.sense import SkepjaSense  # noqa: F401
from heretic.skilningr.senses.skepja.tools import SKEPJA_TOOL_DEFINITIONS  # noqa: F401

__all__ = [
    "SkepjaSense",
    "SkepjaClient",
    "SKEPJA_TOOL_DEFINITIONS",
]
