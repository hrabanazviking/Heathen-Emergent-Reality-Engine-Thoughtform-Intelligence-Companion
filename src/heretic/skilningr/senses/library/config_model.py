"""
Library sense config model — LibraryConfig.

LibraryConfig is defined authoritatively in heretic.skilningr.config_model.
This shim allows callers within the library subpackage to import it locally:

    from heretic.skilningr.senses.library.config_model import LibraryConfig

without importing the full config_model module. This mirrors the pattern
used in the minni and skepja subpackages.

Ref: heretic.skilningr.config_model (authoritative definition)
"""

from heretic.skilningr.config_model import LibraryConfig  # noqa: F401

__all__ = ["LibraryConfig"]
