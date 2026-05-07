"""
Whisper transcription engine backends — L2 Rödd Hlust substrate.

Defines the WhisperEngine abstract base class and three concrete backends:

- PyWhisperCppBackend: primary backend using the pywhispercpp Python bindings
  (MIT; wraps whisper.cpp). Clean Python API, no subprocess marshalling.
  Lazy model loading: load_model() is called on first utterance, NOT at Kynding.
- CliSubprocessBackend: fallback backend — shells out to a user-installed
  ``whisper-cli`` binary on PATH. Serialises audio via a temp WAV file.
  Zero install pain for HERETIC; slower due to per-utterance subprocess startup.
- NullWhisperBackend: silent fallback — transcribe() always returns an empty
  string. Hlust detects the Null backend and falls back to stdin input.

Hlust selects the backend at init time via ``WhisperEngine.best_available()``.

Lazy-load contract (locked by Architect — resolves audit C-Q-C1):
    load_model() is NEVER called at Kynding (startup). It is called by Hlust on
    the first call to transcribe() during a live ceremony. This prevents blocking
    the startup sequence on a model load that may take several seconds (ggml-base
    is ~147 MB). The ``is_loaded`` property reflects whether load_model() has
    completed. Callers must not call transcribe() if is_loaded is False AND have
    not awaited load_model() — but in practice Hlust always calls load_model()
    before the first transcribe() inside capture_one_utterance().

Audio input contract (shared with microphone.py and vad.py):
    sample_rate : 16 000 Hz
    channels    : 1 (mono)
    dtype       : int16 (raw bytes)
    Whisper natively expects 16 kHz mono float32; PyWhisperCppBackend is
    responsible for the int16->float32 conversion internally.
"""

from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddSttConfig


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class WhisperEngine(abc.ABC):
    """Contract for all Whisper transcription engine backends.

    Implementations load a Whisper model and transcribe raw audio bytes to text.

    Lifecycle (lazy-load, per C-Q-C1 resolution):
        engine = WhisperEngine.best_available(config, logger)
        # ... no model loaded yet; startup proceeds immediately ...
        await engine.load_model()           # blocks until model weights loaded
        text = await engine.transcribe(audio_bytes, sample_rate=16000)
        # ... repeat transcribe() calls without re-loading ...

    The ``is_loaded`` property lets callers check load state before transcribing.
    Hlust always calls load_model() before the first transcribe() call. Callers
    must not bypass this sequence.
    """

    @property
    @abc.abstractmethod
    def is_loaded(self) -> bool:
        """True after load_model() has completed successfully."""

    @classmethod
    @abc.abstractmethod
    def available(cls) -> bool:
        """Return True if this backend can be instantiated on the current platform.

        Probes required dependencies or binaries without raising.
        """

    @abc.abstractmethod
    async def load_model(self) -> None:
        """Load the Whisper model weights from disk.

        Called by Hlust on the first utterance (lazy strategy per C-Q-C1).
        For ``eager`` load strategy (config.stt.load_strategy == 'eager'),
        Hlust calls this at Kynding instead. Either way, this method drives
        all model-loading I/O.

        After this coroutine returns, ``is_loaded`` must be True.

        Raises:
            WhisperModelLoadError: if the model file is missing, corrupt, or
                cannot be loaded by the backend.
        """

    @abc.abstractmethod
    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        """Transcribe raw audio bytes to text.

        Args:
            audio: Concatenated int16 PCM audio bytes from mic capture.
                   Sample rate must match the configured model input (16 kHz).
            sample_rate: The audio sample rate in Hz. Defaults to 16 000.

        Returns:
            Transcribed text string. May be empty if the audio contained no
            recognisable speech. Leading/trailing whitespace is stripped.

        Raises:
            WhisperError: if transcription fails (model error, audio too short, etc.).
            WhisperModelLoadError: if called before load_model() on a backend
                                   that requires explicit loading.
        """

    @staticmethod
    def best_available(
        config: "RoddSttConfig",
        logger: logging.Logger,
    ) -> "WhisperEngine":
        """Factory: return the best available WhisperEngine for this machine.

        Preference order:
            1. PyWhisperCppBackend  — requires pywhispercpp (in [voice] extra)
            2. CliSubprocessBackend — requires whisper-cli binary on PATH
            3. NullWhisperBackend   — always available; never transcribes

        Args:
            config: RoddSttConfig from heretic.yaml. Carries model_path, language.
            logger: Logger instance from grunnr.logger.get_logger.

        Returns:
            A WhisperEngine instance. Never raises — returns NullWhisperBackend
            when no real backend is available so the ceremony can continue
            in stdin fallback mode.
        """
        if PyWhisperCppBackend.available():
            logger.debug("WhisperEngine.best_available: selecting PyWhisperCppBackend")
            return PyWhisperCppBackend(config=config, logger=logger)

        logger.warning(
            "WhisperEngine.best_available: pywhispercpp not available "
            "(try: pip install heretic[voice]). "
            "Checking for whisper-cli binary on PATH."
        )
        if CliSubprocessBackend.available():
            logger.debug("WhisperEngine.best_available: selecting CliSubprocessBackend")
            return CliSubprocessBackend(config=config, logger=logger)

        logger.warning(
            "WhisperEngine.best_available: whisper-cli binary not found on PATH. "
            "Using NullWhisperBackend — Hlust will fall back to stdin input."
        )
        return NullWhisperBackend(config=config, logger=logger)


# ---------------------------------------------------------------------------
# PyWhisperCppBackend — primary backend
# ---------------------------------------------------------------------------

class PyWhisperCppBackend(WhisperEngine):
    """Primary Whisper backend using pywhispercpp Python bindings (MIT).

    pywhispercpp wraps whisper.cpp — the same ggml-based implementation used
    by HERETIC's recommended Whisper setup — via a C extension. It provides a
    clean Python API without subprocess marshalling overhead.

    Model loading is lazy: the ggml model file is loaded from disk on first call
    to load_model(), not at construction. This keeps Kynding fast.

    Audio conversion: pywhispercpp expects float32 audio; Forge will implement
    the int16->float32 conversion (divide by 32768.0) inside transcribe().
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        """Initialise without loading the model.

        Args:
            config: RoddSttConfig; reads model_path and language.
            logger: Logger instance.
        """
        self._config = config
        self._log = logger
        self._model: object | None = None  # pywhispercpp.model.Whisper at runtime
        self._loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        """True after load_model() succeeded."""
        return self._loaded

    @classmethod
    def available(cls) -> bool:
        """Return True if pywhispercpp can be imported."""
        raise NotImplementedError(
            "Forge will implement: attempt `import pywhispercpp.model` and return True. "
            "Catch ImportError, return False. Never raise."
        )

    async def load_model(self) -> None:
        """Load the ggml model from config.model_path.

        Forge will implement: run the blocking pywhispercpp.model.Whisper(model_path)
        load in a thread-pool executor (run_in_executor) so the asyncio event loop
        is not blocked during the several-second model load. Set self._loaded = True
        on success. Raise WhisperModelLoadError on any failure (missing file,
        corrupt ggml, insufficient memory).
        """
        raise NotImplementedError(
            "Forge will implement: run_in_executor(None, pywhispercpp.model.Whisper, model_path), "
            "store result in self._model, set self._loaded = True. "
            "Raise WhisperModelLoadError on FileNotFoundError or ggml load failure."
        )

    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        """Transcribe int16 PCM bytes via pywhispercpp.

        Forge will implement: convert int16 bytes to float32 numpy array
        (divide by 32768.0), run_in_executor(None, self._model.transcribe, float32_array),
        collect segments, join as a single stripped string. Raise WhisperError on failure.
        """
        raise NotImplementedError(
            "Forge will implement: int16 bytes -> float32 array (div 32768.0), "
            "run blocking self._model.transcribe() in executor, "
            "join returned segments into a single stripped text string."
        )


# ---------------------------------------------------------------------------
# CliSubprocessBackend — fallback backend
# ---------------------------------------------------------------------------

class CliSubprocessBackend(WhisperEngine):
    """Fallback Whisper backend using the user-installed whisper-cli binary.

    Serialises each utterance as a temp WAV file, subprocesses to ``whisper-cli``,
    parses the transcript from stdout, and deletes the temp file. No Python bindings
    required — the user installs the whisper.cpp CLI separately.

    Trade-off: per-utterance subprocess startup cost (~100–300 ms on most hardware)
    plus WAV serialisation. Acceptable for voice command workflows; not recommended
    for rapid-fire conversation.

    Binary probe: uses shutil.which("whisper-cli") to check PATH availability.
    The binary name is configurable in future; for v0.3 it is fixed as "whisper-cli".
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        """True after load_model() has been called (no-op for CLI backend)."""
        return self._loaded

    @classmethod
    def available(cls) -> bool:
        """Return True if whisper-cli is found on PATH."""
        raise NotImplementedError(
            "Forge will implement: `import shutil; return shutil.which('whisper-cli') is not None`."
        )

    async def load_model(self) -> None:
        """No-op for CLI backend — the binary loads the model per invocation.

        Sets self._loaded = True to satisfy the is_loaded contract.
        Verifies the whisper-cli binary is still on PATH and the model file
        exists, raising WhisperModelLoadError if either is absent.
        """
        raise NotImplementedError(
            "Forge will implement: verify whisper-cli on PATH (shutil.which) "
            "and model_path exists (Path(model_path).exists()); "
            "set self._loaded = True; raise WhisperModelLoadError on missing binary or file."
        )

    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        """Write audio to a temp WAV file, invoke whisper-cli, return transcript.

        Forge will implement:
            1. Write audio bytes as a valid 16 kHz mono int16 WAV file in a
               NamedTemporaryFile (use the wave stdlib module).
            2. subprocess.run(['whisper-cli', '-m', model_path, '-l', language,
                               '--output-txt', '-f', tmp_wav_path], ...)
            3. Parse stdout for the transcript text (strip timing markup).
            4. Delete the temp WAV file.
            5. Return stripped text. Raise WhisperError on non-zero exit code.
        """
        raise NotImplementedError(
            "Forge will implement: write int16 PCM to temp WAV (wave stdlib), "
            "subprocess whisper-cli with model_path and language from config, "
            "parse stdout transcript, cleanup temp file, return stripped text."
        )


# ---------------------------------------------------------------------------
# NullWhisperBackend — silent fallback
# ---------------------------------------------------------------------------

class NullWhisperBackend(WhisperEngine):
    """No-op Whisper backend. Always available; transcribe() returns empty string.

    Used when no real Whisper backend is available. Hlust detects the Null backend
    and falls back to stdin input for the ceremony rather than attempting transcription.
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @classmethod
    def available(cls) -> bool:
        """Always True."""
        return True

    async def load_model(self) -> None:
        """No-op — sets is_loaded = True."""
        self._loaded = True
        self._log.debug("NullWhisperBackend.load_model: no-op (null backend)")

    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        """Always returns an empty string."""
        self._log.debug("NullWhisperBackend.transcribe: no-op (null backend) — returning empty")
        return ""
