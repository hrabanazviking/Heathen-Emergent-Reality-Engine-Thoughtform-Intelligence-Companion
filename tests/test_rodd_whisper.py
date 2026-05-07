"""
Placeholder tests — WhisperEngine backends (L2 Rödd Hlust substrate).

All tests are skip-marked. Forge implements these in v0.3 Wave 2.

Coverage targets (Forge):
    - NullWhisperBackend.available() is always True
    - NullWhisperBackend.load_model() sets is_loaded = True
    - NullWhisperBackend.transcribe() returns empty string
    - PyWhisperCppBackend.available() returns True when pywhispercpp importable
    - PyWhisperCppBackend.available() returns False on ImportError (mocked)
    - PyWhisperCppBackend.is_loaded is False before load_model()
    - PyWhisperCppBackend.is_loaded is True after load_model() (mocked model)
    - PyWhisperCppBackend.transcribe() converts int16 bytes to float32 and calls model
    - PyWhisperCppBackend.load_model() raises WhisperModelLoadError on missing file
    - CliSubprocessBackend.available() returns True when whisper-cli on PATH (mocked)
    - CliSubprocessBackend.available() returns False when whisper-cli absent
    - CliSubprocessBackend.load_model() raises WhisperModelLoadError on missing binary
    - CliSubprocessBackend.transcribe() serialises WAV, subprocesses, parses output
    - WhisperEngine.best_available() preference: pywhispercpp > cli > null
    - Lazy-load invariant: is_loaded is False immediately after construction
"""

from __future__ import annotations

import pytest

from heretic.rodd.config_model import RoddSttConfig
from heretic.rodd.errors import WhisperModelLoadError
from heretic.rodd.whisper_engine import (
    CliSubprocessBackend,
    NullWhisperBackend,
    PyWhisperCppBackend,
    WhisperEngine,
)


# ---------------------------------------------------------------------------
# NullWhisperBackend
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_whisper_always_available() -> None:
    """NullWhisperBackend.available() is always True."""
    assert NullWhisperBackend.available() is True


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_null_whisper_load_model_sets_is_loaded() -> None:
    """NullWhisperBackend.load_model() sets is_loaded to True."""
    import logging
    config = RoddSttConfig()
    engine = NullWhisperBackend(config=config, logger=logging.getLogger("test.null_whisper"))
    assert engine.is_loaded is False
    await engine.load_model()
    assert engine.is_loaded is True


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_null_whisper_transcribe_returns_empty() -> None:
    """NullWhisperBackend.transcribe() returns an empty string."""
    import logging
    config = RoddSttConfig()
    engine = NullWhisperBackend(config=config, logger=logging.getLogger("test.null_whisper"))
    result = await engine.transcribe(b"\x00" * 960, sample_rate=16_000)
    assert result == ""


# ---------------------------------------------------------------------------
# Lazy-load invariant (applies to all real backends)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_pywhispercpp_is_loaded_false_at_construction() -> None:
    """PyWhisperCppBackend.is_loaded is False immediately after __init__."""
    import logging
    config = RoddSttConfig()
    engine = PyWhisperCppBackend(config=config, logger=logging.getLogger("test.pywc"))
    assert engine.is_loaded is False


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_cli_subprocess_is_loaded_false_at_construction() -> None:
    """CliSubprocessBackend.is_loaded is False immediately after __init__."""
    import logging
    config = RoddSttConfig()
    engine = CliSubprocessBackend(config=config, logger=logging.getLogger("test.cli_whisper"))
    assert engine.is_loaded is False


# ---------------------------------------------------------------------------
# PyWhisperCppBackend — probed by Forge with mocked pywhispercpp
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_pywhispercpp_available_when_importable(monkeypatch) -> None:
    """PyWhisperCppBackend.available() returns True when pywhispercpp is importable."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_pywhispercpp_available_false_on_import_error(monkeypatch) -> None:
    """PyWhisperCppBackend.available() returns False on ImportError."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_pywhispercpp_load_model_sets_is_loaded(monkeypatch, tmp_path) -> None:
    """PyWhisperCppBackend.load_model() sets is_loaded after successful load (mocked)."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_pywhispercpp_load_model_raises_on_missing_file(tmp_path) -> None:
    """PyWhisperCppBackend.load_model() raises WhisperModelLoadError for missing model."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_pywhispercpp_transcribe_converts_int16_to_float32(monkeypatch) -> None:
    """PyWhisperCppBackend.transcribe() converts int16 bytes to float32 before calling model."""
    pass


# ---------------------------------------------------------------------------
# CliSubprocessBackend — probed by Forge with mocked shutil.which + subprocess
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_cli_available_when_binary_on_path(monkeypatch) -> None:
    """CliSubprocessBackend.available() returns True when whisper-cli found on PATH."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_cli_available_false_when_binary_absent(monkeypatch) -> None:
    """CliSubprocessBackend.available() returns False when whisper-cli not on PATH."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_cli_transcribe_writes_wav_and_parses_output(monkeypatch, tmp_path) -> None:
    """CliSubprocessBackend.transcribe() writes a temp WAV and parses subprocess stdout."""
    pass


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_whisper_best_available_prefers_pywhispercpp(monkeypatch) -> None:
    """best_available() returns PyWhisperCppBackend when pywhispercpp is present."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_whisper_best_available_falls_back_to_cli(monkeypatch) -> None:
    """best_available() returns CliSubprocessBackend when pywhispercpp absent."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_whisper_best_available_falls_back_to_null(monkeypatch) -> None:
    """best_available() returns NullWhisperBackend when neither backend is available."""
    pass
