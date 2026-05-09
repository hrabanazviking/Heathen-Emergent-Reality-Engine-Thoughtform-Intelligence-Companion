"""
Skepja sense config model — re-export shim.

SkepjaConfig is defined authoritatively in heretic.skilningr.config_model.
This shim allows callers within the skepja subpackage to import it locally.

Ref: heretic.skilningr.config_model (authoritative definition)
"""

from heretic.skilningr.config_model import SkepjaConfig  # noqa: F401

__all__ = ["SkepjaConfig"]
