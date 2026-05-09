"""
Minni sense config model — re-export shim.

MinniConfig is defined authoritatively in heretic.skilningr.config_model.
This shim allows callers within the minni subpackage to import it locally:

    from heretic.skilningr.senses.minni.config_model import MinniConfig

without importing the full config_model module. This mirrors the pattern
used in the smidja subpackage.

Ref: heretic.skilningr.config_model (authoritative definition)
"""

from heretic.skilningr.config_model import MinniConfig  # noqa: F401

__all__ = ["MinniConfig"]
