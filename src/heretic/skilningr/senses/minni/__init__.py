"""
heretic.skilningr.senses.minni — L5.1 Minni sense subpackage.

Minni ("memory") is the filesystem sense: sandboxed local file reads,
writes, and directory listings within operator-defined allowed_roots.

Public API re-exported from this __init__ for clean external imports:

    from heretic.skilningr.senses.minni import (
        MinniSense,
        MinniClient,
        MINNI_TOOL_DEFINITIONS,
    )

Module map:
    config_model.py — MinniConfig (re-exported from skilningr.config_model)
    errors.py       — Minni error types (re-exports from heretic.skilningr.errors)
    client.py       — MinniClient (filesystem operations with sandbox validation)
    tools.py        — MINNI_TOOL_DEFINITIONS (3 OpenAI tool schemas, locked)
    sense.py        — MinniSense (orchestrator; registered in ToolDispatcher as "minni")
    INTERFACE.md    — Full Minni sense contract (sandbox invariants, tools, failure modes)

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     src/heretic/skilningr/senses/minni/INTERFACE.md
"""

from heretic.skilningr.senses.minni.client import MinniClient  # noqa: F401
from heretic.skilningr.senses.minni.sense import MinniSense  # noqa: F401
from heretic.skilningr.senses.minni.tools import MINNI_TOOL_DEFINITIONS  # noqa: F401

__all__ = [
    "MinniSense",
    "MinniClient",
    "MINNI_TOOL_DEFINITIONS",
]
