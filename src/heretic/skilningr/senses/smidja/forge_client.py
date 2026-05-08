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

# Hint injected into ForgeTimeoutError so the agent knows what to tell the operator
_TIMEOUT_HINT = (
    "Increase request_timeout_seconds in ForgeConfig for complex Loom specs. "
    "Standard builds take 60–120 s; high-poly or multi-view builds may exceed 120 s."
)


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

    All methods are async.

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

        # httpx.AsyncClient is built in open(); None until then
        self._http: "httpx.AsyncClient | None" = None

        # Track whether open() has been called and succeeded
        self._is_open: bool = False

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
        """
        # Build headers — only inject Authorization when a token is present
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=httpx.Timeout(float(self._config.request_timeout_seconds)),
        )

        # Probe /v1/health — raises on failure so callers know immediately
        try:
            health = await self.health()
        except (ForgeUnreachableError, ForgeTimeoutError):
            raise
        except Exception as exc:
            raise ForgeUnreachableError(
                f"Health probe failed for Straumur at {self._base_url}: {exc}"
            ) from exc

        status = health.get("status", "")
        if status != "ok":
            raise ForgeUnreachableError(
                f"Straumur at {self._base_url} returned health status {status!r} "
                f"(expected 'ok')."
            )

        self._is_open = True
        self._log.info(
            "Straumur (Forge) reachable at %s — version %s",
            self._base_url,
            health.get("version", "unknown"),
        )

    async def close(self) -> None:
        """Close the httpx AsyncClient and release resources.

        Idempotent — safe to call multiple times. Called from SmidjaSense.close().
        """
        self._is_open = False
        if self._http is not None:
            try:
                await self._http.aclose()
            except Exception as exc:
                self._log.warning("Error while closing Forge httpx client: %s", exc)
            finally:
                self._http = None

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _assert_open(self) -> None:
        """Raise ForgeUnreachableError if the client has not been opened."""
        if self._http is None:
            raise ForgeUnreachableError(
                "ForgeHttpClient is not open — call open() before making requests."
            )

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        """Perform a GET request with unified error mapping.

        Args:
            path: URL path relative to base_url (e.g. "/v1/health").
            params: Optional query parameters dict.

        Returns:
            Parsed JSON response (dict or list depending on endpoint).

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
            ForgeValidationError: on HTTP 4xx.
            ForgeError: on HTTP 5xx.
        """
        assert self._http is not None  # _assert_open() already checked
        try:
            response = await self._http.get(path, params=params)
        except httpx.ConnectError as exc:
            raise ForgeUnreachableError(
                f"Cannot connect to Straumur at {self._base_url}{path}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ForgeTimeoutError(
                f"Request to Straumur timed out ({path}): {exc}. hint: {_TIMEOUT_HINT}"
            ) from exc
        except Exception as exc:
            raise ForgeUnreachableError(
                f"Unexpected error from Straumur GET {path}: {exc}"
            ) from exc
        return _handle_response(response, path)

    async def _post(self, path: str, body: dict) -> dict | list:
        """Perform a POST request with unified error mapping.

        Args:
            path: URL path relative to base_url.
            body: Request body as a Python dict (serialised to JSON automatically).

        Returns:
            Parsed JSON response.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
            ForgeValidationError: on HTTP 4xx.
            ForgeError: on HTTP 5xx.
        """
        assert self._http is not None
        try:
            response = await self._http.post(path, json=body)
        except httpx.ConnectError as exc:
            raise ForgeUnreachableError(
                f"Cannot connect to Straumur at {self._base_url}{path}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ForgeTimeoutError(
                f"Request to Straumur timed out ({path}): {exc}. hint: {_TIMEOUT_HINT}"
            ) from exc
        except Exception as exc:
            raise ForgeUnreachableError(
                f"Unexpected error from Straumur POST {path}: {exc}"
            ) from exc
        return _handle_response(response, path)

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
        """
        self._assert_open()
        result = await self._get("/v1/health")
        assert isinstance(result, dict)
        return result

    # ------------------------------------------------------------------
    # Tool endpoints
    # ------------------------------------------------------------------

    async def build_avatar(self, loom_spec: dict[str, Any]) -> dict:
        """POST /v1/avatars — build an avatar from a Loom spec dict.

        Request body (BuildRequestBody in api.py):
            {
                "spec": <loom_spec dict>,
                "output_dir": null,
                "render_views": null,
                "compliance_targets": null,
                "session_metadata": {}
            }

        Response shape (on success — HTTP 200):
            {
                "success": true,
                "request_id": "<uuid4>",
                "vrm_path": "<absolute path on Straumur host or null>",
                "render_paths": {"<view_name>": "<path>", ...},
                "compliance_passed": true | false | null,
                "session_id": "<uuid4>",
                "elapsed_seconds": 42.1,
                "errors": []
            }

        Args:
            loom_spec: Full Loom spec as a Python dict. Must include at minimum
                       "base_asset_id" (str).

        Returns:
            dict matching the response shape above.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout (default 120 s — builds are slow).
            ForgeValidationError: on HTTP 422 (server-side schema rejection).
        """
        self._assert_open()
        body: dict[str, Any] = {
            "spec": loom_spec,
            "output_dir": None,
            "render_views": None,
            "compliance_targets": None,
            "session_metadata": {},
        }
        result = await self._post("/v1/avatars", body)
        assert isinstance(result, dict)
        return result

    async def get_avatar(self, session_id: str) -> dict:
        """GET /v1/avatars/{session_id} — retrieve the Annáll session record for a build.

        IMPORTANT: The {id} in the path is the session_id from the POST /v1/avatars
        response (the Annáll session UUID), NOT an avatar asset ID.

        Response shape (HTTP 200):
            {
                "session_id": "<uuid4>",
                "agent_id": "rest_client",
                "bridge_type": "straumur",
                "started_at": "<ISO datetime or null>",
                "ended_at": "<ISO datetime or null>",
                "success": true | false,
                "summary": "<human-readable summary string>",
                "events": [...]
            }

        Args:
            session_id: The Annáll session UUID returned by build_avatar()
                        response["session_id"].

        Returns:
            dict matching the session record shape above.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
            ForgeValidationError: on HTTP 404 (session_id not found).
        """
        self._assert_open()
        result = await self._get(f"/v1/avatars/{session_id}")
        assert isinstance(result, dict)
        return result

    async def inspect_avatar(
        self,
        vrm_path: str,
        targets: list[str] | None = None,
    ) -> dict:
        """POST /v1/inspect — run Gate compliance check on a .vrm file.

        IMPORTANT: The request body is NOT an avatar_id. It is the SERVER-SIDE
        path to a .vrm file that Straumur can access. The path must:
            - End in .vrm (case-insensitive) — H-004 check
            - Be within Straumur's allow-listed directories

        Request body (InspectRequestBody in api.py):
            {
                "vrm_path": "<server-side path to .vrm>",
                "targets": ["vrchat", "vtuber"] | null
            }

        Args:
            vrm_path: Server-side path to the .vrm file.
            targets: Optional list of Gate target names to check against.
                     None = all configured targets.

        Returns:
            dict with passed, vrm_path, targets_checked, elapsed_seconds, results.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
            ForgeValidationError: on HTTP 400 (invalid path or extension).
        """
        self._assert_open()
        body: dict[str, Any] = {
            "vrm_path": vrm_path,
            "targets": targets if targets is not None else None,
        }
        result = await self._post("/v1/inspect", body)
        assert isinstance(result, dict)
        return result

    async def list_assets(
        self,
        asset_type: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        """GET /v1/assets — list available Hoard assets.

        Optional query parameters:
            asset_type: str | None — filter by asset type
            tag: str | None — filter by tag

        Returns:
            List of asset dicts. Empty list if no matches.

        Raises:
            ForgeUnreachableError: on connection failure.
            ForgeTimeoutError: on timeout.
        """
        self._assert_open()
        params: dict[str, str] = {}
        if asset_type is not None:
            params["asset_type"] = asset_type
        if tag is not None:
            params["tag"] = tag
        result = await self._get("/v1/assets", params=params or None)
        # Straumur returns a list for /v1/assets
        if isinstance(result, list):
            return result
        # Graceful degradation: if the server wraps it, try to unwrap
        if isinstance(result, dict):
            return result.get("assets", [result])
        return []


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _handle_response(response: "httpx.Response", path: str) -> dict | list:
    """Parse and validate an httpx response; raise typed ForgeError on failure.

    Error mapping per Cartographer §4.11.9:
        - ConnectError → ForgeUnreachableError (raised before we reach here)
        - TimeoutException → ForgeTimeoutError (raised before we reach here)
        - HTTP 4xx → ForgeValidationError
        - HTTP 5xx → ForgeError("render_failed")
        - HTTP 200 → return parsed JSON

    Args:
        response: The httpx.Response to evaluate.
        path: The request path — included in error messages for diagnostics.

    Returns:
        Parsed JSON body (dict or list).

    Raises:
        ForgeValidationError: on HTTP 4xx.
        ForgeError: on HTTP 5xx.
    """
    if response.is_success:
        try:
            return response.json()
        except Exception as exc:
            raise ForgeError(
                f"Straumur returned non-JSON body from {path}: {exc}"
            ) from exc

    # Try to extract a useful error detail from the response body
    detail = ""
    try:
        body = response.json()
        # FastAPI returns {"detail": "<str>"} or {"detail": [{...}]}
        raw_detail = body.get("detail", "") if isinstance(body, dict) else ""
        detail = str(raw_detail)[:500]  # guard against huge payloads
    except Exception:
        detail = response.text[:500]

    if 400 <= response.status_code < 500:
        raise ForgeValidationError(
            f"Straumur rejected request to {path} (HTTP {response.status_code}): {detail}"
        )

    # HTTP 5xx
    raise ForgeError(
        f"Straumur render_failed — {path} returned HTTP {response.status_code}: {detail}"
    )
