"""
ChatterBox TTS client — L2 Rödd Tunga substrate.

This module defines the ChatterboxClient abstract base class and the
ChatterboxHttpClient concrete skeleton. All business logic is NotImplementedError
stubs; Forge (Eldra Járnsdóttir) will implement the HTTP communication in Wave 2.

ChatterBox API reference: TASK_HERETIC_v0.2_FIRST_VOICE.md §3
Endpoint: http://<pi-ip>:7851
  GET  /health             — service health check
  GET  /v1/models          — list available TTS model variants
  POST /v1/audio/speech    — synthesise WAV audio from text
"""

from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddTtsConfig


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class ChatterboxClient(abc.ABC):
    """Contract for all ChatterBox TTS service clients.

    Implementations communicate with a ChatterBox instance (or a compatible
    stand-in) and return raw WAV bytes. The base class enforces the interface;
    ChatterboxHttpClient is the production implementation.

    Lifecycle:
        client = ChatterboxHttpClient(config, logger)
        await client.open()
        wav = await client.synthesize("Hello, world.")
        await client.close()

    Context manager usage is the preferred pattern — implementations should
    support ``async with ChatterboxHttpClient(...) as client:``.
    """

    @abc.abstractmethod
    async def open(self) -> None:
        """Initialise the HTTP session and verify the endpoint is reachable.

        Raises:
            ChatterboxConnectionError: if the endpoint is unreachable.
            ChatterboxAuthError: if HTTP 401/403 is returned during probe.
            ChatterboxTimeoutError: if the health check exceeds the timeout.
        """

    @abc.abstractmethod
    async def health(self) -> dict:
        """Fetch the /health response from ChatterBox.

        Returns:
            dict: The JSON body of the /health response.

        Raises:
            ChatterboxConnectionError: on network failure.
            ChatterboxApiError: on unexpected HTTP status.
        """

    @abc.abstractmethod
    async def list_models(self) -> list[dict]:
        """Fetch the list of available TTS model variants from /v1/models.

        Returns:
            list[dict]: Each dict represents one model variant as returned
            by ChatterBox. Typical fields: id, name, description.

        Raises:
            ChatterboxConnectionError: on network failure.
            ChatterboxApiError: on unexpected HTTP status.
        """

    @abc.abstractmethod
    async def synthesize(
        self,
        text: str,
        *,
        model: str | None = None,
        voice: str | None = None,
        language_id: str | None = None,
        exaggeration: float | None = None,
        cfg_weight: float | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        repetition_penalty: float | None = None,
    ) -> bytes:
        """Send text to ChatterBox and return raw WAV audio bytes.

        Posts to /v1/audio/speech with the OpenAI-compat-style request body
        documented in TASK_HERETIC_v0.2_FIRST_VOICE.md §3.

        Args:
            text: The text to synthesise. 1–4000 characters. Callers must respect
                  the 4000-char limit; Tunga's chunker is responsible for splitting.
            model: Override the config model. None = use RoddTtsConfig.model.
            voice: Path to a voice prompt .wav file (>= 5s for turbo). None = default.
            language_id: BCP-47 code. Only meaningful for the ``multilingual`` model.
            exaggeration: Emotional exaggeration 0.0–2.0. None = use config default.
            cfg_weight: CFG guidance 0.0–2.0. None = use config default.
            temperature: Sampling temperature 0.05–2.0. None = use config default.
            top_p: Nucleus sampling 0.0–1.0. None = use config default.
            repetition_penalty: Repetition penalty 0.1–5.0. None = use config default.

        Returns:
            bytes: Raw WAV audio data (Content-Type: audio/wav).

        Raises:
            ChatterboxConnectionError: endpoint not reachable.
            ChatterboxAuthError: HTTP 401/403.
            ChatterboxTimeoutError: request exceeded ``request_timeout_seconds``.
            ChatterboxApiError: non-200 HTTP status or non-WAV response body.
            ValueError: if text is empty or exceeds 4000 characters.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the underlying HTTP session and release resources.

        Safe to call even if open() was never called or failed.
        After close(), this instance must not be reused.
        """

    @property
    @abc.abstractmethod
    def is_open(self) -> bool:
        """True if the HTTP session is initialised and not yet closed."""


# ---------------------------------------------------------------------------
# Concrete HTTP implementation skeleton
# ---------------------------------------------------------------------------

class ChatterboxHttpClient(ChatterboxClient):
    """Production ChatterBox client — httpx-based, async.

    Uses httpx (already a project dependency via L1 Bifröst) to communicate
    with the ChatterBox service over HTTP. Fully async; compatible with the
    Tunga orchestrator's asyncio event loop.

    Configuration is read from RoddTtsConfig at construction time; none of
    the settings are hardcoded here — all are drawn from config fields.

    Forge will implement all method bodies. The skeleton declares types,
    attributes, and docstrings to give Forge a complete implementation target.
    """

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        """Initialise the client from config.

        Args:
            config: RoddTtsConfig holding endpoint, timeouts, and synthesis defaults.
            logger: Logger instance (from grunnr.logger.get_logger). Must not be None.
        """
        self._config = config
        self._log = logger
        # Forge: initialise httpx.AsyncClient here — do NOT open a session yet.
        # Session lifecycle is managed by open() / close().
        self._client: object | None = None  # type: ignore[assignment]
        self._open: bool = False

    @property
    def is_open(self) -> bool:
        """True if the HTTP session is initialised and not yet closed."""
        return self._open

    async def open(self) -> None:
        """Initialise the httpx.AsyncClient and probe /health.

        Forge will implement:
        - Create httpx.AsyncClient with timeout=Timeout(connect=15, read=self._config.request_timeout_seconds)
        - GET {self._config.endpoint}/health
        - On HTTP error map to the appropriate ChatterboxError subclass
        - Set self._open = True on success
        - Log the endpoint and health response at DEBUG level
        """
        raise NotImplementedError(
            "Forge will implement: create httpx.AsyncClient, probe /health, "
            "map HTTP errors to ChatterboxError subclasses, set self._open = True."
        )

    async def health(self) -> dict:
        """Fetch /health from ChatterBox.

        Forge will implement:
        - GET {self._config.endpoint}/health
        - Return parsed JSON dict
        - Raise ChatterboxConnectionError on network failure
        - Raise ChatterboxApiError on non-200 status
        """
        raise NotImplementedError(
            "Forge will implement: GET /health, parse JSON, raise ChatterboxConnectionError "
            "or ChatterboxApiError as appropriate."
        )

    async def list_models(self) -> list[dict]:
        """Fetch /v1/models from ChatterBox.

        Forge will implement:
        - GET {self._config.endpoint}/v1/models
        - Return list of model dicts from the JSON body
        - Raise ChatterboxConnectionError on network failure
        - Raise ChatterboxApiError on non-200 status
        """
        raise NotImplementedError(
            "Forge will implement: GET /v1/models, parse JSON array, return list[dict], "
            "raise appropriate error types on failure."
        )

    async def synthesize(
        self,
        text: str,
        *,
        model: str | None = None,
        voice: str | None = None,
        language_id: str | None = None,
        exaggeration: float | None = None,
        cfg_weight: float | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        repetition_penalty: float | None = None,
    ) -> bytes:
        """POST /v1/audio/speech and return raw WAV bytes.

        Forge will implement:
        - Build the request body dict per ChatterBox API spec in §3 of the task file:
            {
              "model": model or self._config.model,
              "input": text,
              "voice": voice or self._config.voice_prompt_path or None,
              "response_format": "wav",
              "language_id": language_id or self._config.language_id,
              "exaggeration": exaggeration if exaggeration is not None else self._config.exaggeration,
              "cfg_weight": cfg_weight if cfg_weight is not None else self._config.cfg_weight,
              "temperature": temperature if temperature is not None else self._config.temperature,
              "top_p": top_p if top_p is not None else self._config.top_p,
              "repetition_penalty": repetition_penalty if repetition_penalty is not None
                                    else self._config.repetition_penalty,
            }
          (Omit None values from the body — ChatterBox uses its own defaults for absent fields.)
        - POST {self._config.endpoint}/v1/audio/speech with the body above
        - Verify Content-Type is audio/wav; raise ChatterboxApiError if not
        - Return response.content (raw bytes)
        - Validate text: raise ValueError if empty or len > 4000
        - Raise ChatterboxConnectionError on transport failure
        - Raise ChatterboxTimeoutError on httpx.TimeoutException
        - Raise ChatterboxAuthError on HTTP 401/403
        - Raise ChatterboxApiError on other non-200 statuses
        - Log synthesis request at DEBUG (text length, model, latency_ms)
        """
        raise NotImplementedError(
            "Forge will implement: build ChatterBox request body from config + overrides, "
            "POST /v1/audio/speech, validate WAV Content-Type, return raw bytes, "
            "map all HTTP/network errors to appropriate ChatterboxError subclasses."
        )

    async def close(self) -> None:
        """Close the httpx.AsyncClient session.

        Forge will implement:
        - If self._client is not None, call await self._client.aclose()
        - Set self._open = False
        - Set self._client = None
        - Log close at DEBUG
        """
        raise NotImplementedError(
            "Forge will implement: await self._client.aclose(), "
            "set self._open = False, nullify self._client."
        )

    async def __aenter__(self) -> "ChatterboxHttpClient":
        """Forge will implement: call self.open() and return self."""
        raise NotImplementedError(
            "Forge will implement: await self.open(); return self."
        )

    async def __aexit__(self, *args: object) -> None:
        """Forge will implement: call self.close() unconditionally."""
        raise NotImplementedError(
            "Forge will implement: await self.close()."
        )
