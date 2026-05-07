"""
Placeholder tests — heretic.rodd.playback (AudioPlayback backends).

All tests are skip-marked. Forge (Eldra Járnsdóttir) replaces the skip markers
and ``pass`` bodies with real assertions in Wave 2.

All calls to sounddevice and OS subprocess must be mocked — no real speakers
required in CI. Use pytest-mock (mocker fixture) to patch sounddevice.play and
subprocess.run.

Coverage targets (Forge):

    AudioPlayback.best_available():
        - Returns SoundDeviceBackend when sounddevice is importable.
        - Returns PlatformFallbackBackend when sounddevice raises ImportError.

    SoundDeviceBackend:
        - available() returns True when sounddevice and device are present (mocked).
        - available() returns False when sounddevice raises ImportError.
        - available() returns False when device query raises (no such device).
        - available() never raises — returns False on any exception.
        - play() calls sounddevice.play with correct samplerate and data (mocked).
        - play() raises PlaybackError on sounddevice.PortAudioError.
        - close() calls sounddevice.stop() (mocked).

    PlatformFallbackBackend:
        - available() returns True on Windows when winsound is importable (mocked).
        - available() returns True on Linux when aplay is on PATH (mocked shutil.which).
        - available() returns True on macOS when afplay is on PATH (mocked shutil.which).
        - available() returns False when no native method exists.
        - play() writes a temp .wav file and invokes the correct native command (mocked).
        - play() removes the temp file even when the native command fails.
        - play() raises PlaybackError on subprocess.CalledProcessError.
        - close() does not raise.
"""

import pytest


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_best_available_returns_sounddevice_backend_when_importable(mocker) -> None:
    """best_available() returns SoundDeviceBackend when sounddevice can be imported."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_best_available_returns_fallback_when_sounddevice_missing(mocker) -> None:
    """best_available() returns PlatformFallbackBackend when sounddevice is absent."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_available_true_when_device_found(mocker) -> None:
    """SoundDeviceBackend.available() returns True when sounddevice and device are present."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_available_false_when_import_fails(mocker) -> None:
    """SoundDeviceBackend.available() returns False when sounddevice raises ImportError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_available_false_when_device_missing(mocker) -> None:
    """SoundDeviceBackend.available() returns False when device query raises."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_available_never_raises(mocker) -> None:
    """SoundDeviceBackend.available() returns False (not raises) on any exception."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_play_calls_sounddevice_play(mocker) -> None:
    """SoundDeviceBackend.play() calls sounddevice.play with correct samplerate."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_play_raises_playback_error_on_portaudio_error(mocker) -> None:
    """SoundDeviceBackend.play() raises PlaybackError on sounddevice.PortAudioError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_sounddevice_close_calls_stop(mocker) -> None:
    """SoundDeviceBackend.close() calls sounddevice.stop()."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_available_on_linux(mocker) -> None:
    """PlatformFallbackBackend.available() returns True on Linux when aplay is on PATH."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_available_on_macos(mocker) -> None:
    """PlatformFallbackBackend.available() returns True on macOS when afplay is on PATH."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_available_on_windows(mocker) -> None:
    """PlatformFallbackBackend.available() returns True on Windows when winsound importable."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_play_creates_and_removes_temp_file(mocker) -> None:
    """PlatformFallbackBackend.play() writes a temp file and deletes it after playback."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_play_removes_temp_file_on_failure(mocker) -> None:
    """PlatformFallbackBackend.play() removes the temp file even when the command fails."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_play_raises_playback_error_on_subprocess_failure(mocker) -> None:
    """PlatformFallbackBackend.play() raises PlaybackError on CalledProcessError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
def test_fallback_close_does_not_raise() -> None:
    """PlatformFallbackBackend.close() completes without raising."""
    pass
