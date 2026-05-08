# HERETIC — Audit: v0.6.1 Forge Dispatch

**Date:** 2026-05-08
**Auditor:** Sólrún Hvítmynd (Auditor role, Mythic Engineering)
**Scope:** Full audit of the v0.6.1 Forge Dispatch milestone. Commits audited:
`0349a60` (Cartographer — DATA_FLOW.md §4.11.7-9 + §16),
`24a93da` (Architect — forge_client.py scaffold + ForgeConfig + 3 tool schemas + dual-half SmidjaSense INTERFACE.md),
`ea57e40` (Forge — CAP-SALVAGE: ForgeHttpClient impl + SmidjaSense dual-half extension).
Branch: `development`.

**Context:** The Anthropic usage cap interrupted Forge mid-test-replacement. The 7
placeholder `NotImplementedError` tests were removed and the real implementation was
salvage-committed. Approximately 25 real httpx-mocked method-level tests that Forge would
have written are missing. The 27 schema/structure tests from the Architect wave still pass.
This audit therefore carries a **doubled responsibility**: standard contract verification
AND salvage triage (code-reading the unverified implementation as a substitute for
automated test coverage).

**Environment:** Windows 11 Home 10.0.22621, Python 3.10.11, Node.js 20.x, PowerShell.

**Commands run:**

```
python -m pytest tests/ -q                              → 770 passed, 2 skipped, 34 warnings
python -m pytest tests/test_forge_client.py tests/test_smidja_sense.py tests/test_smidja_tools.py -v --tb=short
                                                        → 59 passed, 2 skipped
cd frontend && npm test -- --run                        → 91 passed
cd frontend && npx tsc --noEmit                         → 0 errors
cd frontend && npm run build                            → OK (163.44 kB, 1.12s)
python -m heretic version && python -m heretic --help   → 0.1.0.dev0, all commands listed
python -c "from heretic.skilningr.errors import ForgeServerError"
                                                        → ImportError (confirms N-1)
python -c "..." (dispatch mock probe confirming TypeError→SENSE_INTERNAL_ERROR path)
grep -rn "ForgeServerError|ForgeAssetNotFound" src/ docs/ tests/
                                                        → 5 doc-only references; 0 in code
```

---

## Summary Verdict

**PASS WITH CONCERNS**

The v0.6.1 Forge Dispatch milestone delivers a working dual-half Smiðja sense: ForgeHttpClient
(httpx async, all five endpoints implemented), ForgeConfig with correct defaults, 3 new OpenAI
tool schemas, SmidjaSense extended for independent per-half lifecycle, tool routing by `forge_`
prefix, and heretic.example.yaml forge sub-block. All 770 Python tests pass. 91 frontend tests
pass. TypeScript strict mode: 0 errors. Vite build: clean.

**No blockers found.** The implementation is structurally sound. Every API path, request body,
response mapping, error hierarchy, and lifecycle invariant was verified by code reading against
`api.py` (authoritative). One notable documentation drift was found (ForgeServerError referenced
in DATA_FLOW and SYSTEM_OVERVIEW but absent from errors.py). One serious finding (S-1) is the
coverage gap left by the cap-salvage: ~25 method-level httpx-mocked tests are missing, leaving
`forge_client.py`'s method bodies unverified by any automated test. A second secondary finding
(N-2) is a stale test that passes for the wrong reason.

v0.6.1 is **releasable as a development milestone** with the concerns noted. It must not close
Wave 3 without the S-1 tests added. The N-1 doc drift should be resolved in Wave 3 cleanup.

| Severity  | Count | Items                                       |
|-----------|-------|---------------------------------------------|
| BLOCKER   | 0     | —                                           |
| SERIOUS   | 1     | S-1 (coverage gap — method bodies unverified by tests) |
| NOTABLE   | 1     | N-1 (ForgeServerError doc/code mismatch)    |
| NIT       | 1     | X-1 (stale test name + wrong-reason pass)   |
| VERIFIED  | 28    | A-1..A-5, B-1..B-5, C-1..C-6, D-1..D-4, E-1..E-5, F-1..F-3 |

---

## Responsibility A — Standard v0.6.1 Contract Verification

### Section A — API Path Correctness

**A-1: Health probe hits `/v1/health` (not `/health`).** VERIFIED.

`forge_client.py:301` — `await self._get("/v1/health")` inside `health()`. The module
docstring (lines 9-13) explicitly calls out the TASK §4 discrepancy: "Health path is
`/v1/health` (NOT `/health` — lives under the `/v1/` prefix)." Confirmed against
`api.py:188` — `@app.get("/v1/health")`. Match.

**A-2: `build_avatar` POSTs to `/v1/avatars`.** VERIFIED.

`forge_client.py:353` — `result = await self._post("/v1/avatars", body)`.
`api.py:192` — `@app.post("/v1/avatars")`. Match. Request body fields
(`spec`, `output_dir`, `render_views`, `compliance_targets`, `session_metadata`) match
`BuildRequestBody` (api.py:55-63) exactly.

**A-3: `get_avatar` GETs `/v1/avatars/{session_id}`.** VERIFIED.

`forge_client.py:388` — `result = await self._get(f"/v1/avatars/{session_id}")`.
`api.py:331` — `@app.get("/v1/avatars/{session_id}")`. Match. The docstring correctly
notes the `{id}` is the Annáll `session_id` (uuid4), NOT an asset id. This was a
documented TASK §4 discrepancy, handled correctly.

**A-4: `inspect_avatar` POSTs to `/v1/inspect` with `vrm_path` + `targets`.** VERIFIED.

`forge_client.py:424-429` — builds `{"vrm_path": vrm_path, "targets": targets}` and
calls `await self._post("/v1/inspect", body)`. `api.py:254` —
`@app.post("/v1/inspect")` with `InspectRequestBody(vrm_path: str, targets: list[str] | None)`.
Match. The docstring correctly notes the request is NOT an `avatar_id`.

**A-5: `list_assets` GETs `/v1/assets` with optional query params.** VERIFIED.

`forge_client.py:451-456` — calls `self._get("/v1/assets", params=params or None)` where
`params` is built from optional `asset_type` and `tag` kwargs. `api.py:302` —
`@app.get("/v1/assets")` with `asset_type: str | None = None, tag: str | None = None`.
Match. Query parameter names match exactly.

---

### Section B — Request Bodies

**B-1: `build_avatar` includes all five `BuildRequestBody` fields.** VERIFIED.

`forge_client.py:346-352` — dict contains `spec` (loom_spec), `output_dir: None`,
`render_views: None`, `compliance_targets: None`, `session_metadata: {}`. All five
fields from `BuildRequestBody` (api.py:55-63) are present with correct defaults.

**B-2: `inspect_avatar` correctly uses `vrm_path` key (not `avatar_id`).** VERIFIED.

`forge_client.py:424-427` — body key is `"vrm_path"`, matching `InspectRequestBody.vrm_path`.
`SmidjaSense._route_forge` (sense.py:579) maps tool param `args["avatar_id"]` → kwarg
`vrm_path=`. The mapping is explicit and documented in the INTERFACE.md §"IMPORTANT parameter
naming". No drift.

**B-3: `get_avatar` uses `session_id` in URL path, not query param.** VERIFIED.

`forge_client.py:388` — f-string path interpolation `f"/v1/avatars/{session_id}"`.
No query parameter leakage.

**B-4: `build_avatar` loom_spec is passed under the `"spec"` key.** VERIFIED.

`forge_client.py:346` — `"spec": loom_spec`. `api.py:57` — `spec: Any`. Match.

**B-5: Forge does NOT send a Brúarhönd envelope.** VERIFIED.

No call to `_build_envelope` or any `request_id`/`session_id`/`agent_id` injection in
`forge_client.py`. Correct per INTERFACE.md: "The Forge (Straumur) API does NOT use a
request envelope."

---

### Section C — Tool Schemas (OpenAI Spec Conformance)

**C-1: All 3 Forge tools have `"type": "function"` and a `"function"` block.** VERIFIED.

`tools.py:310`, `350`, `384` — each tool dict has `{"type": "function", "function": {...}}`.

**C-2: `smidja.forge_build_avatar` — `loom_spec` required, `additionalProperties: True`.** VERIFIED.

`tools.py:326-340` — `"required": ["loom_spec"]`, `"additionalProperties": True` on the
`loom_spec` object (correct — the schema is open for arbitrary Loom fields).
`"additionalProperties": False` on the outer parameters object. OpenAI-compliant.

**C-3: `smidja.forge_get_avatar` — `avatar_id` required, no extras.** VERIFIED.

`tools.py:363-379` — `"required": ["avatar_id"]`, `"additionalProperties": False`.
Description correctly documents it is the Annáll `session_id`.

**C-4: `smidja.forge_inspect_avatar` — `avatar_id` required; no `targets` in schema.** VERIFIED.

`tools.py:399-416` — `"required": ["avatar_id"]`, `"additionalProperties": False`.
No `targets` parameter is exposed in the schema — the agent cannot set targets. This is
a deliberate scope choice (targets default to None = all configured targets). Consistent
with `ForgeHttpClient.inspect_avatar(targets=None)`. Acceptable for v0.6.1.

**C-5: Tool names follow two-part `smidja.<action>` convention.** VERIFIED.

All three: `"smidja.forge_build_avatar"`, `"smidja.forge_get_avatar"`,
`"smidja.forge_inspect_avatar"`. `forge_` sub-prefix matches routing rule.

**C-6: 27 Architect schema tests pass.** VERIFIED.

`python -m pytest tests/test_smidja_tools.py -v` — 27 passed, 0 failed.

---

### Section D — Dual-Half SmidjaSense Lifecycle

**D-1: Both halves open independently; one failure does not affect the other.** VERIFIED.

`sense.py:195-254` — Brúarhönd and Forge blocks are separate `if` branches. Each has its own
`try/except` catching `SmidjaError`, `ForgeError`, `NotImplementedError`, and bare `Exception`.
Neither branch references the other's state. If Forge fails, `_brunhand_open` is unaffected.
If Brúarhönd fails, `_forge_open` is unaffected.

**D-2: Fault tolerance invariant — `open()` never raises to caller.** VERIFIED.

`sense.py:179` docstring: "NEVER raise to the caller." Every exception variant
(SmidjaError, ForgeError, NotImplementedError, Exception) is caught within the method body
with `_brunhand_open = False` / `_forge_open = False` as the degraded result.

**D-3: `close()` is idempotent for both halves.** VERIFIED.

`sense.py:263-281` — two `try/except/finally` blocks. `finally` always sets the open flag
to False. Calling `close()` twice sets the flag again to False — safe. `ForgeHttpClient.close()`
(forge_client.py:192-204) has its own idempotent `self._http is None` guard.

**D-4: `is_available` requires at least one enabled AND open half.** VERIFIED.

`sense.py:165-167` — `brunhand_available = self._config.enabled and self._brunhand_open`.
`forge_available = self._config.forge.enabled and self._forge_open`.
Return is `brunhand_available or forge_available`. Correct conjunction.

---

### Section E — Error Mapping

**E-1: `ConnectError` → `ForgeUnreachableError`.** VERIFIED.

`forge_client.py:237-239` (`_get`) and `forge_client.py:269-271` (`_post`) — both catch
`httpx.ConnectError` and raise `ForgeUnreachableError`. `open()` (lines 172-177) catches
the re-raise from `health()` and propagates. Correct.

**E-2: `TimeoutException` → `ForgeTimeoutError` with hint.** VERIFIED.

`forge_client.py:240-243` and `forge_client.py:272-275` — both catch
`httpx.TimeoutException` and raise `ForgeTimeoutError` with the `_TIMEOUT_HINT` string
(defined at line 72) embedded in the message. Hint text is informative.

**E-3: HTTP 4xx → `ForgeValidationError`.** VERIFIED.

`forge_client.py:509-512` (`_handle_response`) — `400 <= response.status_code < 500`
raises `ForgeValidationError`. The detail extraction tries `response.json()["detail"]`
first (FastAPI pattern), falls back to `response.text`. Capped at 500 chars to guard
against huge payloads.

**E-4: HTTP 5xx → `ForgeError` (base class).** VERIFIED.

`forge_client.py:514-517` — bare `raise ForgeError(...)`. This is the correct choice given
that `ForgeServerError` was planned in the Cartographer map but was never defined in code.
The base `ForgeError` is catchable everywhere `ForgeServerError` would have been caught.
See N-1 below for the doc drift.

**E-5: `ForgeError` is a subclass of `SmidjaError` and `SkilningrError`.** VERIFIED.

`errors.py:123-134` — `class ForgeError(SmidjaError)`. `SmidjaError` inherits `SkilningrError`.
`_smidja_error_code` in `sense.py:656-695` handles all Forge subclasses. The error code
mapping is complete: `ForgeUnreachableError → EXTERNAL_APP_UNAVAILABLE`,
`ForgeTimeoutError → SENSE_TIMEOUT`, `ForgeValidationError → INVALID_ARGUMENTS`,
base `ForgeError → SENSE_INTERNAL_ERROR` (falls through to final `return "SENSE_INTERNAL_ERROR"`).

---

### Section F — Auth + Token Invariants

**F-1: `token_env = None` does not raise at construction.** VERIFIED.

`forge_client.py:119-122` — `if config.token_env is not None: ... else: self._token = None`.
`ForgeConfig(token_env=None)` is the default. `test_forge_client_constructs_with_defaults`
passes.

**F-2: When `token_env` is None, no `Authorization` header is sent.** VERIFIED.

`forge_client.py:159-161` — `if self._token:` guards the header injection. `None` is falsy.

**F-3: Token value never appears in repr.** VERIFIED.

`forge_client.py:133-140` — `__repr__` outputs `token_env=` (the env var name), never the
token value. `test_forge_client_repr_does_not_include_token` passes.

---

### Section G — Cross-Platform and Config

**G-1: No absolute paths in `forge_client.py`.** VERIFIED.

No `os.path.join`, no `Path(...)` with hardcoded roots, no platform-specific separators.
All paths are URL paths (strings starting with `/v1/`). Base URL comes from `config.endpoint`.

**G-2: No auto-disk-writes.** VERIFIED.

`forge_client.py` contains no file I/O. The client transmits and receives JSON; it does not
write render artifacts — confirmed per TASK §4: "HERETIC just receives URLs/IDs; user fetches
from Seidr-Smidja directly."

**G-3: `heretic.example.yaml` forge sub-block present and correct.** VERIFIED.

`heretic.example.yaml:233-237` — `forge:` block under `smidja:` with all four fields:
`enabled: false`, `endpoint: http://127.0.0.1:8765`, `token_env: SEIDR_SMIDJA_FORGE_TOKEN`,
`request_timeout_seconds: 120`. Comments explain optional auth and Blender render latency.

**G-4: `ForgeConfig` defaults match documented values.** VERIFIED.

`config_model.py:83-107` — `enabled=False`, `endpoint="http://127.0.0.1:8765"`,
`token_env=None`, `request_timeout_seconds=120`. `test_forge_config_default_values` passes.

---

## Responsibility B — Salvage Triage

### S-1 (SERIOUS) — Coverage Gap: ~25 Method-Level Tests Missing

**Location:** `tests/test_forge_client.py` (currently 9 tests; 0 cover method bodies).

**Evidence:** `forge_client.py:146-463` contains the fully implemented methods `open`,
`close`, `health`, `build_avatar`, `get_avatar`, `inspect_avatar`, `list_assets`. None of
these are exercised by any automated test that uses httpx mocking. The only existing tests
verify config defaults, repr safety, and the error hierarchy. Two live-daemon tests are
`@pytest.mark.skip`. The 7 Wave 1 `NotImplementedError` tests were removed at salvage and
not replaced.

**Why serious:** Every invariant in Section A–G above was verified by this auditor's eye
reading the code. An eye-read is not a regression safety net. Any future edit to
`forge_client.py` — including a typo in a path string, a wrong key name in a request body,
or a broken error-mapping branch — will pass the test suite without detection.

**Required before v0.6.2 close-out:** Wave 3 must add the following test cases to
`tests/test_forge_client.py`:

```
# ForgeHttpClient lifecycle

test_forge_client_open_creates_async_client_and_sets_is_open
    → mock health() to return {"status": "ok", "version": "0.1.0"}
    → assert client._is_open is True after open()

test_forge_client_open_raises_unreachable_on_connect_error
    → mock httpx.AsyncClient.get to raise httpx.ConnectError
    → assert ForgeUnreachableError is raised from open()

test_forge_client_open_raises_unreachable_on_non_ok_health_status
    → mock health() to return {"status": "degraded"}
    → assert ForgeUnreachableError is raised

test_forge_client_open_raises_timeout_on_health_timeout
    → mock httpx.AsyncClient.get to raise httpx.TimeoutException
    → assert ForgeTimeoutError is raised from open()

test_forge_client_token_env_None_does_not_raise
    → ForgeConfig(token_env=None) → ForgeHttpClient(...) → no error
    → client._token is None

test_forge_client_token_env_set_includes_authorization_header
    → monkeypatch.setenv("MY_TOKEN_VAR", "secret")
    → ForgeConfig(token_env="MY_TOKEN_VAR") → ForgeHttpClient(...)
    → client._token == "secret"
    → open() → assert httpx.AsyncClient headers["Authorization"] == "Bearer secret"

test_forge_client_close_is_idempotent
    → open, close, close again → no error

# build_avatar

test_forge_client_build_avatar_posts_to_v1_avatars_with_loom_spec
    → mock httpx post to return {"success": True, "session_id": "abc", ...}
    → call build_avatar({"base_asset_id": "vroid_base_v1"})
    → assert request path == "/v1/avatars"
    → assert request body["spec"] == {"base_asset_id": "vroid_base_v1"}
    → assert result["session_id"] == "abc"

test_forge_client_build_avatar_timeout_raises_forge_timeout_with_hint
    → mock httpx post to raise httpx.TimeoutException
    → assert ForgeTimeoutError raised
    → assert _TIMEOUT_HINT in str(exc)

test_forge_client_build_avatar_422_raises_forge_validation_error
    → mock httpx post to return HTTP 422 with {"detail": "spec invalid"}
    → assert ForgeValidationError raised
    → assert "spec invalid" in str(exc)

test_forge_client_build_avatar_500_raises_forge_error
    → mock httpx post to return HTTP 500 with {"detail": "internal"}
    → assert ForgeError raised (not subclass — base class)

# get_avatar

test_forge_client_get_avatar_gets_v1_avatars_session_id
    → mock httpx get to return valid session record dict
    → call get_avatar("my-session-uuid")
    → assert request path == "/v1/avatars/my-session-uuid"
    → assert result["session_id"] == "my-session-uuid"

test_forge_client_get_avatar_404_raises_forge_validation_error
    → mock httpx get to return HTTP 404
    → assert ForgeValidationError raised

# inspect_avatar

test_forge_client_inspect_avatar_posts_with_vrm_path_and_targets
    → mock httpx post to return valid inspect response
    → call inspect_avatar("output/my.vrm", targets=["vrchat"])
    → assert request path == "/v1/inspect"
    → assert request body == {"vrm_path": "output/my.vrm", "targets": ["vrchat"]}

test_forge_client_inspect_avatar_targets_none_sends_null
    → call inspect_avatar("output/my.vrm", targets=None)
    → assert request body["targets"] is None

test_forge_client_inspect_avatar_400_raises_forge_validation_error
    → mock HTTP 400 (path outside allow-list)
    → assert ForgeValidationError raised

# list_assets

test_forge_client_list_assets_returns_list
    → mock httpx get to return [{...}, {...}]
    → assert list_assets() returns a Python list
    → assert request path == "/v1/assets" with no params

test_forge_client_list_assets_passes_asset_type_query_param
    → call list_assets(asset_type="base")
    → assert params["asset_type"] == "base"

test_forge_client_list_assets_handles_dict_wrapper_gracefully
    → mock httpx get to return {"assets": [{...}]}
    → assert list_assets() returns the list, not the wrapper

# _assert_open guard

test_forge_client_method_raises_unreachable_before_open
    → ForgeHttpClient(cfg) without calling open()
    → call health() / build_avatar() / etc.
    → assert ForgeUnreachableError raised ("not open")

# SmidjaSense dual-half Forge routing (add to test_smidja_sense.py)

test_smidja_sense_forge_build_avatar_routes_to_forge_client
    → set sense._forge_open = True
    → mock forge_client.build_avatar to return {"success": True, "session_id": "x"}
    → dispatch smidja.forge_build_avatar with {"loom_spec": {...}}
    → assert forge_client.build_avatar called with correct loom_spec
    → assert result content contains "session_id"

test_smidja_sense_forge_get_avatar_maps_avatar_id_to_session_id
    → mock forge_client.get_avatar to return valid record
    → dispatch smidja.forge_get_avatar with {"avatar_id": "abc"}
    → assert forge_client.get_avatar called with session_id="abc"

test_smidja_sense_forge_inspect_avatar_maps_avatar_id_to_vrm_path
    → mock forge_client.inspect_avatar to return valid inspect result
    → dispatch smidja.forge_inspect_avatar with {"avatar_id": "output/x.vrm"}
    → assert forge_client.inspect_avatar called with vrm_path="output/x.vrm", targets=None

test_smidja_sense_forge_unreachable_error_returns_external_unavailable_code
    → mock forge_client.build_avatar to raise ForgeUnreachableError
    → dispatch smidja.forge_build_avatar
    → assert content["code"] == "EXTERNAL_APP_UNAVAILABLE"

test_smidja_sense_forge_timeout_returns_sense_timeout_code
    → mock forge_client.build_avatar to raise ForgeTimeoutError
    → assert content["code"] == "SENSE_TIMEOUT"

test_smidja_sense_forge_validation_error_returns_invalid_arguments_code
    → mock forge_client.build_avatar to raise ForgeValidationError
    → assert content["code"] == "INVALID_ARGUMENTS"

test_smidja_sense_close_is_idempotent_for_both_halves
    → open both halves (mocked), close twice
    → no error; both open flags False

test_smidja_sense_dual_half_both_open_is_available
    → both _brunhand_open=True, _forge_open=True
    → is_available = True; brunhand_available = True; forge_available = True

test_smidja_sense_dual_half_forge_only_open_is_available
    → _brunhand_open=False, _forge_open=True, forge.enabled=True
    → is_available = True; brunhand_available = False; forge_available = True

test_smidja_sense_dual_half_neither_open_not_available
    → both flags False → is_available = False
```

Total missing: approximately 25+ method-level tests.
**Wave 3 must add these before v0.6.1 is considered fully closed.**

---

### N-1 (NOTABLE) — `ForgeServerError` Referenced in Docs but Absent from Code

**Location (docs):**
- `docs/cartography/DATA_FLOW.md:4273` — error hierarchy diagram: `|-- ForgeServerError (F-4, Forge arm)`
- `docs/cartography/DATA_FLOW.md:4421` — routing diagram: `HTTP 5xx --> ForgeServerError (F-4)`
- `docs/cartography/DATA_FLOW.md:4796-4797` — §4.11.9 F-4: `ForgeHttpClient raises ForgeServerError`
- `docs/cartography/DATA_FLOW.md:4819` — §16 diagram: `|-- ForgeServerError (F-4)`
- `docs/cartography/SYSTEM_OVERVIEW.md:594` — error list includes `ForgeServerError`

**Location (code):** `src/heretic/skilningr/errors.py` — `ForgeServerError` does not exist.
Confirmed: `python -c "from heretic.skilningr.errors import ForgeServerError"` →
`ImportError: cannot import name 'ForgeServerError'`.

**What the code actually does:** `forge_client.py:515-516` raises the base `ForgeError` for
HTTP 5xx — functional but less precise than the named subclass the Cartographer specified.

**Impact:** Callers trying to catch `ForgeServerError` specifically would get an ImportError.
No code currently imports it; the impact is isolated to the doc/code contract. However, if a
future test or client catches by this name, it will fail. The discrepancy also makes the
documentation unreliable as a reference for Wave 3 work.

**Recommendation for Wave 3:** Either add `ForgeServerError(ForgeError)` to `errors.py` and
use it in `_handle_response` for HTTP 5xx, or remove the `ForgeServerError` references from
DATA_FLOW.md and SYSTEM_OVERVIEW.md and document that base `ForgeError` covers HTTP 5xx.

---

### X-1 (NIT) — Stale Test: `test_forge_tool_when_forge_open_returns_not_implemented_error`

**Location:** `tests/test_smidja_sense.py:429`

**Evidence:** This test was written for the Wave 1 stub world where `ForgeHttpClient.build_avatar`
raised `NotImplementedError`. After the salvage commit, `build_avatar` is implemented. The mock
in `make_mock_forge_client()` returns `AsyncMock()` with no side_effect, which returns a plain
`MagicMock` object. Calling `json.dumps(MagicMock())` raises `TypeError`, which `dispatch_tool_call`
catches as an unexpected exception and returns `SENSE_INTERNAL_ERROR`. The test asserts only
`content["error"] is True` — which is true for any error path — so it passes.

**Why this is a problem:** The test was designed to verify the stub degradation path. It now
accidentally passes because JSON serialization of a mock fails, not because of anything
intentional. The test name references a concept (`NotImplementedError`) that no longer applies.
It provides false confidence.

**Recommendation for Wave 3:** Replace with `test_smidja_sense_forge_build_avatar_routes_to_forge_client`
(listed in S-1 above), which uses a properly-returning mock and asserts the success path.

---

### Additional Code-Reading Observations (no separate findings)

**`open()` calls `self.health()` after `self._http` is set.** Correct. `forge_client.py:162-177`:
`self._http` is assigned (line 162) before the `health()` call (line 170). `health()` calls
`self._assert_open()` which checks `self._http is None`. Since `_http` was just set, the guard
passes. No ordering bug.

**`list_assets` graceful dict-wrapper handling.** `forge_client.py:458-463`: if the server
returns `{"assets": [...]}` instead of a bare list, the code unwraps it. This is a defensive
measure against future Straumur response shape changes. Appropriate.

**`tool_definitions` gating is correct.** `sense.py:299-308`: non-forge tools filtered by
`not t["function"]["name"].split(".", 1)[1].startswith("forge_")`; forge tools filtered by the
positive case. Logic is the exact inverse — no overlap, no omission.

**`_FORGE_TOOL_NAMES` frozenset.** `sense.py:85-89`: contains exactly the three tool names that
appear in `SMIDJA_TOOL_DEFINITIONS`. `forge_list_assets` is intentionally absent from both the
tool schemas and `_FORGE_TOOL_NAMES` — it is in TASK §4 as "(optional)" and was deferred.
`ForgeHttpClient.list_assets` exists as a method but is not yet exposed as a tool. This is a
deliberate, documented scope choice.

**DATA_FLOW.md §4.11.8 variable name `_forge_available` vs code `_forge_open`.** The DATA_FLOW
diagram at lines 4710/4713/4742 uses `_forge_available`; the actual attribute in `sense.py` is
`_forge_open` (line 144). This is a minor naming drift in the documentation — the property
`forge_available` exists (`sense.py:175-177`) and IS accurate; only the internal attribute name
in the diagram is off. Not filed as a separate finding (too minor for NIT), noted here for the
Cartographer to fix in the next doc pass.

---

## Verified Claims Summary

| Claim | Source | Status |
|---|---|---|
| Health probe uses `/v1/health` | TASK §4 discrepancy, forge_client.py:301, api.py:188 | VERIFIED |
| build_avatar POSTs to `/v1/avatars` | forge_client.py:353, api.py:192 | VERIFIED |
| build_avatar body includes all 5 fields | forge_client.py:346-352, api.py:55-63 | VERIFIED |
| get_avatar GETs `/v1/avatars/{session_id}` | forge_client.py:388, api.py:331 | VERIFIED |
| inspect_avatar POSTs `{vrm_path, targets}` | forge_client.py:424-429, api.py:65-69 | VERIFIED |
| list_assets GETs `/v1/assets` with query params | forge_client.py:451-456, api.py:302 | VERIFIED |
| 3 Forge tool schemas conform to OpenAI spec | tools.py:310-416 | VERIFIED |
| forge_ prefix routing rule | sense.py:460-461, 463-464 | VERIFIED |
| Dual-half lifecycle independence | sense.py:195-254 | VERIFIED |
| open() never raises to caller | sense.py:179, exception coverage 208-252 | VERIFIED |
| close() is idempotent | sense.py:263-281, forge_client.py:192-204 | VERIFIED |
| is_available correct conjunction | sense.py:165-167 | VERIFIED |
| token_env=None → no auth header | forge_client.py:159-161 | VERIFIED |
| ConnectError → ForgeUnreachableError | forge_client.py:237-239, 269-271 | VERIFIED |
| TimeoutException → ForgeTimeoutError + hint | forge_client.py:240-243, 272-275 | VERIFIED |
| HTTP 4xx → ForgeValidationError | forge_client.py:509-512 | VERIFIED |
| HTTP 5xx → ForgeError base | forge_client.py:514-517 | VERIFIED |
| No auto-disk-writes | forge_client.py full read | VERIFIED |
| No absolute paths | forge_client.py full read | VERIFIED |
| heretic.example.yaml forge block correct | heretic.example.yaml:233-237 | VERIFIED |
| ForgeServerError missing from errors.py | errors.py full read, import test | NOT MET (N-1) |
| 25 method-level tests present | tests/test_forge_client.py | NOT MET (S-1) |

---

## Release Recommendation

v0.6.1 is **releasable as a development milestone**. The implementation is sound. All API
paths, request bodies, error mappings, and lifecycle invariants are correct as verified by
code reading against the authoritative `api.py` contract.

**The milestone must not be marked fully closed until Wave 3 provides:**

1. The ~25 method-level httpx-mocked tests catalogued in S-1. This is non-negotiable before
   v0.6.2 work begins — the salvage gap must be plugged while the implementation is fresh.
2. Resolution of N-1 (either add `ForgeServerError` or remove the stale doc references).
3. Replacement of the X-1 stale test with a genuine success-path dispatch test.

The v0.6.1 exit criterion "audit verdict PASS or PASS WITH CONCERNS, no blockers" is met.

---

*Sólrún Hvítmynd, Auditor — 2026-05-08*
*The workshop has two anvils now. The implementation stands. The test net has a gap.*
*Wave 3 must close it.*
