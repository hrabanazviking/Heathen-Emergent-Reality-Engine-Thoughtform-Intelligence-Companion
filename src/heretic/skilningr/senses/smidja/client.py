"""
BrunhandHttpClient — httpx-based async HTTP client for the Brúarhönd daemon.

This client wraps Seidr-Smidja's Horfunarþjónn (Watching-Daemon) HTTP API.
It sends authenticated requests to the daemon's /v1/brunhand/* endpoints and
returns structured Python values.

AUTH INVARIANT (NEVER BREAK):
    The bearer token is resolved from the environment variable named in
    config.token_env ONCE at __init__ time. It is stored in self._token
    and injected via httpx's headers={} at client construction — it is
    NEVER logged, repr'd, or echoed in any error message, response, or
    audit event. Use '[REDACTED]' if a log line needs to reference the auth
    header value.

REQUEST ENVELOPE INVARIANT:
    Every POST to an authenticated endpoint must include:
        request_id  (uuid4 string — generated per call)
        session_id  (set at open() time; persisted across calls in the same session)
        agent_id    (set at init time from config.host_name)
    These are generated automatically by _build_envelope(). The agent tool
    parameters do NOT need to include them.

ENDPOINT MAP (from Seidr-Smidja daemon INTERFACE.md — verified 2026-05-08):
    GET  /v1/brunhand/health                  — no auth; liveness probe
    GET  /v1/brunhand/capabilities            — Bearer; platform caps manifest
    POST /v1/brunhand/screenshot              — Bearer; capture PNG
    POST /v1/brunhand/click                   — Bearer; mouse click
    POST /v1/brunhand/type                    — Bearer; type text
    POST /v1/brunhand/hotkey                  — Bearer; key combination
    POST /v1/brunhand/vroid/open_project      — Bearer; open .vroid file
    POST /v1/brunhand/vroid/export_vrm        — Bearer; export .vrm file

    NOTE: TASK §4 listed /vroid-open and /vroid-export as flat paths.
    The ACTUAL paths (from daemon INTERFACE.md) are:
        /v1/brunhand/vroid/open_project   (NOT /vroid-open)
        /v1/brunhand/vroid/export_vrm     (NOT /vroid-export)
    This client uses the ACTUAL paths. See tools.py module docstring for full
    discrepancy list.

Ref: C:/Users/volma/runa/Seidr-Smidja/src/seidr_smidja/brunhand/daemon/INTERFACE.md
     heretic.skilningr.config_model.SmidjaConfig
     docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from typing import Any

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.errors import (
    BrunhandAuthError,
    BrunhandSessionLockedError,
    BrunhandTimeoutError,
    BrunhandUnreachableError,
)

try:
    import httpx
except ImportError as _httpx_missing:
    raise ImportError(
        "httpx is required for heretic.skilningr.senses.smidja.client. "
        "It is declared as a core dependency in pyproject.toml. "
        "Run: pip install heretic"
    ) from _httpx_missing

logger = logging.getLogger(__name__)


class BrunhandHttpClient:
    """Async HTTP client for the Brúarhönd daemon (Horfunarþjónn).

    One instance per configured Brúarhönd host. Manages bearer-token auth,
    per-request envelope generation, HTTP error mapping, and timeout enforcement.

    Lifecycle:
        client = BrunhandHttpClient(config, logger)   # resolves token; raises BrunhandAuthError if absent
        await client.open()                           # probes /health; raises on failure
        result = await client.screenshot()            # ... call methods ...
        await client.close()                          # release httpx client

    All methods are async. Call them from an async context (e.g. asyncio.run or
    pytest-asyncio test).
    """

    def __init__(
        self,
        config: SmidjaConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise the client and resolve the bearer token from the environment.

        The token is resolved once here. It is stored in self._token (private)
        and used to build the Authorization header. It is never logged.

        Args:
            config: SmidjaConfig with host, port, token_env, timeouts, etc.
            logger: Optional logger instance. If None, uses module-level logger.

        Raises:
            BrunhandAuthError: if config.enabled is True and the env var named in
                               config.token_env is unset or empty. The operator must
                               set the env var before starting HERETIC.
        """
        self._config = config
        self._log = logger if logger is not None else logging.getLogger(__name__)
        self._session_id: str = str(uuid.uuid4())
        self._agent_id: str = config.host_name

        # Resolve token from environment — NEVER include value in any log line
        token = os.environ.get(config.token_env, "")
        if config.enabled and not token:
            raise BrunhandAuthError(
                f"Bearer token environment variable {config.token_env!r} is not set "
                f"or is empty. Set {config.token_env}=<your_token> in the environment "
                f"before starting HERETIC with skilningr.smidja.enabled=true. "
                f"See docs/architecture/LAYER_INTERFACES.md §L5 Skilningr for setup."
            )
        # Store the token value (may be empty string if disabled — client is inert)
        self._token: str = token

        # Build the base URL from config — never an absolute filesystem path
        scheme = "https" if config.require_https else "http"
        self._base_url: str = f"{scheme}://{config.host}:{config.port}"

        # httpx.AsyncClient is built lazily in open() so tests can construct without opening
        self._http: httpx.AsyncClient | None = None

    def __repr__(self) -> str:
        """Safe repr — NEVER includes the token value."""
        return (
            f"BrunhandHttpClient("
            f"host={self._config.host!r}, "
            f"port={self._config.port}, "
            f"enabled={self._config.enabled}, "
            f"session_id={self._session_id!r})"
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def open(self) -> None:
        """Open the httpx AsyncClient and probe /v1/brunhand/health.

        Must be called before any endpoint method. Typically called from
        SmidjaSense.open().

        Raises:
            BrunhandUnreachableError: if the health probe fails (connection refused,
                DNS failure, or non-200 response).
            BrunhandTimeoutError: if the health probe times out.
        """
        # Build httpx.AsyncClient with Authorization header injected once —
        # the header is set here and never logged.
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=httpx.Timeout(float(self._config.request_timeout_seconds)),
        )
        # Probe health endpoint — raises on failure so callers know immediately
        try:
            health = await self.health()
        except BrunhandUnreachableError:
            raise
        except BrunhandTimeoutError:
            raise
        except Exception as exc:
            raise BrunhandUnreachableError(
                f"Health probe failed for Brúarhönd at {self._config.host}:{self._config.port}: {exc}"
            ) from exc

        status = health.get("status", "")
        if status != "ok":
            raise BrunhandUnreachableError(
                f"Brúarhönd daemon at {self._config.host}:{self._config.port} "
                f"returned health status {status!r} (expected 'ok')."
            )
        self._log.info(
            "Brúarhönd daemon reachable at %s:%s",
            self._config.host,
            self._config.port,
        )

    async def close(self) -> None:
        """Close the httpx AsyncClient and release resources.

        Idempotent — safe to call multiple times. Called from SmidjaSense.close().
        """
        if self._http is not None:
            try:
                await self._http.aclose()
            except Exception as exc:
                self._log.warning("Error while closing Brúarhönd httpx client: %s", exc)
            finally:
                self._http = None

    # ------------------------------------------------------------------
    # Utility endpoints
    # ------------------------------------------------------------------

    async def health(self) -> dict:
        """GET /v1/brunhand/health — no auth required.

        Returns:
            dict with daemon_version, os_name, uptime_seconds, status keys.

        Raises:
            BrunhandUnreachableError: on connection failure.
            BrunhandTimeoutError: on timeout.
        """
        if self._http is None:
            raise BrunhandUnreachableError(
                "BrunhandHttpClient is not open — call open() first."
            )
        try:
            response = await self._http.get("/v1/brunhand/health")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as exc:
            raise BrunhandUnreachableError(
                f"Cannot reach Brúarhönd daemon at {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise BrunhandTimeoutError(
                f"Brúarhönd health probe timed out after "
                f"{self._config.request_timeout_seconds}s: {exc}"
            ) from exc

    async def capabilities(self) -> dict:
        """GET /v1/brunhand/capabilities — Bearer auth required.

        Returns:
            dict with daemon_version, os_name, screen_geometry, primitives, probed_at.
            See daemon INTERFACE.md §capabilities for full schema.

        Raises:
            BrunhandAuthError: on HTTP 401.
            BrunhandUnreachableError: on connection failure.
            BrunhandTimeoutError: on timeout.
        """
        if self._http is None:
            raise BrunhandUnreachableError(
                "BrunhandHttpClient is not open — call open() first."
            )
        try:
            response = await self._http.get("/v1/brunhand/capabilities")
            _raise_for_auth(response)
            response.raise_for_status()
            return response.json()
        except (BrunhandAuthError, BrunhandSessionLockedError):
            raise
        except httpx.ConnectError as exc:
            raise BrunhandUnreachableError(
                f"Cannot reach Brúarhönd daemon: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise BrunhandTimeoutError(
                f"Brúarhönd capabilities request timed out: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Tool endpoints (Priority 2 — per-endpoint typed methods)
    # ------------------------------------------------------------------

    async def screenshot(self, region: dict | None = None) -> bytes:
        """POST /v1/brunhand/screenshot — capture PNG bytes.

        The daemon returns the image as a base64-encoded string in the JSON response
        field 'png_bytes_b64'. This method decodes it and returns raw PNG bytes.

        The screenshot is NOT cached or stored. Callers (SmidjaSense) may pass
        it to the agent as a base64 data URL in the tool_result content, mirroring
        the format used by L3 Sjón (FrameEncoder). Per v0.6 privacy invariant:
        no screenshots are cached beyond what Sjón's ring buffer already does.

        Args:
            region: Optional dict with left/top/width/height keys (all int).
                    None = full primary monitor.

        Returns:
            Raw PNG bytes decoded from the daemon's base64 response.

        Raises:
            BrunhandAuthError: on HTTP 401.
            BrunhandUnreachableError: on connection failure.
            BrunhandTimeoutError: on timeout.
        """
        body = self._build_envelope({"region": region})
        return await self._post_for_png("/v1/brunhand/screenshot", body)

    async def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1,
        modifiers: list[str] | None = None,
    ) -> dict:
        """POST /v1/brunhand/click — mouse click at (x, y).

        Args:
            x: Screen X coordinate.
            y: Screen Y coordinate.
            button: "left" | "right" | "middle". Default "left".
            clicks: Number of clicks. Default 1.
            modifiers: List of held modifier key names. Default [].

        Returns:
            dict with x, y, button, clicks_delivered.

        Raises:
            BrunhandAuthError, BrunhandUnreachableError, BrunhandTimeoutError.
        """
        body = self._build_envelope({
            "x": x,
            "y": y,
            "button": button,
            "clicks": clicks,
            "modifiers": modifiers or [],
        })
        return await self._post_for_payload("/v1/brunhand/click", body)

    async def type_text(self, text: str, interval: float = 0.05) -> dict:
        """POST /v1/brunhand/type — type text into the focused field.

        NOTE: method name is type_text (not type) because 'type' is a Python builtin.
        The daemon endpoint path is /v1/brunhand/type (unchanged).
        The tool name exposed to the agent is smidja.type_text (per tools.py).

        Args:
            text: Text string to type. Unicode supported.
            interval: Seconds between keystrokes. Default 0.05.

        Returns:
            dict with characters_typed.

        Raises:
            BrunhandAuthError, BrunhandUnreachableError, BrunhandTimeoutError.
        """
        body = self._build_envelope({"text": text, "interval": interval})
        return await self._post_for_payload("/v1/brunhand/type", body)

    async def hotkey(self, keys: list[str]) -> dict:
        """POST /v1/brunhand/hotkey — press key combination.

        Args:
            keys: List of PyAutoGUI key name strings. All pressed simultaneously.

        Returns:
            dict with keys (echoed list).

        Raises:
            BrunhandAuthError, BrunhandUnreachableError, BrunhandTimeoutError.
        """
        body = self._build_envelope({"keys": keys})
        return await self._post_for_payload("/v1/brunhand/hotkey", body)

    async def vroid_open(
        self, project_path: str, wait_timeout_seconds: float = 60.0
    ) -> dict:
        """POST /v1/brunhand/vroid/open_project — open .vroid project in VRoid Studio.

        IMPORTANT: The correct path is /v1/brunhand/vroid/open_project.
        TASK §4 listed /vroid-open — this was incorrect per daemon INTERFACE.md.

        Args:
            project_path: Relative path to .vroid file on the daemon host.
                          Relative to daemon's brunhand.daemon.project_root.
            wait_timeout_seconds: Max seconds to wait for VRoid to load. Default 60.

        Returns:
            dict with opened_path, elapsed_seconds, steps_executed.

        Raises:
            BrunhandAuthError, BrunhandUnreachableError, BrunhandTimeoutError.
        """
        body = self._build_envelope({
            "project_path": project_path,
            "wait_timeout_seconds": wait_timeout_seconds,
        })
        return await self._post_for_payload("/v1/brunhand/vroid/open_project", body)

    async def vroid_export(
        self, output_path: str, overwrite: bool = True, wait_timeout_seconds: float = 120.0
    ) -> dict:
        """POST /v1/brunhand/vroid/export_vrm — export .vrm from VRoid Studio.

        IMPORTANT: The correct path is /v1/brunhand/vroid/export_vrm.
        TASK §4 listed /vroid-export — this was incorrect per daemon INTERFACE.md.

        Args:
            output_path: Relative output path on daemon host. Relative to
                         daemon's brunhand.daemon.export_root.
            overwrite: Confirm overwrite if output already exists. Default True.
            wait_timeout_seconds: Max seconds for export flow. Default 120.

        Returns:
            dict with exported_path, elapsed_seconds, steps_executed.

        Raises:
            BrunhandAuthError, BrunhandUnreachableError, BrunhandTimeoutError.
        """
        body = self._build_envelope({
            "output_path": output_path,
            "overwrite": overwrite,
            "wait_timeout_seconds": wait_timeout_seconds,
        })
        return await self._post_for_payload("/v1/brunhand/vroid/export_vrm", body)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_envelope(self, primitive_params: dict[str, Any]) -> dict[str, Any]:
        """Build the shared request envelope required by all authenticated endpoints.

        Every POST body must include request_id, session_id, agent_id alongside
        the primitive-specific fields. This method merges both into one dict.

        Per daemon INTERFACE.md §Shared Envelope:
            request_id  — uuid4, unique per request; echoed in response
            session_id  — persisted for the lifetime of this client's session
            agent_id    — set to config.host_name (logical agent label)

        Args:
            primitive_params: Dict of endpoint-specific fields (e.g. x, y, text).

        Returns:
            Full request body dict ready for json= kwarg in httpx POST.
        """
        return {
            "request_id": str(uuid.uuid4()),
            "session_id": self._session_id,
            "agent_id": self._agent_id,
            **primitive_params,
        }

    async def _post_for_payload(self, path: str, body: dict[str, Any]) -> dict:
        """POST to an authenticated endpoint and return response['payload'].

        Common implementation shared by click, type_text, hotkey, vroid_open,
        vroid_export. Handles error mapping for all standard HTTP failure modes.

        Args:
            path: API path (e.g. '/v1/brunhand/click').
            body: Full request body including envelope fields.

        Returns:
            Parsed response payload dict.

        Raises:
            BrunhandAuthError, BrunhandSessionLockedError,
            BrunhandUnreachableError, BrunhandTimeoutError.
        """
        if self._http is None:
            raise BrunhandUnreachableError(
                "BrunhandHttpClient is not open — call open() first."
            )
        try:
            response = await self._http.post(path, json=body)
            _raise_for_auth(response)
            _raise_for_server_error(response, path)
            response.raise_for_status()
            return response.json().get("payload", response.json())
        except (BrunhandAuthError, BrunhandSessionLockedError):
            raise
        except (BrunhandUnreachableError, BrunhandTimeoutError):
            raise
        except httpx.ConnectError as exc:
            raise BrunhandUnreachableError(
                f"Cannot reach Brúarhönd daemon at {path}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise BrunhandTimeoutError(
                f"Brúarhönd request to {path} timed out after "
                f"{self._config.request_timeout_seconds}s: {exc}"
            ) from exc
        except Exception as exc:
            # Catch JSONDecodeError and any httpx edge-case as an opaque dispatch error
            from heretic.skilningr.errors import ToolDispatchError
            raise ToolDispatchError(
                f"Malformed or unexpected response from Brúarhönd at {path}: {exc}"
            ) from exc

    async def _post_for_png(self, path: str, body: dict[str, Any]) -> bytes:
        """POST to the screenshot endpoint and return decoded PNG bytes.

        The daemon returns JSON with payload.png_bytes_b64 (base64-encoded PNG).
        This method decodes it into raw bytes for the caller.

        Args:
            path: API path (/v1/brunhand/screenshot).
            body: Full request body including envelope fields.

        Returns:
            Raw PNG bytes.

        Raises:
            BrunhandAuthError, BrunhandSessionLockedError,
            BrunhandUnreachableError, BrunhandTimeoutError.
        """
        if self._http is None:
            raise BrunhandUnreachableError(
                "BrunhandHttpClient is not open — call open() first."
            )
        try:
            response = await self._http.post(path, json=body)
            _raise_for_auth(response)
            _raise_for_server_error(response, path)
            response.raise_for_status()
            data = response.json()
            # Daemon response shape: {"payload": {"png_bytes_b64": "<base64>"}}
            png_b64: str = data["payload"]["png_bytes_b64"]
            return base64.b64decode(png_b64)
        except (BrunhandAuthError, BrunhandSessionLockedError):
            raise
        except (BrunhandUnreachableError, BrunhandTimeoutError):
            raise
        except httpx.ConnectError as exc:
            raise BrunhandUnreachableError(
                f"Cannot reach Brúarhönd daemon at {path}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise BrunhandTimeoutError(
                f"Brúarhönd screenshot request timed out after "
                f"{self._config.request_timeout_seconds}s: {exc}"
            ) from exc
        except Exception as exc:
            from heretic.skilningr.errors import ToolDispatchError
            raise ToolDispatchError(
                f"Malformed response from Brúarhönd screenshot: {exc}"
            ) from exc


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _raise_for_auth(response: "httpx.Response") -> None:
    """Raise BrunhandAuthError if the response is HTTP 401.

    Also raises BrunhandSessionLockedError for HTTP 423.

    Args:
        response: The httpx response object.

    Raises:
        BrunhandAuthError: if status code is 401.
        BrunhandSessionLockedError: if status code is 423.
    """
    if response.status_code == 401:
        raise BrunhandAuthError(
            "Bearer token rejected by Brúarhönd daemon (HTTP 401). "
            "Verify the token in the environment variable configured in "
            "SmidjaConfig.token_env matches the daemon's expected token. "
            "Authorization header value: [REDACTED]"
        )
    if response.status_code == 423:
        raise BrunhandSessionLockedError(
            "Brúarhönd daemon has an active session from another connection (HTTP 423). "
            "Only one concurrent session is permitted. Retry after the current session ends."
        )


def _raise_for_server_error(response: "httpx.Response", path: str) -> None:
    """Raise ToolDispatchError for HTTP 5xx responses with excerpted body.

    Args:
        response: The httpx response object.
        path: The endpoint path (for context in the error message).

    Raises:
        ToolDispatchError: if status code is 500-599.
    """
    if response.status_code >= 500:
        from heretic.skilningr.errors import ToolDispatchError
        # Excerpt body for diagnostics — never include auth tokens
        try:
            body_excerpt = response.text[:300]
        except Exception:
            body_excerpt = "<unreadable>"
        raise ToolDispatchError(
            f"Brúarhönd daemon returned server error HTTP {response.status_code} "
            f"for {path}. Body excerpt: {body_excerpt}"
        )
