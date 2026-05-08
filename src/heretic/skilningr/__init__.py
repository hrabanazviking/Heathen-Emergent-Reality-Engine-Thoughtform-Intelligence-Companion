"""
heretic.skilningr — L5 Skilningr sense hub layer.

The sense hub is the registry and router for all agent-callable tool surfaces.
It is the body's collection of hands, eyes, and instruments.

Public API:

    from heretic.skilningr import (
        SkilningrConfig,     # root config (from config_model.py)
        SmidjaConfig,        # Smiðja/Brúarhönd config (from config_model.py)
        ToolDispatcher,      # route tool_calls to registered senses
        SmidjaSense,         # L5.5 Brúarhönd remote-control sense
        SkilningrError,      # root error class
        SenseUnavailableError,
        ToolDispatchError,
        AuthError,
    )

Layer position: L5 Skilningr — sits between L1 Bifröst and all sense implementations.
    - Receives tool_call from L1 Bifröst.
    - Routes to the matching sense via ToolDispatcher.
    - Returns tool_result to L1 Bifröst.
    - Emits sense.tool_call IPC events to L4 Vébond.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md
     src/heretic/skilningr/INTERFACE.md
"""

from heretic.skilningr.config_model import (  # noqa: F401
    SkilningrConfig,
    SmidjaConfig,
)
from heretic.skilningr.dispatcher import ToolDispatcher  # noqa: F401
from heretic.skilningr.errors import (  # noqa: F401
    AuthError,
    BrunhandAuthError,
    BrunhandSessionLockedError,
    BrunhandTimeoutError,
    BrunhandUnreachableError,
    SenseUnavailableError,
    SkilningrError,
    SmidjaError,
    ToolDispatchError,
)
from heretic.skilningr.senses.smidja import (  # noqa: F401
    BrunhandHttpClient,
    SMIDJA_TOOL_DEFINITIONS,
    SmidjaSense,
)

__all__ = [
    # Config
    "SkilningrConfig",
    "SmidjaConfig",
    # Dispatcher
    "ToolDispatcher",
    # Smiðja sense
    "SmidjaSense",
    "BrunhandHttpClient",
    "SMIDJA_TOOL_DEFINITIONS",
    # Errors
    "SkilningrError",
    "SenseUnavailableError",
    "ToolDispatchError",
    "AuthError",
    "SmidjaError",
    "BrunhandUnreachableError",
    "BrunhandTimeoutError",
    "BrunhandAuthError",
    "BrunhandSessionLockedError",
]
