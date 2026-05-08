"""
ForgeHttpClient — httpx-based async HTTP client for Seidr-Smidja Straumur REST bridge.

This client wraps Seidr-Smidja's Straumur REST API (the headless Blender pipeline).
It is the second half of the Smiðja sense, parallel to BrunhandHttpClient (Brúarhönd).
Both halves live under the same sense but are fully independent: separate endpoints,
separate auth profiles, separate timeout profiles, separate lifecycle.

ENDPOINT MAP (from src/seidr_smidja/bridges/straumur/api.py — verified 2026-05-08):
    GET  /v1/health                    — liveness probe; no auth; returns {"status":"ok","version":"0.1.0"}
    POST /v1/avatars                   — build avatar from Loom spec; returns build result
    GET  /v1/avatars/{session_id}      — retrieve full Annáll session record for a prior build
    POST /v1/inspect                   — standalone Gate compliance check on a .vrm file
    GET  /v1/assets                    — list Hoard assets (optional query: asset_type, tag)

AUTH MODEL:
    Straumur does NOT require authentication on localhost (H-005 design in api.py).
    token_env in ForgeConfig is OPTIONAL (default None). When None, no Authorization
    header is sent. When set, ForgeHttpClient injects Bearer <token> — for operators
    who expose Straumur beyond localhost via allow_remote_bind.

TIMEOUT PROFILE:
    Default request_timeout_seconds = 120 (ForgeConfig default). Blender render passes
    take 60–120 s; complex multi-view builds may need 180–300 s. The per-call timeout
    is the ForgeConfig value; there is no per-method override in this client — callers
    set the config value before opening.

API DISCREPANCIES vs TASK §4 (documented for the record):
    1. Health path is /v1/health (NOT /health — lives under the /v1/ prefix).
    2. GET /v1/avatars/{id} returns the full Annáll session record (session_id,
       agent_id, bridge_type, started_at, ended_at, success, summary, events) —
       NOT simple "avatar metadata". The identifier is session_id (uuid4) from
       the POST /v1/avatars response field "session_id".
    3. POST /v1/inspect takes {"vrm_path": str, "targets": list[str] | None} —
       NOT an avatar_id. The vrm_path must be a .vrm file within Straumur's
       allow-listed directories (output/ or data/hoard/bases/ by default).
    4. Straumur has NO bearer-token auth layer at the HTTP level (localhost H-005).
    5. Default port confirmed: 8765 (matches TASK §4 and api.py __main__).

All methods raise NotImplementedError stubs. Forge implements in Wave 2.

Ref: src/seidr_smidja/bridges/straumur/api.py (AUTHORITATIVE endpoint contracts)
     src/heretic/skilningr/senses/smidja/INTERFACE.md §Forge dispatch
     src/heretic/skilningr/config_model.ForgeConfig
"""

from __future__ import annotations

import logging
import os
from typing import Any

from heretic.skilningr.config_model import ForgeConfig
from heretic.skilningr.senses.smidja.errors import (
    ForgeError,
    ForgeTimeoutError,
    ForgeUnreachableError,
    ForgeValidationError,
)

try:
    import httpx
except ImportError as _httpx_missing:
    raise ImportError(
        "httpx is required for heretic.skilningr.senses.smidja.forge_client. "
        "It is declared as a core dependency in pyproject.toml. "
        "Run: pip install heretic"
    ) from _httpx_missing

logger = logging.getLogger(__name__)


class ForgeHttpClient:
    """Async HTTP client for the Seidr-Smidja Straumur REST bridge.

    One instance per ForgeConfig. Manages optional bearer-token auth (Straumur
    does not require auth on localhost — see AUTH MODEL in module docstring),
    HTTP error mapping, and timeout enforcement.

    Lifecycle:
        client = ForgeHttpClient(config, logger)   # resolves optional token
        await client.open()                         # probes /v1/health
        result = await client.build_avatar(spec)    # ... call methods ...
        await client.close()                        # release httpx client

    All methods are async. Methods raise NotImplementedError stubs — Forge implements.

    AUTH INVARIANT:
        If config.token_env is set, the token is resolved from os.environ ONCE at
        __init__ time and stored in self._token. It is NEVER logged, repr'd, or echoed.
        If config.token_env is None, self._token is None and no Authorization header
        is sent — matching Straumur's localhost-only H-005 default.
    """

    def __init__(
        self,
        config: ForgeConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise the client and optionally resolve the bearer token.

        Args:
            config: ForgeConfig with endpoint, token_env, timeout, etc.
            logger: Optional logger. If None, uses module-level logger.

        Notes:
            Unlike BrunhandHttpClient, this does NOT raise on missing token —
            because Straumur auth is optional. The token is resolved only when
            config.token_env is set; otherwise self._token is None.
        """
        self._config = config
        self._log = logger if logger is not None else logging.getLogger(__name__)

        # Resolve optional bearer token from environment — NEVER log the value
        if config.token_env is not None:
            self._token: str | None = os.environ.get(config.token_env) or None
        else:
            self._token = None

        # Base URL comes from config — never an absolute filesystem path
        self._base_url: str = config.endpoint.rstrip("/")

        # httpx.AsyncClient is built lazily in open()
        self._http: "httpx.AsyncClient | None" = None

    def __repr__(self) -> str:
        """Safe repr — NEVER includes the token value."""
        return (
            f"ForgeHttpClient("
            f"endpoint={self._base_url!r}, "
            f"enabled={self._config.enabled}, "
            f"token_env={self._config.token_env!r})"
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def open(self) -> None:
        """Open the httpx AsyncClient and probe /v1/health.

        Must be called before any endpoint method. Typically called from
        SmidjaSense.open() when ForgeConfig.enabled is True.

        Raises:
            ForgeUnreachableError: if the health probe fails (connection refused,
                DNS failure, or non-200 response).
            ForgeTimeoutError: if the health probe times out.

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.open() — Forge implements in v0.6.1 Wave 2. "
            "Expected behaviour: build httpx.AsyncClient, probe GET /v1/health, "
            "raise ForgeUnreachableError on failure."
        )

    async def close(self) -> None:
        """Close the httpx AsyncClient and release resources.

        Idempotent — safe to call multiple times. Called from SmidjaSense.close().

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.close() — Forge implements in v0.6.1 Wave 2. "
            "Expected behaviour: aclose() the httpx client; set self._http = None."
        )

    # ------------------------------------------------------------------
    # Utility endpoints
    # ------------------------------------------------------------------

    async def health(self) -> dict:
        """GET /v1/health — liveness probe; no auth required.

        Straumur response shape:
            {"status": "ok", "version": "0.1.0"}

        Returns:
            dict with at minimum "status" and "version" keys.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.health() — Forge implements in v0.6.1 Wave 2. "
            "Path: GET /v1/health. No auth. Returns JSON with status + version."
        )

    # ------------------------------------------------------------------
    # Tool endpoints
    # ------------------------------------------------------------------

    async def build_avatar(self, loom_spec: dict[str, Any]) -> dict:
        """POST /v1/avatars — build an avatar from a Loom spec dict.

        Request body (BuildRequestBody in api.py):
            {
                "spec": <loom_spec dict>,    -- the full Loom spec JSON
                "output_dir": null,          -- null = Straumur default output/
                "render_views": null,        -- null = no render; list of view names for renders
                "compliance_targets": null,  -- null = default Gate targets
                "session_metadata": {}       -- arbitrary agent-side metadata
            }

        Response shape (on success — HTTP 200):
            {
                "success": true,
                "request_id": "<uuid4>",
                "vrm_path": "<absolute path on Straumur host or null>",
                "render_paths": {"<view_name>": "<path>", ...},
                "compliance_passed": true | false | null,
                "session_id": "<uuid4>",           -- use this for get_avatar()
                "elapsed_seconds": 42.1,
                "errors": []                       -- list of {stage, message} on failure
            }

        Response shape (on failure — HTTP 422):
            Same shape, success=false, errors=[{stage, message}, ...]

        NOTE: The session_id in the response is the Annáll session identifier.
        Pass it to get_avatar(session_id) to retrieve the full session record.

        Args:
            loom_spec: Full Loom spec as a Python dict. Must include at minimum
                       "base_asset_id" (str). Other fields per Loom domain schema.

        Returns:
            dict matching the response shape above.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout (default 120 s — builds are slow).
            ForgeValidationError: on HTTP 422 (server-side schema rejection).

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.build_avatar() — Forge implements in v0.6.1 Wave 2. "
            "Path: POST /v1/avatars. Body: BuildRequestBody. Returns build result dict."
        )

    async def get_avatar(self, session_id: str) -> dict:
        """GET /v1/avatars/{session_id} — retrieve the Annáll session record for a build.

        IMPORTANT: The {id} in the path is the session_id from the POST /v1/avatars
        response (the Annáll session UUID), NOT an avatar asset ID. This retrieves
        the full audit/event record for a prior build session.

        Response shape (HTTP 200):
            {
                "session_id": "<uuid4>",
                "agent_id": "rest_client",
                "bridge_type": "straumur",
                "started_at": "<ISO datetime or null>",
                "ended_at": "<ISO datetime or null>",
                "success": true | false,
                "summary": "<human-readable summary string>",
                "events": [
                    {
                        "event_type": "<str>",
                        "severity": "<str>",
                        "payload": {...},
                        "timestamp": "<ISO datetime>"
                    },
                    ...
                ]
            }

        Raises HTTP 404 (via HTTPException) if the session_id is not found in Annáll.

        Args:
            session_id: The Annáll session UUID returned by build_avatar() response["session_id"].

        Returns:
            dict matching the session record shape above.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
            ForgeValidationError: on HTTP 404 (session_id not found).

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.get_avatar() — Forge implements in v0.6.1 Wave 2. "
            "Path: GET /v1/avatars/{session_id}. Returns Annáll session record dict."
        )

    async def inspect_avatar(self, vrm_path: str, targets: list[str] | None = None) -> dict:
        """POST /v1/inspect — run Gate compliance check on a .vrm file.

        IMPORTANT: The request body is NOT an avatar_id. It is the SERVER-SIDE
        path to a .vrm file that Straumur can access. The path must:
            - End in .vrm (case-insensitive) — H-004 check
            - Be within Straumur's allow-listed directories:
                  <project_root>/output/
                  <project_root>/data/hoard/bases/
              (or operator-configured straumur.inspect_roots in seidr-smidja config)
        Paths outside the allow-list receive HTTP 400 "vrm_path_not_allowed".

        Request body (InspectRequestBody in api.py):
            {
                "vrm_path": "<server-side absolute or relative path to .vrm>",
                "targets": ["vrchat", "vtuber"] | null   -- null = all targets
            }

        Response shape (HTTP 200):
            {
                "passed": true | false,
                "vrm_path": "<path echoed>",
                "targets_checked": ["vrchat", ...],
                "elapsed_seconds": 1.2,
                "results": {
                    "<target_name>": {
                        "passed": true | false,
                        "violations": [
                            {
                                "rule_id": "<str>",
                                "severity": "error" | "warning" | "info",
                                "description": "<human-readable>"
                            },
                            ...
                        ]
                    },
                    ...
                }
            }

        Args:
            vrm_path: Server-side path to the .vrm file. Must be within
                      Straumur's allow-listed output or hoard directories.
            targets: Optional list of Gate target names to check against.
                     None = all configured targets.

        Returns:
            dict matching the compliance report shape above.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
            ForgeValidationError: on HTTP 400 (invalid path or extension).

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.inspect_avatar() — Forge implements in v0.6.1 Wave 2. "
            "Path: POST /v1/inspect. Body: InspectRequestBody. Returns Gate report dict."
        )

    async def list_assets(
        self,
        asset_type: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        """GET /v1/assets — list available Hoard assets.

        Optional query parameters (passed as URL query string):
            asset_type: str | None — filter by asset type
            tag: str | None — filter by tag

        Response shape (HTTP 200) — list of asset objects:
            [
                {
                    "asset_id": "<str>",
                    "display_name": "<str>",
                    "asset_type": "<str>",
                    "tags": ["<str>", ...],
                    "vrm_version": "<str>",
                    "cached": true | false
                },
                ...
            ]

        Args:
            asset_type: Optional asset type filter string.
            tag: Optional tag filter string. Straumur accepts only one tag per request.

        Returns:
            List of asset dicts matching the shape above. Empty list if no matches.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.

        Forge implements.
        """
        raise NotImplementedError(
            "ForgeHttpClient.list_assets() — Forge implements in v0.6.1 Wave 2. "
            "Path: GET /v1/assets. Optional query: asset_type, tag. Returns list of asset dicts."
        )
