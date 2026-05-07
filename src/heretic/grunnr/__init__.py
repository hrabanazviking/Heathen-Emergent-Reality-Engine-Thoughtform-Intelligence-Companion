"""
L0 Grunnr — the Foundation.

Old Norse *grunnr*: the ground beneath everything, the silent base on which all else
stands. Grunnr is the first layer HERETIC initialises and the last it tears down.

Grunnr owns:
    - heretic.yaml loading and typed Config struct (config.py)
    - Structured logging initialisation (logger.py)
    - Lifecycle state machine and hooks (lifecycle.py)
    - Portable path resolution (paths.py)

No other layer reads heretic.yaml directly. All config flows through
``grunnr.config.load_config()`` and the resulting ``HereticConfig`` dataclass.

Public re-exports from this sub-package are intentionally minimal to enforce that
callers go through the typed interfaces, not raw dict access.
"""

from __future__ import annotations

from heretic.grunnr.config import HereticConfig, load_config
from heretic.grunnr.lifecycle import Lifecycle, LifecycleState
from heretic.grunnr.logger import get_logger

__all__ = [
    "HereticConfig",
    "load_config",
    "Lifecycle",
    "LifecycleState",
    "get_logger",
]
