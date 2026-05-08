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
import asyncio
import logging
import shutil
import struct
import tempfile
import threading
import wave
from pathlib import Path
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

    Audio conversion: pywhispercpp expects float32 audio; transcribe() converts
    the incoming int16 bytes by dividing each sample by 32768.0.

    Thread safety: load_model() uses a threading.Lock to prevent concurrent loads
    if the caller ever invokes it from multiple threads (unusual but defensive).
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
        self._load_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        """True after load_model() succeeded."""
        return self._loaded

    @classmethod
    def available(cls) -> bool:
        """Return True if pywhispercpp can be imported.

        Does NOT check whether the model file exists — that is checked at
        load_model() time so the factory can still select this backend even if
        the model hasn't been downloaded yet.

        Never raises.
        """
        try:
            import importlib
            importlib.import_module("pywhispercpp.model")
            return True
        except ImportError:
            return False

    async def load_model(self) -> None:
        """Load the ggml model from config.model_path.

        Runs the blocking pywhispercpp.model.Whisper(model_path) call in a
        thread-pool executor to avoid blocking the asyncio event loop during
        the several-second model load.

        Idempotent: if already loaded, returns immediately.

        Raises:
            WhisperModelLoadError: if the model file is missing or cannot be loaded.
        """
        from heretic.rodd.errors import WhisperModelLoadError

        # Idempotent: fast-path if already loaded
        if self._loaded:
            return

        model_path = Path(self._config.model_path)
        if not model_path.is_absolute():
            # Relative paths are resolved from the current working directory,
            # which is typically the project root when heretic is invoked via CLI.
            # This matches the RULES.AI requirement: no absolute paths in config.
            model_path = Path.cwd() / model_path

        if not model_path.exists():
            raise WhisperModelLoadError(
                f"PyWhisperCppBackend.load_model: model file not found at {self._config.model_path}. "
                f"Download the ggml model and place it at the configured path.",
                model_path=self._config.model_path,
            )

        self._log.info(
            "PyWhisperCppBackend: loading model from %r (this may take a few seconds)...",
            str(self._config.model_path),
        )

        def _load_blocking() -> object:
            # This runs on the thread pool — NOT the asyncio thread.
            # threading.Lock protects against concurrent load_model() calls.
            with self._load_lock:
                if self._loaded:
                    # Another coroutine beat us to it — short-circuit.
                    return self._model
                import importlib
                pwc_model = importlib.import_module("pywhispercpp.model")
                return pwc_model.Whisper(str(model_path))

        try:
            model = await asyncio.get_running_loop().run_in_executor(None, _load_blocking)
            self._model = model
            self._loaded = True
            self._log.info("PyWhisperCppBackend: model loaded successfully")
        except Exception as exc:
            raise WhisperModelLoadError(
                f"PyWhisperCppBackend.load_model failed: {exc}",
                model_path=self._config.model_path,
            ) from exc

    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        """Transcribe int16 PCM bytes via pywhispercpp.

        Converts int16 bytes to float32 (divides by 32768.0) and runs the
        blocking transcription in a thread-pool executor.

        Args:
            audio: Raw int16 little-endian PCM bytes.
            sample_rate: Must be 16 000 Hz for whisper.cpp.

        Returns:
            Stripped transcript string. Empty if no speech found.

        Raises:
            WhisperError: on transcription failure.
            WhisperModelLoadError: if model not loaded.
        """
        from heretic.rodd.errors import WhisperError, WhisperModelLoadError

        if not self._loaded or self._model is None:
            raise WhisperModelLoadError(
                "PyWhisperCppBackend.transcribe called before load_model(). "
                "Call await engine.load_model() first."
            )

        if len(audio) < 2:
            return ""

        def _transcribe_blocking() -> str:
            # Convert int16 little-endian bytes to float32 numpy array.
            # We need numpy here — it's in the [voice] extra alongside pywhispercpp.
            import numpy as np
            n_samples = len(audio) // 2
            int16_array = np.frombuffer(audio[:n_samples * 2], dtype=np.int16)
            float32_array = int16_array.astype(np.float32) / 32768.0

            # pywhispercpp.model.Whisper.transcribe() returns a list of Segment objects.
            # Each segment has a .text attribute.
            segments = self._model.transcribe(float32_array)
            return " ".join(seg.text for seg in segments if hasattr(seg, "text")).strip()

        try:
            result = await asyncio.get_running_loop().run_in_executor(None, _transcribe_blocking)
            return result
        except Exception as exc:
            raise WhisperError(
                f"PyWhisperCppBackend.transcribe failed: {exc}"
            ) from exc


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
    The binary name is fixed as "whisper-cli" for v0.3.
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
        """Return True if whisper-cli is found on PATH.

        Uses shutil.which which is cross-platform (Windows .exe extension handled).
        Never raises.
        """
        try:
            return shutil.which("whisper-cli") is not None
        except Exception:
            return False

    async def load_model(self) -> None:
        """Verify binary and model file exist; set is_loaded = True.

        The CLI backend loads the model on each subprocess invocation, so
        there is no persistent in-memory load here. This method validates that
        the necessary resources are present before the first transcription.

        Raises:
            WhisperModelLoadError: if the whisper-cli binary or model file is absent.
        """
        from heretic.rodd.errors import WhisperModelLoadError

        if self._loaded:
            return

        binary = shutil.which("whisper-cli")
        if binary is None:
            raise WhisperModelLoadError(
                "CliSubprocessBackend.load_model: whisper-cli binary not found on PATH. "
                "Install whisper.cpp and ensure 'whisper-cli' is on your PATH."
            )

        model_path = Path(self._config.model_path)
        if not model_path.is_absolute():
            model_path = Path.cwd() / model_path

        if not model_path.exists():
            raise WhisperModelLoadError(
                f"CliSubprocessBackend.load_model: model file not found at "
                f"{self._config.model_path}.",
                model_path=self._config.model_path,
            )

        self._loaded = True
        self._log.info(
            "CliSubprocessBackend: binary=%r, model=%r — ready",
            binary,
            str(self._config.model_path),
        )

    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        """Write audio to a temp WAV file, invoke whisper-cli, return transcript.

        Sequence:
            1. Write int16 PCM bytes as a valid 16 kHz mono int16 WAV file.
            2. subprocess whisper-cli with model_path, language, and audio file.
            3. Parse stdout for transcript text (strips any timing markup).
            4. Delete the temp WAV file.
            5. Return stripped text.

        Args:
            audio: Raw int16 little-endian PCM bytes.
            sample_rate: Must be 16 000 Hz.

        Returns:
            Stripped transcript string.

        Raises:
            WhisperError: on subprocess failure or non-zero exit code.
        """
        import subprocess
        from heretic.rodd.errors import WhisperError, WhisperModelLoadError

        if not self._loaded:
            raise WhisperModelLoadError(
                "CliSubprocessBackend.transcribe called before load_model()."
            )

        model_path = Path(self._config.model_path)
        if not model_path.is_absolute():
            model_path = Path.cwd() / model_path

        def _run_blocking() -> str:
            # Write audio to a temp WAV file using the stdlib wave module.
            # NamedTemporaryFile with delete=False so we can pass the path to subprocess,
            # then clean up manually.
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                with wave.open(tmp_path, "wb") as wav_out:
                    wav_out.setnchannels(1)       # mono
                    wav_out.setsampwidth(2)        # int16 = 2 bytes per sample
                    wav_out.setframerate(sample_rate)
                    wav_out.writeframes(audio)

                # Invoke whisper-cli with the audio file and model
                cmd = [
                    "whisper-cli",
                    "-m", str(model_path),
                    "-l", self._config.language,
                    "--output-txt",
                    "--no-timestamps",
                    "-f", tmp_path,
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 60-second hard cap for transcription
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"whisper-cli exited with code {result.returncode}: {result.stderr}"
                    )
                # Parse stdout — whisper-cli prints lines like "[00:00:00 --> 00:00:02] text"
                # With --no-timestamps the output is plain text; strip leading/trailing whitespace.
                transcript = result.stdout.strip()
                return transcript
            finally:
                # Always clean up the temp file — even on exception
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass

        try:
            result = await asyncio.get_running_loop().run_in_executor(None, _run_blocking)
            return result
        except Exception as exc:
            raise WhisperError(
                f"CliSubprocessBackend.transcribe failed: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# NullWhisperBackend — silent fallback
# ---------------------------------------------------------------------------

class NullWhisperBackend(WhisperEngine):
    """No-op Whisper backend. Always available; transcribe() returns empty string.

    Used when no real Whisper backend is available. Hlust detects the Null backend
    via isinstance() and falls back to stdin input for the ceremony rather than
    attempting transcription.
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
