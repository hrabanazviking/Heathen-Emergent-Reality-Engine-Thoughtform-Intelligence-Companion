"""
Tests — WhisperEngine backends (L2 Rödd Hlust substrate).

pywhispercpp, subprocess, and shutil.which are all mocked throughout.
No real Whisper model or binary is required.
"""

from __future__ import annotations

import logging
import struct
import sys
import types
import wave
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.rodd.config_model import RoddSttConfig
from heretic.rodd.errors import WhisperError, WhisperModelLoadError
from heretic.rodd.whisper_engine import (
    CliSubprocessBackend,
    NullWhisperBackend,
    PyWhisperCppBackend,
    WhisperEngine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(model_path: str = "models/test.bin", language: str = "en") -> RoddSttConfig:
    return RoddSttConfig(model_path=model_path, language=language)


def _make_logger(name: str = "test.whisper") -> logging.Logger:
    return logging.getLogger(name)


def _make_mock_pywhispercpp(transcription: str = "hello world") -> types.ModuleType:
    """Build a minimal mock pywhispercpp.model module."""
    pwc_model_mock = MagicMock()
    model_instance = MagicMock()
    segment = MagicMock()
    segment.text = transcription
    model_instance.transcribe.return_value = [segment]
    pwc_model_mock.Whisper.return_value = model_instance
    return pwc_model_mock


def _silent_audio_bytes(n_frames: int = 480) -> bytes:
    """Return raw int16 PCM bytes representing silence."""
    return b"\x00" * (n_frames * 2)


# ---------------------------------------------------------------------------
# NullWhisperBackend
# ---------------------------------------------------------------------------

def test_null_whisper_always_available() -> None:
    """NullWhisperBackend.available() is always True."""
    assert NullWhisperBackend.available() is True


@pytest.mark.asyncio
async def test_null_whisper_load_model_sets_is_loaded() -> None:
    """NullWhisperBackend.load_model() sets is_loaded to True."""
    engine = NullWhisperBackend(config=_make_config(), logger=_make_logger())
    assert engine.is_loaded is False
    await engine.load_model()
    assert engine.is_loaded is True


@pytest.mark.asyncio
async def test_null_whisper_transcribe_returns_empty() -> None:
    """NullWhisperBackend.transcribe() returns an empty string."""
    engine = NullWhisperBackend(config=_make_config(), logger=_make_logger())
    result = await engine.transcribe(_silent_audio_bytes(), sample_rate=16_000)
    assert result == ""


@pytest.mark.asyncio
async def test_null_whisper_load_model_idempotent() -> None:
    """NullWhisperBackend.load_model() can be called twice safely."""
    engine = NullWhisperBackend(config=_make_config(), logger=_make_logger())
    await engine.load_model()
    await engine.load_model()
    assert engine.is_loaded is True


# ---------------------------------------------------------------------------
# Lazy-load invariant
# ---------------------------------------------------------------------------

def test_pywhispercpp_is_loaded_false_at_construction() -> None:
    """PyWhisperCppBackend.is_loaded is False immediately after __init__."""
    engine = PyWhisperCppBackend(config=_make_config(), logger=_make_logger())
    assert engine.is_loaded is False


def test_cli_subprocess_is_loaded_false_at_construction() -> None:
    """CliSubprocessBackend.is_loaded is False immediately after __init__."""
    engine = CliSubprocessBackend(config=_make_config(), logger=_make_logger())
    assert engine.is_loaded is False


# ---------------------------------------------------------------------------
# PyWhisperCppBackend
# ---------------------------------------------------------------------------

def test_pywhispercpp_available_when_importable(monkeypatch) -> None:
    """PyWhisperCppBackend.available() returns True when pywhispercpp is importable."""
    mock_module = MagicMock()
    monkeypatch.setitem(sys.modules, "pywhispercpp", mock_module)
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", MagicMock())
    assert PyWhisperCppBackend.available() is True


def test_pywhispercpp_available_false_on_import_error(monkeypatch) -> None:
    """PyWhisperCppBackend.available() returns False on ImportError."""
    monkeypatch.setitem(sys.modules, "pywhispercpp", None)
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", None)
    assert PyWhisperCppBackend.available() is False


@pytest.mark.asyncio
async def test_pywhispercpp_load_model_raises_on_missing_file(tmp_path) -> None:
    """PyWhisperCppBackend.load_model() raises WhisperModelLoadError for missing model."""
    missing_path = "models/does_not_exist.bin"
    engine = PyWhisperCppBackend(
        config=_make_config(model_path=missing_path),
        logger=_make_logger(),
    )
    with pytest.raises(WhisperModelLoadError, match="not found"):
        await engine.load_model()


@pytest.mark.asyncio
async def test_pywhispercpp_load_model_sets_is_loaded(monkeypatch, tmp_path) -> None:
    """PyWhisperCppBackend.load_model() sets is_loaded after successful load (mocked)."""
    # Create a fake model file so the existence check passes
    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake_model")

    pwc_mock = _make_mock_pywhispercpp()
    monkeypatch.setitem(sys.modules, "pywhispercpp", MagicMock())
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", pwc_mock)

    engine = PyWhisperCppBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    assert engine.is_loaded is False
    await engine.load_model()
    assert engine.is_loaded is True


@pytest.mark.asyncio
async def test_pywhispercpp_load_model_idempotent(monkeypatch, tmp_path) -> None:
    """PyWhisperCppBackend.load_model() is idempotent (second call is no-op)."""
    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake_model")

    pwc_mock = _make_mock_pywhispercpp()
    monkeypatch.setitem(sys.modules, "pywhispercpp", MagicMock())
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", pwc_mock)

    engine = PyWhisperCppBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    await engine.load_model()
    await engine.load_model()  # second call — should not reload

    # Whisper() constructor called only once
    pwc_mock.Whisper.assert_called_once()


@pytest.mark.asyncio
async def test_pywhispercpp_transcribe_converts_int16_to_float32(monkeypatch, tmp_path) -> None:
    """PyWhisperCppBackend.transcribe() converts int16 bytes to float32 before calling model."""
    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake_model")

    pwc_mock = _make_mock_pywhispercpp("hello world")
    monkeypatch.setitem(sys.modules, "pywhispercpp", MagicMock())
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", pwc_mock)

    # numpy is actually needed for this test since the implementation uses it
    import numpy as np
    engine = PyWhisperCppBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    await engine.load_model()

    # Create a simple audio buffer with known int16 values
    n_samples = 480
    audio_bytes = struct.pack(f"<{n_samples}h", *(16384 for _ in range(n_samples)))
    result = await engine.transcribe(audio_bytes, sample_rate=16_000)

    assert result == "hello world"
    # Check that the model's transcribe was called with a float32 array
    model_instance = pwc_mock.Whisper.return_value
    model_instance.transcribe.assert_called_once()
    passed_array = model_instance.transcribe.call_args.args[0]
    assert passed_array.dtype == np.float32
    # Values should be normalised to [-1.0, 1.0]
    assert abs(float(passed_array[0]) - (16384 / 32768.0)) < 0.0001


@pytest.mark.asyncio
async def test_pywhispercpp_transcribe_raises_before_load_model(monkeypatch) -> None:
    """PyWhisperCppBackend.transcribe() raises WhisperModelLoadError if not yet loaded."""
    engine = PyWhisperCppBackend(config=_make_config(), logger=_make_logger())
    with pytest.raises(WhisperModelLoadError):
        await engine.transcribe(_silent_audio_bytes())


@pytest.mark.asyncio
async def test_pywhispercpp_transcribe_returns_empty_on_zero_audio(monkeypatch, tmp_path) -> None:
    """PyWhisperCppBackend.transcribe() returns empty string for zero-length audio."""
    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake_model")

    pwc_mock = _make_mock_pywhispercpp("should not appear")
    monkeypatch.setitem(sys.modules, "pywhispercpp", MagicMock())
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", pwc_mock)

    engine = PyWhisperCppBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    await engine.load_model()
    result = await engine.transcribe(b"", sample_rate=16_000)
    assert result == ""


# ---------------------------------------------------------------------------
# CliSubprocessBackend
# ---------------------------------------------------------------------------

def test_cli_available_when_binary_on_path(monkeypatch) -> None:
    """CliSubprocessBackend.available() returns True when whisper-cli found on PATH."""
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/local/bin/whisper-cli" if name == "whisper-cli" else None)
    assert CliSubprocessBackend.available() is True


def test_cli_available_false_when_binary_absent(monkeypatch) -> None:
    """CliSubprocessBackend.available() returns False when whisper-cli not on PATH."""
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert CliSubprocessBackend.available() is False


@pytest.mark.asyncio
async def test_cli_load_model_sets_is_loaded(monkeypatch, tmp_path) -> None:
    """CliSubprocessBackend.load_model() sets is_loaded when binary and model exist."""
    import shutil
    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake")
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/local/bin/whisper-cli")

    engine = CliSubprocessBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    await engine.load_model()
    assert engine.is_loaded is True


@pytest.mark.asyncio
async def test_cli_load_model_raises_when_binary_absent(monkeypatch) -> None:
    """CliSubprocessBackend.load_model() raises WhisperModelLoadError when whisper-cli absent."""
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)

    engine = CliSubprocessBackend(config=_make_config(), logger=_make_logger())
    with pytest.raises(WhisperModelLoadError, match="whisper-cli"):
        await engine.load_model()


@pytest.mark.asyncio
async def test_cli_transcribe_writes_wav_and_parses_output(monkeypatch, tmp_path) -> None:
    """CliSubprocessBackend.transcribe() writes a temp WAV and parses subprocess stdout."""
    import shutil
    import subprocess as sp

    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake")
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/local/bin/whisper-cli")

    # Mock subprocess.run to return a successful result
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "  hello from whisper  "
    mock_result.stderr = ""
    monkeypatch.setattr(sp, "run", lambda *a, **kw: mock_result)

    engine = CliSubprocessBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    await engine.load_model()

    audio = b"\x00" * 960
    result = await engine.transcribe(audio, sample_rate=16_000)
    assert result == "hello from whisper"  # stripped


@pytest.mark.asyncio
async def test_cli_transcribe_raises_on_nonzero_exit(monkeypatch, tmp_path) -> None:
    """CliSubprocessBackend.transcribe() raises WhisperError on non-zero exit code."""
    import shutil
    import subprocess as sp

    model_file = tmp_path / "test.bin"
    model_file.write_bytes(b"fake")
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/local/bin/whisper-cli")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "fatal error"
    monkeypatch.setattr(sp, "run", lambda *a, **kw: mock_result)

    engine = CliSubprocessBackend(
        config=_make_config(model_path=str(model_file)),
        logger=_make_logger(),
    )
    await engine.load_model()

    with pytest.raises(WhisperError):
        await engine.transcribe(b"\x00" * 960, sample_rate=16_000)


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

def test_whisper_best_available_prefers_pywhispercpp(monkeypatch) -> None:
    """best_available() returns PyWhisperCppBackend when pywhispercpp is present."""
    monkeypatch.setattr(PyWhisperCppBackend, "available", classmethod(lambda cls: True))
    config = _make_config()
    logger = _make_logger("test.whisper_factory")
    engine = WhisperEngine.best_available(config, logger)
    assert isinstance(engine, PyWhisperCppBackend)


def test_whisper_best_available_falls_back_to_cli(monkeypatch) -> None:
    """best_available() returns CliSubprocessBackend when pywhispercpp absent."""
    monkeypatch.setattr(PyWhisperCppBackend, "available", classmethod(lambda cls: False))
    monkeypatch.setattr(CliSubprocessBackend, "available", classmethod(lambda cls: True))
    config = _make_config()
    logger = _make_logger("test.whisper_factory")
    engine = WhisperEngine.best_available(config, logger)
    assert isinstance(engine, CliSubprocessBackend)


def test_whisper_best_available_falls_back_to_null(monkeypatch) -> None:
    """best_available() returns NullWhisperBackend when neither backend is available."""
    monkeypatch.setattr(PyWhisperCppBackend, "available", classmethod(lambda cls: False))
    monkeypatch.setattr(CliSubprocessBackend, "available", classmethod(lambda cls: False))
    config = _make_config()
    logger = _make_logger("test.whisper_factory")
    engine = WhisperEngine.best_available(config, logger)
    assert isinstance(engine, NullWhisperBackend)


def test_whisper_best_available_never_raises(monkeypatch) -> None:
    """best_available() never raises regardless of backend state."""
    monkeypatch.setattr(PyWhisperCppBackend, "available", classmethod(lambda cls: False))
    monkeypatch.setattr(CliSubprocessBackend, "available", classmethod(lambda cls: False))
    config = _make_config()
    logger = _make_logger("test.whisper_factory")
    engine = WhisperEngine.best_available(config, logger)
    assert engine is not None
