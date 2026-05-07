"""
ChatterBox TTS client — L2 Rödd Tunga substrate.

Implements the ChatterboxClient ABC and the ChatterboxHttpClient concrete class.

ChatterBox API reference: TASK_HERETIC_v0.2_FIRST_VOICE.md §3
Endpoint: http://<pi-ip>:7851
  GET  /health             — service health check
  GET  /v1/models          — list available TTS model variants
  POST /v1/audio/speech    — synthesise WAV audio from text

Drift note (DATA_FLOW.md §4.6.1): LAYER_INTERFACES.md §L2 documents a `speed: 1.0`
field that does not exist in the live ChatterBox API. The `speed` field in RoddTtsConfig
is accepted and stored by the config parser but has no effect — it is silently ignored
when building the request body. See _build_request_body() below.

Drift note (DATA_FLOW.md §4.6.1): `voice_id` in the config is a WAV file PATH for
voice cloning, not a string identifier. When voice_id is "default" or empty, the
`voice` field is omitted from the request body and ChatterBox uses its built-in voice.
"""

from __future__ import annotations

import abc
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from heretic.rodd.errors import (
    ChatterboxApiError,
    ChatterboxAuthError,
    ChatterboxConnectionError,
    ChatterboxTimeoutError,
)

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
# Concrete HTTP implementation
# ---------------------------------------------------------------------------

class ChatterboxHttpClient(ChatterboxClient):
    """Production ChatterBox client — httpx-based, async.

    Uses httpx (already a project dependency via L1 Bifröst) to communicate
    with the ChatterBox service over HTTP. Fully async; compatible with the
    Tunga orchestrator's asyncio event loop.

    Configuration is read from RoddTtsConfig at construction time; none of
    the settings are hardcoded here — all are drawn from config fields.
    """

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        """Initialise the client from config.

        Args:
            config: RoddTtsConfig holding endpoint, timeouts, and synthesis defaults.
            logger: Logger instance (from grunnr.logger.get_logger). Must not be None.
        """
        self._config = config
        self._log = logger
        # HTTP session created in open(), not here — open() manages the lifecycle.
        self._client: httpx.AsyncClient | None = None
        self._open: bool = False

    @property
    def is_open(self) -> bool:
        """True if the HTTP session is initialised and not yet closed."""
        return self._open

    def _make_timeout(self) -> httpx.Timeout:
        """Build an httpx Timeout from config.

        Uses a shorter connect timeout (15s) so failures at Kynding are snappy,
        while the read timeout matches request_timeout_seconds for long synthesis.
        """
        return httpx.Timeout(
            connect=15.0,
            read=float(self._config.request_timeout_seconds),
            write=30.0,
            pool=5.0,
        )

    def _resolve_voice_path(self, voice_value: str | None) -> str | None:
        """Resolve a voice path value to an absolute path string for the API.

        DATA_FLOW.md §4.6.1 drift note: ChatterBox's `voice` field expects a WAV
        file path for voice cloning, not a symbolic identifier. When the configured
        value is "default" or empty, we omit the field so ChatterBox uses its own
        built-in voice. Otherwise, we expand ~ and resolve relative paths against
        the current working directory (callers provide absolute-resolved paths from
        grunnr.paths; this is a belt-and-suspenders guard).

        Returns None when the voice field should be omitted from the request body.
        """
        if not voice_value or voice_value.strip().lower() == "default":
            return None
        # Expand user home dir and resolve to absolute
        resolved = Path(voice_value).expanduser().resolve()
        return str(resolved)

    def _build_request_body(
        self,
        text: str,
        model: str | None,
        voice: str | None,
        language_id: str | None,
        exaggeration: float | None,
        cfg_weight: float | None,
        temperature: float | None,
        top_p: float | None,
        repetition_penalty: float | None,
    ) -> dict:
        """Assemble the /v1/audio/speech request body from config + per-call overrides.

        Only non-None fields are included in the output dict — ChatterBox uses its own
        defaults for absent optional fields. This prevents sending null values to the API.

        Drift note (DATA_FLOW.md §4.6.1): The `speed` field from LAYER_INTERFACES.md §L2
        has NO corresponding field in the live ChatterBox API. We do NOT include it in the
        request body. The config field is stored but silently ignored here. The Architect
        will correct LAYER_INTERFACES.md in a future pass.
        """
        body: dict = {
            "model": model if model is not None else self._config.model,
            "input": text,
            "response_format": "wav",
        }

        # Resolve voice path — omit if "default" or empty (use ChatterBox built-in)
        effective_voice = voice if voice is not None else self._config.voice_prompt_path
        resolved_voice = self._resolve_voice_path(effective_voice)
        if resolved_voice is not None:
            body["voice"] = resolved_voice

        # Optional synthesis parameters — include only when non-None
        effective_language = language_id if language_id is not None else self._config.language_id
        if effective_language and effective_language != "en":
            # language_id is only meaningful for the multilingual model; include when set
            body["language_id"] = effective_language

        effective_exaggeration = exaggeration if exaggeration is not None else self._config.exaggeration
        body["exaggeration"] = effective_exaggeration

        effective_cfg = cfg_weight if cfg_weight is not None else self._config.cfg_weight
        body["cfg_weight"] = effective_cfg

        effective_temp = temperature if temperature is not None else self._config.temperature
        body["temperature"] = effective_temp

        effective_top_p = top_p if top_p is not None else self._config.top_p
        body["top_p"] = effective_top_p

        effective_rep = repetition_penalty if repetition_penalty is not None else self._config.repetition_penalty
        body["repetition_penalty"] = effective_rep

        # NOTE: `speed` from config is intentionally NOT included here.
        # The live ChatterBox API does not support a speed field (DATA_FLOW.md §4.6.1).
        # Logging at debug only when speed is non-default so operators are aware.
        if hasattr(self._config, "speed") and self._config.speed != 1.0:
            self._log.debug(
                "rodd.tts.speed=%s is configured but has no effect — "
                "ChatterBox API does not expose a speed parameter (DATA_FLOW.md §4.6.1)",
                self._config.speed,
            )

        return body

    def _map_http_error(self, exc: httpx.HTTPStatusError) -> None:
        """Map an httpx HTTP status error to the appropriate ChatterboxError subclass.

        Always raises — never returns normally.
        """
        status = exc.response.status_code
        try:
            detail = exc.response.text
        except Exception:
            detail = None
        if status in (401, 403):
            raise ChatterboxAuthError(
                f"ChatterBox returned HTTP {status} — authentication rejected. "
                f"Detail: {detail}"
            ) from exc
        raise ChatterboxApiError(
            f"ChatterBox returned HTTP {status}. Detail: {detail}",
            status_code=status,
            detail=detail,
        ) from exc

    async def open(self) -> None:
        """Initialise the httpx.AsyncClient and probe /health.

        Creates the HTTP session and verifies the ChatterBox endpoint is reachable
        before the ceremony begins. Raises on failure so Tunga can enter degraded mode.

        Raises:
            ChatterboxConnectionError: if the endpoint is unreachable.
            ChatterboxAuthError: if HTTP 401/403 is returned.
            ChatterboxTimeoutError: if the health probe exceeds the timeout.
        """
        self._client = httpx.AsyncClient(timeout=self._make_timeout())
        url = f"{self._config.endpoint.rstrip('/')}/health"
        self._log.debug("ChatterboxHttpClient: probing health at %s", url)
        try:
            response = await self._client.get(url)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            await self._client.aclose()
            self._client = None
            raise ChatterboxConnectionError(
                f"ChatterBox endpoint unreachable at {self._config.endpoint!r}. "
                f"Is the Pi running and on the Tailscale network? Detail: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            await self._client.aclose()
            self._client = None
            raise ChatterboxTimeoutError(
                f"ChatterBox health probe timed out at {self._config.endpoint!r} "
                f"after {self._config.request_timeout_seconds}s."
            ) from exc
        except httpx.HTTPStatusError as exc:
            await self._client.aclose()
            self._client = None
            self._map_http_error(exc)
        except Exception as exc:
            await self._client.aclose()
            self._client = None
            raise ChatterboxConnectionError(
                f"ChatterBox health probe failed with unexpected error: {exc}"
            ) from exc

        self._open = True
        self._log.debug(
            "ChatterboxHttpClient: open — endpoint=%s model=%s",
            self._config.endpoint,
            self._config.model,
        )

    async def health(self) -> dict:
        """Fetch /health from ChatterBox and return the parsed JSON body.

        Raises:
            ChatterboxConnectionError: on network failure.
            ChatterboxApiError: on non-200 HTTP status.
        """
        assert self._client is not None, "health() called before open()"
        url = f"{self._config.endpoint.rstrip('/')}/health"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as exc:
            raise ChatterboxConnectionError(
                f"ChatterBox unreachable at {self._config.endpoint!r}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ChatterboxTimeoutError(
                f"ChatterBox /health timed out: {exc}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._map_http_error(exc)

    async def list_models(self) -> list[dict]:
        """Fetch /v1/models from ChatterBox and return the list of model dicts.

        Raises:
            ChatterboxConnectionError: on network failure.
            ChatterboxApiError: on non-200 HTTP status.
        """
        assert self._client is not None, "list_models() called before open()"
        url = f"{self._config.endpoint.rstrip('/')}/v1/models"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            body = response.json()
            # ChatterBox returns {"object": "list", "data": [...]} per OpenAI compat format
            if isinstance(body, dict) and "data" in body:
                return body["data"]
            if isinstance(body, list):
                return body
            return [body]
        except httpx.ConnectError as exc:
            raise ChatterboxConnectionError(
                f"ChatterBox unreachable at {self._config.endpoint!r}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ChatterboxTimeoutError(
                f"ChatterBox /v1/models timed out: {exc}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._map_http_error(exc)

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

        Validates the text length, builds the request body from config + overrides,
        posts to the ChatterBox endpoint, validates the response Content-Type is
        audio/wav, and returns the raw WAV bytes.

        Args:
            text: Text to synthesise. Must be 1–4000 characters.
            (remaining args: per-call overrides; None = use config defaults)

        Returns:
            Raw WAV bytes (Content-Type: audio/wav).

        Raises:
            ValueError: text is empty or exceeds 4000 characters.
            ChatterboxConnectionError: endpoint not reachable.
            ChatterboxAuthError: HTTP 401/403.
            ChatterboxTimeoutError: request timed out.
            ChatterboxApiError: non-200 HTTP status or non-WAV response.
        """
        # Validate text bounds before hitting the wire
        if not text:
            raise ValueError("synthesize(): text must not be empty.")
        if len(text) > 4000:
            raise ValueError(
                f"synthesize(): text length {len(text)} exceeds the 4000-character limit. "
                "Tunga's chunker is responsible for splitting long responses."
            )

        assert self._client is not None, "synthesize() called before open()"

        body = self._build_request_body(
            text=text,
            model=model,
            voice=voice,
            language_id=language_id,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
        )

        url = f"{self._config.endpoint.rstrip('/')}/v1/audio/speech"
        self._log.debug(
            "ChatterboxHttpClient.synthesize: text_len=%d model=%s url=%s",
            len(text),
            body.get("model"),
            url,
        )

        t_start = time.monotonic()
        try:
            response = await self._client.post(url, json=body)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise ChatterboxConnectionError(
                f"ChatterBox unreachable at {self._config.endpoint!r}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ChatterboxTimeoutError(
                f"ChatterBox synthesis timed out after {self._config.request_timeout_seconds}s "
                f"for {len(text)}-char input."
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._map_http_error(exc)

        # Verify we got WAV back — guard against misconfigured endpoints returning JSON errors
        content_type = response.headers.get("content-type", "")
        if "audio/wav" not in content_type and "audio/wave" not in content_type:
            raise ChatterboxApiError(
                f"ChatterBox /v1/audio/speech returned unexpected Content-Type: {content_type!r}. "
                "Expected audio/wav. Check that the endpoint is a ChatterBox TTS server.",
                status_code=response.status_code,
                detail=content_type,
            )

        latency_ms = int((time.monotonic() - t_start) * 1000)
        wav_bytes = response.content
        self._log.debug(
            "ChatterboxHttpClient.synthesize: got %d WAV bytes in %dms",
            len(wav_bytes),
            latency_ms,
        )
        return wav_bytes

    async def close(self) -> None:
        """Close the httpx.AsyncClient session and release resources.

        Safe to call even if open() was never called or failed.
        After close(), this instance must not be reused.
        """
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception as exc:
                self._log.debug("ChatterboxHttpClient.close: error during aclose: %s", exc)
            finally:
                self._client = None
        self._open = False
        self._log.debug("ChatterboxHttpClient: closed")

    async def __aenter__(self) -> "ChatterboxHttpClient":
        """Open the client and return self for use as an async context manager."""
        await self.open()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Close the client unconditionally on context manager exit."""
        await self.close()
