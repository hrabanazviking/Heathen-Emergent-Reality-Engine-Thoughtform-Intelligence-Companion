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
        client = BrunhandHttpClient(config, logger)   # resolves token; raises AuthError if absent
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
            AuthError: if config.enabled is True and the env var named in
                       config.token_env is unset or empty. The operator must
                       set the env var before starting HERETIC.
        """
        raise NotImplementedError(
            "BrunhandHttpClient.__init__ — Forge implements in Wave 2. "
            "Steps: "
            "1. self._config = config. "
            "2. self._log = logger or logging.getLogger(__name__). "
            "3. self._session_id = str(uuid.uuid4()). "
            "4. token = os.environ.get(config.token_env, ''). "
            "5. If config.enabled and not token: raise BrunhandAuthError("
            "   f'Bearer token env var {config.token_env!r} is not set. '). "
            "   Log as WARNING, never include the token value in log. "
            "6. self._token = token (may be empty if not enabled; client is inert). "
            "7. scheme = 'https' if config.require_https else 'http'. "
            "8. self._base_url = f'{scheme}://{config.host}:{config.port}'. "
            "9. self._http: httpx.AsyncClient | None = None  "
            "   (built in open()). "
            "SECURITY: never include self._token in __repr__, __str__, or any log call."
        )

    async def open(self) -> None:
        """Open the httpx AsyncClient and probe /v1/brunhand/health.

        Must be called before any endpoint method. Typically called from
        SmidjaSense.open().

        Raises:
            BrunhandUnreachableError: if the health probe fails (connection refused,
                DNS failure, or non-200 response).
            BrunhandTimeoutError: if the health probe times out.
        """
        raise NotImplementedError(
            "BrunhandHttpClient.open — Forge implements in Wave 2. "
            "Steps: "
            "1. Build httpx.AsyncClient with: "
            "   headers={'Authorization': f'Bearer {self._token}'}, "
            "   timeout=httpx.Timeout(self._config.request_timeout_seconds), "
            "   base_url=self._base_url. "
            "2. self._http = client. "
            "3. response = await self.health(). "
            "4. If response does not indicate status='ok': "
            "   raise BrunhandUnreachableError with detail. "
            "Catch httpx.ConnectError -> BrunhandUnreachableError. "
            "Catch httpx.TimeoutException -> BrunhandTimeoutError."
        )

    async def close(self) -> None:
        """Close the httpx AsyncClient and release resources.

        Idempotent — safe to call multiple times. Called from SmidjaSense.close().
        """
        raise NotImplementedError(
            "BrunhandHttpClient.close — Forge implements in Wave 2. "
            "Body: if self._http: await self._http.aclose(); self._http = None."
        )

    async def health(self) -> dict:
        """GET /v1/brunhand/health — no auth required.

        Returns:
            dict with daemon_version, os_name, uptime_seconds, status keys.

        Raises:
            BrunhandUnreachableError: on connection failure.
            BrunhandTimeoutError: on timeout.
        """
        raise NotImplementedError(
            "BrunhandHttpClient.health — Forge implements in Wave 2. "
            "Body: response = await self._http.get('/v1/brunhand/health'); "
            "response.raise_for_status(); return response.json()."
        )

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
        raise NotImplementedError(
            "BrunhandHttpClient.capabilities — Forge implements in Wave 2. "
            "Body: response = await self._http.get('/v1/brunhand/capabilities'); "
            "_raise_for_auth(response); response.raise_for_status(); return response.json()."
        )

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
        raise NotImplementedError(
            "BrunhandHttpClient.screenshot — Forge implements in Wave 2. "
            "Steps: "
            "1. body = self._build_envelope({'region': region}). "
            "2. response = await self._http.post('/v1/brunhand/screenshot', json=body). "
            "3. _raise_for_auth(response). "
            "4. response.raise_for_status(). "
            "5. payload = response.json()['payload']. "
            "6. import base64; return base64.b64decode(payload['png_bytes_b64'])."
        )

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
        raise NotImplementedError(
            "BrunhandHttpClient.click — Forge implements in Wave 2. "
            "Body: body = self._build_envelope("
            "{'x': x, 'y': y, 'button': button, 'clicks': clicks, "
            "'modifiers': modifiers or []}); "
            "response = await self._http.post('/v1/brunhand/click', json=body); "
            "_raise_for_auth(response); response.raise_for_status(); "
            "return response.json()['payload']."
        )

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
        raise NotImplementedError(
            "BrunhandHttpClient.type_text — Forge implements in Wave 2. "
            "Body: body = self._build_envelope({'text': text, 'interval': interval}); "
            "response = await self._http.post('/v1/brunhand/type', json=body); "
            "_raise_for_auth(response); response.raise_for_status(); "
            "return response.json()['payload']."
        )

    async def hotkey(self, keys: list[str]) -> dict:
        """POST /v1/brunhand/hotkey — press key combination.

        Args:
            keys: List of PyAutoGUI key name strings. All pressed simultaneously.

        Returns:
            dict with keys (echoed list).

        Raises:
            BrunhandAuthError, BrunhandUnreachableError, BrunhandTimeoutError.
        """
        raise NotImplementedError(
            "BrunhandHttpClient.hotkey — Forge implements in Wave 2. "
            "Body: body = self._build_envelope({'keys': keys}); "
            "response = await self._http.post('/v1/brunhand/hotkey', json=body); "
            "_raise_for_auth(response); response.raise_for_status(); "
            "return response.json()['payload']."
        )

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
        raise NotImplementedError(
            "BrunhandHttpClient.vroid_open — Forge implements in Wave 2. "
            "Body: body = self._build_envelope("
            "{'project_path': project_path, "
            "'wait_timeout_seconds': wait_timeout_seconds}); "
            "response = await self._http.post("
            "'/v1/brunhand/vroid/open_project', json=body); "
            "_raise_for_auth(response); response.raise_for_status(); "
            "return response.json()['payload']."
        )

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
        raise NotImplementedError(
            "BrunhandHttpClient.vroid_export — Forge implements in Wave 2. "
            "Body: body = self._build_envelope("
            "{'output_path': output_path, 'overwrite': overwrite, "
            "'wait_timeout_seconds': wait_timeout_seconds}); "
            "response = await self._http.post("
            "'/v1/brunhand/vroid/export_vrm', json=body); "
            "_raise_for_auth(response); response.raise_for_status(); "
            "return response.json()['payload']."
        )

    # -----------------------------------------------------------------------
    # Private helpers — Forge implements bodies
    # -----------------------------------------------------------------------

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
        raise NotImplementedError(
            "BrunhandHttpClient._build_envelope — Forge implements in Wave 2. "
            "Body: return { "
            "'request_id': str(uuid.uuid4()), "
            "'session_id': self._session_id, "
            "'agent_id': self._config.host_name, "
            "**primitive_params "
            "}."
        )


def _raise_for_auth(response: "httpx.Response") -> None:
    """Raise BrunhandAuthError if the response is HTTP 401.

    Forge calls this immediately after every authenticated endpoint response,
    before calling response.raise_for_status(). This produces a typed error
    rather than an httpx.HTTPStatusError for auth failures.

    Also raises BrunhandSessionLockedError for HTTP 423.

    Args:
        response: The httpx response object.

    Raises:
        BrunhandAuthError: if status code is 401.
        BrunhandSessionLockedError: if status code is 423.
    """
    raise NotImplementedError(
        "_raise_for_auth — Forge implements in Wave 2. "
        "Body: "
        "if response.status_code == 401: raise BrunhandAuthError('Bearer token rejected'). "
        "if response.status_code == 423: raise BrunhandSessionLockedError("
        "'Daemon has an active session from another connection (HTTP 423)')."
    )
