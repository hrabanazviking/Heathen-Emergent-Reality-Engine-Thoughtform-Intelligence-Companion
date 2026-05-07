"""
Placeholder tests — heretic.rodd error hierarchy.

All tests are skip-marked. Forge (Eldra Járnsdóttir) replaces the skip markers
and ``pass`` bodies with real assertions in Wave 2.

Coverage targets (Forge):
    - All error classes are importable from heretic.rodd.
    - Hierarchy: ChatterboxConnectionError < ChatterboxError < RoddError < Exception.
    - Hierarchy: PlaybackBackendUnavailableError < PlaybackError < RoddError.
    - Hierarchy: TungaConfigError < RoddError.
    - ChatterboxApiError carries status_code and detail attributes.
    - isinstance checks work transitively (catch RoddError catches all subclasses).
"""

import pytest


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_all_errors_importable_from_rodd_package() -> None:
    """All error classes are importable directly from heretic.rodd."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_chatterbox_error_hierarchy() -> None:
    """ChatterboxConnectionError, AuthError, TimeoutError, ApiError all derive from ChatterboxError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_rodd_error_is_base_for_all_chatterbox_errors() -> None:
    """All ChatterboxError subclasses are also instances of RoddError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_rodd_error_is_base_for_playback_errors() -> None:
    """PlaybackError and PlaybackBackendUnavailableError are instances of RoddError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_rodd_error_is_base_for_tunga_config_error() -> None:
    """TungaConfigError is an instance of RoddError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_chatterbox_api_error_carries_attributes() -> None:
    """ChatterboxApiError stores status_code and detail on the instance."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_catch_rodd_error_catches_all_subclasses() -> None:
    """A try/except RoddError block catches every error subclass in the hierarchy."""
    pass
