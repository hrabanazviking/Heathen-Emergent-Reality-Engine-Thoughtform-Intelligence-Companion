"""
heretic.skilningr.senses.leid — L5.3 Leið sense subpackage.

Leið ("path" / "way") is the HTTP fetch sense: sandboxed outbound HTTP requests
and text extraction within an operator-defined URL allowlist. No URL is
fetchable unless the operator adds a matching pattern.

Public API re-exported from this __init__ for clean external imports:

    from heretic.skilningr.senses.leid import (
        LeidSense,
        LeidClient,
        LEID_TOOL_DEFINITIONS,
    )

Module map:
    config_model.py — LeidConfig (re-exported from skilningr.config_model)
    errors.py       — Leið error types (re-exports from heretic.skilningr.errors)
    client.py       — LeidClient (httpx GET with URL allowlist + size cap)
    tools.py        — LEID_TOOL_DEFINITIONS (2 OpenAI tool schemas, locked)
    sense.py        — LeidSense (orchestrator; registered in ToolDispatcher as "leid")
    INTERFACE.md    — Full Leið sense contract (sandbox invariants, tools, failure modes)

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     src/heretic/skilningr/senses/leid/INTERFACE.md
"""

from heretic.skilningr.senses.leid.client import LeidClient  # noqa: F401
from heretic.skilningr.senses.leid.sense import LeidSense  # noqa: F401
from heretic.skilningr.senses.leid.tools import LEID_TOOL_DEFINITIONS  # noqa: F401

__all__ = [
    "LeidSense",
    "LeidClient",
    "LEID_TOOL_DEFINITIONS",
]
