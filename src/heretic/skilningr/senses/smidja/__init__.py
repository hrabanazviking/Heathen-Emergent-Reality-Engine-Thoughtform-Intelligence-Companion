"""
heretic.skilningr.senses.smidja — L5.5 Smiðja sense subpackage.

Public API re-exported from this __init__ for clean external imports:

    from heretic.skilningr.senses.smidja import (
        SmidjaSense,
        BrunhandHttpClient,
        SMIDJA_TOOL_DEFINITIONS,
    )

Module map:
    client.py   — BrunhandHttpClient (httpx-based async HTTP client for the daemon)
    tools.py    — SMIDJA_TOOL_DEFINITIONS (6 OpenAI tool schemas, locked)
    sense.py    — SmidjaSense (orchestrator; registered in ToolDispatcher as "smidja")
    errors.py   — Smiðja error types (re-exports from heretic.skilningr.errors)
    INTERFACE.md — Full Smiðja sense contract

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     src/heretic/skilningr/senses/smidja/INTERFACE.md
"""

from heretic.skilningr.senses.smidja.client import BrunhandHttpClient  # noqa: F401
from heretic.skilningr.senses.smidja.sense import SmidjaSense  # noqa: F401
from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS  # noqa: F401

__all__ = [
    "SmidjaSense",
    "BrunhandHttpClient",
    "SMIDJA_TOOL_DEFINITIONS",
]
