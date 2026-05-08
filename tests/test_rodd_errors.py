"""
Tests — heretic.rodd error hierarchy.

Verifies the class hierarchy, attribute contract, and isinstance chains
so callers can rely on broad RoddError catches and specific subclass catches.
"""

from __future__ import annotations

import pytest

from heretic.rodd import (
    ChatterboxApiError,
    ChatterboxAuthError,
    ChatterboxConnectionError,
    ChatterboxError,
    ChatterboxTimeoutError,
    PlaybackBackendUnavailableError,
    PlaybackError,
    RoddError,
    TungaConfigError,
)


def test_all_errors_importable_from_rodd_package() -> None:
    """All error classes are importable directly from heretic.rodd."""
    # If we got here, the imports above succeeded
    assert RoddError is not None
    assert ChatterboxError is not None
    assert ChatterboxConnectionError is not None
    assert ChatterboxAuthError is not None
    assert ChatterboxTimeoutError is not None
    assert ChatterboxApiError is not None
    assert PlaybackError is not None
    assert PlaybackBackendUnavailableError is not None
    assert TungaConfigError is not None


def test_chatterbox_error_hierarchy() -> None:
    """ChatterboxConnectionError, AuthError, TimeoutError, ApiError all derive from ChatterboxError."""
    assert issubclass(ChatterboxConnectionError, ChatterboxError)
    assert issubclass(ChatterboxAuthError, ChatterboxError)
    assert issubclass(ChatterboxTimeoutError, ChatterboxError)
    assert issubclass(ChatterboxApiError, ChatterboxError)


def test_rodd_error_is_base_for_all_chatterbox_errors() -> None:
    """All ChatterboxError subclasses are also instances of RoddError."""
    for cls in (ChatterboxConnectionError, ChatterboxAuthError, ChatterboxTimeoutError, ChatterboxApiError):
        assert issubclass(cls, RoddError), f"{cls.__name__} should be a subclass of RoddError"


def test_rodd_error_is_base_for_playback_errors() -> None:
    """PlaybackError and PlaybackBackendUnavailableError are instances of RoddError."""
    assert issubclass(PlaybackError, RoddError)
    assert issubclass(PlaybackBackendUnavailableError, PlaybackError)
    assert issubclass(PlaybackBackendUnavailableError, RoddError)


def test_rodd_error_is_base_for_tunga_config_error() -> None:
    """TungaConfigError is an instance of RoddError."""
    assert issubclass(TungaConfigError, RoddError)


def test_chatterbox_api_error_carries_attributes() -> None:
    """ChatterboxApiError stores status_code and detail on the instance."""
    err = ChatterboxApiError("test message", status_code=422, detail="Unprocessable")
    assert err.status_code == 422
    assert err.detail == "Unprocessable"
    assert str(err) == "test message"


def test_chatterbox_api_error_accepts_none_attributes() -> None:
    """ChatterboxApiError can be constructed with None attributes."""
    err = ChatterboxApiError("bare message")
    assert err.status_code is None
    assert err.detail is None


def test_catch_rodd_error_catches_all_subclasses() -> None:
    """A try/except RoddError block catches every error subclass in the hierarchy."""
    errors_to_test = [
        ChatterboxConnectionError("connection refused"),
        ChatterboxAuthError("403"),
        ChatterboxTimeoutError("timed out"),
        ChatterboxApiError("500", status_code=500),
        PlaybackError("device gone"),
        PlaybackBackendUnavailableError("no device"),
        TungaConfigError("bad config"),
    ]
    for exc in errors_to_test:
        caught = False
        try:
            raise exc
        except RoddError:
            caught = True
        assert caught, f"{type(exc).__name__} was not caught by RoddError"
