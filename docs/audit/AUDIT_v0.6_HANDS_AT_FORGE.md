# HERETIC — Audit: v0.6 Hands at the Forge

**Date:** 2026-05-08
**Auditor:** Sólrún Hvítmynd (Auditor role, Mythic Engineering)
**Scope:** Full code audit of the v0.6 Hands at the Forge milestone. Commits audited:
`b324544` (Skald — THE_FIRST_HAND.md), `fedae33` (Cartographer — DATA_FLOW.md §4.11 + §16),
`b4040ef` (Architect — skilningr/ scaffold + Smiðja sense scaffold + IPC SenseToolCall +
LAYER_INTERFACES.md §L5.5), `1214e5c` (Forge — Skilningr ToolDispatcher + Smiðja
BrunhandHttpClient + SmidjaSense), `75811a2` (Forge — CLI multi-round tool dispatch loop +
test_cli_tool_use), `b97e67e` (Forge — Smiðja frontend indicator + SenseToolCall IPC type
+ frontend tests).
Branch: `development`.

**Environment:** Windows 11 Home 10.0.22621, Python 3.10.11, Node.js (npm), PowerShell.

**Commands run:**
- `python -m pytest tests/ -q 2>&1 | tail -15`
- `python -m pytest tests/test_smidja_client.py tests/test_smidja_sense.py tests/test_cli_tool_use.py tests/test_skilningr_config.py tests/test_skilningr_dispatcher.py -v --tb=short 2>&1 | tail -40`
- `cd frontend && npm test -- --run 2>&1 | tail -12`
- `cd frontend && npx tsc --noEmit 2>&1 | tail -8`
- `cd frontend && npm run build 2>&1 | tail -10`
- `python -m heretic version && python -m heretic --help && python -m heretic status`
- `grep -rn "self._token" src/heretic/skilningr/`
- `grep -rn "self._token\b" src/heretic/skilningr/ | grep -v "token_env\|= token\|f\"Bearer"`
- `grep -rn "token" src/heretic/skilningr/ | grep -iv "token_env\|self._token\b\|Bearer\|REDACTED\|bearer token"` (filtered .pyc and docs)
- `grep -n "smidja|skilningr|dispatcher|tool_call|SenseToolCall|ToolDispatcher" src/heretic/vebond/serve.py`
- `grep -n "wait_timeout" src/heretic/skilningr/senses/smidja/client.py tests/test_smidja_client.py`
- Full read of all source and test files listed in scope

---

## Summary Verdict

**PASS WITH CONCERNS**

The v0.6 Hands at the Forge milestone delivers working Smiðja integration: BrunhandHttpClient,
ToolDispatcher, SmidjaSense, 6 OpenAI tool schemas, CLI multi-round dispatch loop, frontend
LayerStatusPanel Smiðja row, and the IPC SenseToolCall event type. **686 Python tests pass**
(+117 net over v0.5.1), **91 frontend tests pass** (+13), **0 failures**, **29 warnings**
(all environmental — SmidjaConfig enabled-but-no-env-var in test fixtures). TypeScript strict
mode reports **0 errors**. Vite build succeeds (163.44 kB bundle, 1.03s). CLI smoke all green.

All four Forge-flagged fragilities are resolved or triaged. The Cartographer's API discrepancy
thread is fully confirmed: the code uses the corrected paths, envelope, and screenshot envelope.
One NOTABLE finding (serve.py tool-call wiring missing — Priority 7 missed as Forge acknowledged).
One NIT (vroid timeout flow-through not covered by a dedicated test). No BLOCKERS.

| Severity | Count | Items |
|---|---|---|
| BLOCKER  | 0 | — |
| SERIOUS  | 0 | — |
| NOTABLE  | 1 | N-1 (serve.py tool-call dispatch not wired — Priority 7 missed) |
| NIT      | 1 | X-1 (vroid wait_timeout_seconds flow-through not separately tested) |
| VERIFIED | 53 | A-1..A-5, B-1..B-6, C-1..C-6, D-1..D-8, E-1..E-4, F-1..F-6, G-1..G-5, H-1..H-8, I-1..I-2, J-1..J-3 |

---

## Section A — Brúarhönd API Contract Honored

**A-1: Endpoint paths use corrected slash-nested forms.** VERIFIED.

`src/heretic/skilningr/senses/smidja/client.py:386` — `vroid_open` posts to
`"/v1/brunhand/vroid/open_project"`. Line 413 — `vroid_export` posts to
`"/v1/brunhand/vroid/export_vrm"`. The module docstring (lines 36-38) explicitly calls out
the TASK §4 wrong paths (`/vroid-open`, `/vroid-export`) and states the correct paths are in use.
Neither flat shorthand string appears anywhere in the client.

**A-2: Every POST builds envelope via `_build_envelope()`.** VERIFIED.

`client.py:293` — screenshot calls `self._build_envelope(...)`. Lines 319-325, 345-346, 360-361,
381-386, 407-413 — all other POST methods likewise call `_build_envelope`. The helper at lines
419-441 merges `request_id` (fresh uuid4), `session_id` (stable per client lifetime),
and `agent_id` (from `config.host_name`) with every call's primitive params. All 6 endpoints
confirmed.

**A-3: Screenshot decodes `{"payload": {"png_bytes_b64": "..."}}` to bytes.** VERIFIED.

`client.py:517-519` — `_post_for_png` parses `data["payload"]["png_bytes_b64"]` and calls
`base64.b64decode`. Test `test_screenshot_returns_decoded_png_bytes` (test_smidja_client.py:308)
constructs a mock response with that exact shape and asserts the returned bytes match the original.
The test passes.

**A-4: Tool name format two-part `smidja.<action>`.** VERIFIED.

`tools.py:37-285` — all 6 entries carry `"name": "smidja.<action>"`. Names confirmed:
`smidja.screenshot`, `smidja.click`, `smidja.type_text`, `smidja.hotkey`,
`smidja.vroid_open`, `smidja.vroid_export`. No `sense.` prefix. Matches SENSE_CONTRACTS.md A-2.

**A-5: Tool result format matches OpenAI spec.** VERIFIED.

`sense.py:232-236` (success path) — returns
`{"tool_call_id": call_id, "role": "tool", "content": content}`. `dispatcher.py:231-239`
(error path) — same three-field format. Tests assert `result["role"] == "tool"` and
`result["tool_call_id"]` throughout test_smidja_sense.py.

---

## Section B — Auth Invariant (CRITICAL)

**B-1: Token sourced from env var per `config.token_env`.** VERIFIED.

`client.py:115` — `token = os.environ.get(config.token_env, "")`. Resolved once at `__init__`.

**B-2: Token NEVER in `__repr__`.** VERIFIED.

`client.py:133-141` — `__repr__` returns a string with host, port, enabled, session_id.
The token field is absent. Test `test_client_init_token_not_in_repr` (line 113) sets a
distinctive token value (`"super-secret-token-xyz"`), constructs the client, calls both
`repr()` and `str()`, and asserts the value is absent in both outputs. The test passes.

**B-3: Token NEVER in log lines.** VERIFIED.

`grep -rn "self._token" src/heretic/skilningr/` returns 4 matches: lines 10 and 97 (docstrings),
line 124 (`self._token: str = token` — assignment), line 162 (`f"Bearer {self._token}"` in the
httpx header construction). No log call (`self._log.`, `logger.`) contains `self._token`.
The `[REDACTED]` literal appears in the 401 error message at line 558.

**B-4: Token NEVER in exception messages.** VERIFIED.

`client.py:558-562` — `BrunhandAuthError` message says `"Authorization header value: [REDACTED]"`,
not the actual token. Test `test_token_not_in_logs_during_auth_error` (line 642) asserts the
exception string does not contain the token value. The test passes.

**B-5: AuthError raised when enabled+missing token.** VERIFIED.

`client.py:116-122` — `if config.enabled and not token: raise BrunhandAuthError(...)`.
Test `test_client_init_raises_auth_error_if_enabled_and_token_missing` (line 97) confirms.

**B-6: `[REDACTED]` substitution correct.** VERIFIED.

The literal string `"[REDACTED]"` appears at `client.py:562` in the 401 error message.
The test at line 211 asserts `match="REDACTED"` on the raised exception. Pattern is correct.

---

## Section C — Tool Dispatch Correctness

**C-1: ToolDispatcher.register_sense + dispatch by prefix.** VERIFIED.

`dispatcher.py:54-76` — `register_sense` validates non-empty, non-dotted prefix and stores in
`self._senses[prefix]`. `dispatch()` at line 153 extracts prefix with `tool_name.split(".")[0]`
and looks up `self._senses[prefix]`. Tests `test_register_sense_stores_sense` and
`test_dispatch_routes_to_registered_sense` in test_skilningr_dispatcher.py confirm.

**C-2: Unknown tool prefix returns error tool_result, not raise.** VERIFIED.

`dispatcher.py:155-163` — when prefix is absent, returns `_error_result(... "TOOL_NOT_FOUND" ...)`.
The method does not raise. Test `test_dispatch_unknown_prefix_returns_error_json` confirms.

**C-3: Bifröst tool_call chunk detection — string heuristic assessment.** VERIFIED AS SAFE.

`cli.py:423` — `if chunk.startswith("{") and '"type": "tool_call"' in chunk:`.

This looks hazardous in isolation. However, `bifrost/client.py:354-451` shows that
`_parse_sse_stream` is already a structured JSON parser that processes each SSE data line
individually. Tool call deltas are assembled in `tool_call_buffers` across multiple SSE frames;
only when `finish_reason == "tool_calls"` (or on `[DONE]`) does the method yield a complete
JSON string of the form `{"type": "tool_call", "id": ..., "name": ..., "arguments": ...}`
(lines 387-393, 447-452). This assembled JSON is the ONLY `{`-prefixed string that could
contain `"type": "tool_call"`.

The risk Forge described — a text response beginning with `{` that happens to contain the
substring `"type": "tool_call"` — is theoretically possible if the agent narrates the
protocol structure. In practice, the Bifröst parser does NOT pass raw SSE JSON chunks to the
caller; it yields either text content deltas (line 418: `yield content`) or the assembled
tool_call JSON. A text delta that started with `{` and contained that substring would be an
edge case where the agent produces content that looks like an internal event record.

Assessment: **NOTABLE, not SERIOUS**. The check is downstream of a structured parser, not
raw string-matching on the wire. The risk exists but is low-probability in normal operation.
The correct fix (parse the JSON and check `"type"` field, or use a sentinel prefix) remains
the cleaner approach for v0.6.0.x cleanup. Does not block release.

Evidence: `bifrost/client.py:354-452` (full `_parse_sse_stream`); `cli.py:422-444` (detection
and reshape logic).

**C-4: Multi-round loop respects max_tool_call_rounds cap.** VERIFIED.

`cli.py:462-465` — dispatch only proceeds when `tool_call_rounds < max_rounds`. Line 513
logs a warning when cap is reached. The outer `while True` loop breaks when
`accumulated_tool_calls` is empty OR `tool_call_rounds >= max_rounds`.
Test `test_tool_call_round_capped_by_max_rounds` in test_cli_tool_use.py exercises the cap.

**C-5: After cap reached — log warning + halt loop + final assistant message kept.** VERIFIED.

`cli.py:513-518` — `if tool_call_rounds >= max_rounds and accumulated_tool_calls: log.warning(...)`.
`assistant_text = collected_text; break` follows immediately. The collected text from the last
pass is preserved as `assistant_text` and appended to `messages` at line 531.

**C-6: tool_result message construction in CLI matches OpenAI spec.** VERIFIED.

`cli.py:496-505` — the fallback error result uses `{"tool_call_id": ..., "role": "tool", "content": ...}`.
The success path at line 506 appends `tool_result` directly (returned by `dispatcher.dispatch`,
which already produces that structure). Test `test_tool_result_appended_to_messages` asserts
the appended message has `role == "tool"` and correct `tool_call_id`.

---

## Section D — Failure Modes

**D-1: BrunhandUnreachableError → error tool_result `{"error": "brunhand_unreachable"}`.** PARTIALLY VERIFIED.

`sense.py:238-255` catches `SmidjaError` (parent of `BrunhandUnreachableError`) and calls
`_smidja_error_code(exc)` which returns `"EXTERNAL_APP_UNAVAILABLE"` (not `"brunhand_unreachable"`)
at `sense.py:414`. The content JSON uses `"code": "EXTERNAL_APP_UNAVAILABLE"`. This matches
SENSE_CONTRACTS.md and INTERFACE.md §Error Model — the literal string `"brunhand_unreachable"`
was the informal description in the task, not the actual contract. The actual code string is
`EXTERNAL_APP_UNAVAILABLE`. Test `test_dispatch_never_raises_on_client_error` asserts
`code == "EXTERNAL_APP_UNAVAILABLE"`. Finding: correct per spec; task description was informal.

**D-2: AuthError → error tool_result with `"PERMISSION_DENIED"`.** VERIFIED.

`sense.py:415-416` — `BrunhandAuthError` maps to `"PERMISSION_DENIED"`. Covered via
`test_dispatch_never_raises_on_client_error` path.

**D-3: BrunhandTimeoutError → error tool_result.** VERIFIED.

`sense.py:417-418` — maps to `"SENSE_TIMEOUT"`. Test `test_dispatch_emits_failed_event_on_error`
uses `BrunhandTimeoutError` as the side_effect.

**D-4: 5xx → ToolDispatchError → error tool_result.** VERIFIED.

`client.py:570-589` — `_raise_for_server_error` raises `ToolDispatchError` for status >= 500.
`sense.py:413` — `ToolDispatchError` (which is an instance of `SkilningrError` but not
`SmidjaError`) is caught by the outer `except Exception` block at line 257, returning a
`SENSE_INTERNAL_ERROR` result. Test `test_screenshot_5xx_raises_tool_dispatch_error` confirms
the client raises; the sense test `test_dispatch_never_raises_on_unexpected_exception` confirms
the sense catches it.

**D-5: Malformed JSON → ToolDispatchError → error tool_result.** VERIFIED.

`client.py:483-488` — `JSONDecodeError` and other exceptions in `_post_for_payload` are
caught and re-raised as `ToolDispatchError`. `sense.py:257` catches and returns error result.

**D-6: Unknown tool prefix → error tool_result.** VERIFIED.

`dispatcher.py:155-163` — returns `TOOL_NOT_FOUND` error result.

**D-7: dispatch_tool_call NEVER raises to caller.** VERIFIED.

`sense.py:170` — docstring declares this invariant. Lines 238-275 — two `except` clauses
(SmidjaError, Exception) catch all paths and return dicts. Test
`test_dispatch_never_raises_on_client_error` and `test_dispatch_never_raises_on_unexpected_exception`
confirm by calling without `pytest.raises` and asserting `result["role"] == "tool"`.
`dispatcher.py:185-201` adds a second catch at the boundary if the sense's contract is violated.

**D-8: SmidjaSense.open() NEVER raises.** VERIFIED.

`sense.py:113-141` — two except blocks (SmidjaError, Exception) catch all failures and set
`self._is_open = False`. Tests `test_open_degrades_gracefully_on_unreachable_daemon`,
`..._on_auth_error`, `..._on_unexpected_error` all call `await sense.open()` with
side_effect errors and assert no exception is raised and `is_available is False`.

---

## Section E — vebond/serve.py Wiring (Priority 7 — Forge's Flagged Miss)

**E-1: serve.py does NOT wire Skilningr dispatcher.** CONFIRMED GAP.

Evidence: `grep -n "smidja|skilningr|dispatcher|tool_call|SenseToolCall|ToolDispatcher"
src/heretic/vebond/serve.py` returns zero matches. The entire `serve.py` file (611 lines)
contains no import of or reference to any Skilningr symbol.

**E-2: serve mode send_message ignores tool_call chunks.** CONFIRMED.

`cli.py:1004-1040` (inside `_async_serve._handle_send_message`) — `_run_turn` iterates
`client.send_message(messages)` with no `tools=` argument and applies
`if not chunk.startswith("{"):` to pass only text tokens to the EventBus. Tool_call JSON
records emitted by Bifröst are silently discarded — they start with `{` and fail the gate.
No dispatcher is constructed anywhere in `_async_serve`.

**E-3: Severity assessment.** NOTABLE.

The frontend LayerStatusPanel Smiðja row is fully implemented and connected to `SenseToolCall`
events through the ceremony store. The backend Python code for dispatch is complete and tested.
Only the wiring between `_handle_send_message` and the dispatcher is absent in serve mode.
The CLI `light` command works correctly. This is a known v0.6.0 gap that Forge explicitly
flagged (Priority 7 deferred). The body can act via `heretic light`; the UI cannot observe
that action during `heretic serve`. This does not affect the core tool-use correctness but
does mean the Summoning Circle UI never shows Smiðja activity.

**E-4: Recommendation.** Wire serve.py in a v0.6.0.x patch: construct dispatcher + smidja_sense
in `_async_serve` at TENGSL (same pattern as `_async_light`), pass `tools=tools_array` to
`send_message`, handle tool_call chunks and dispatch, emit `SenseToolCall` events through the
already-subscribed `event_bus`. Frontend code requires no changes — it already handles the events.

---

## Section F — Frontend

**F-1: SenseToolCall type literal mirrors Python enum.** VERIFIED.

`frontend/src/types/ipc.ts:172` —
`export type SenseToolCallState = "started" | "completed" | "failed";`
Matches `vebond/protocol.py:SenseToolCallState` exactly:
`STARTED = "started"`, `COMPLETED = "completed"`, `FAILED = "failed"`. Lowercase, correct.

`ipc.ts:181` — `type: "sense.tool_call"`. Matches Python `Literal["sense.tool_call"]`.

**F-2: ceremony store handles sense.tool_call events.** VERIFIED.

`frontend/src/store/ceremony.ts:405-407` —
```
_wsClient.subscribe<SenseToolCall>("sense.tool_call", (event) => {
  if (event.sense === "smidja") {
```
Routes to `setSmidjaToolCallActivity(event.state, event.tool_name)`.
Tests in ceremony-store.test.ts (lines 417-462) cover all three states (started, completed, failed)
and the counter increment for "started" only.

**F-3: LayerStatusPanel adds Smiðja row.** VERIFIED.

`LayerStatusPanel.tsx:146-151` renders a `LayerStatusItem` with `label="Smidja"`,
`status={smidjaStateToHealth(smidjaToolCallState)}`, `note={smidjaNote}`, `accent="eld"`.
Test `"renders a Smidja row in the panel"` (components.test.tsx:367) asserts
`screen.getByText("Smidja")` is present.

**F-4: Eld accent hex tokens.** VERIFIED.

`frontend/tailwind.config.js:32-34` —
```
eld: {
  DEFAULT: "#c8860a",  // Deep amber-gold — candlelight
  glow:    "#e8a020",  // Brighter glow variant
```
Both hex values match AESTHETIC.md specification. `bg-eld-glow` CSS class used at
`LayerStatusItem.tsx:57` for active/healthy states with `eld` accent.

**F-5: LayerStatusItem `eld` variant.** VERIFIED.

`LayerStatusItem.tsx:25` — `export type LayerAccent = "sjon" | "eld" | "default" | undefined;`
`LayerStatusItem.tsx:51` — `const isEld = accent === "eld";`
`LayerStatusItem.tsx:57` — `"bg-eld-glow": (status === "healthy" || status === "active") && isEld,`
Full variant pathway implemented and exercised.

**F-6: Frontend tests cover new state transitions.** VERIFIED.

`tests/components.test.tsx:354-411` — five dedicated tests for the Smiðja row: unavailable (null
state), active (started), healthy (completed), degraded (failed), note display when active.
All 91 frontend tests pass.

---

## Section G — Code Quality

**G-1: No absolute paths.** VERIFIED.

`grep` for `C:/Users\|/home/\|/Users/` in the new Skilningr module files returns no hits in
`.py` source. `client.py` docstring references an absolute path in a comment
(`Ref: C:/Users/volma/runa/Seidr-Smidja/...`) and `tools.py` docstring likewise. These are
documentation cross-references, not runtime path construction. No runtime code constructs or
opens absolute filesystem paths.

**G-2: No hardcoded settings.** VERIFIED.

All connection parameters (host, port, timeout, token_env, require_https, host_name) originate
from `SmidjaConfig`. Default values in `SmidjaConfig.__post_init__` are the YAML-specified
defaults. No literal IP, port, or timeout appears in business logic methods.

**G-3: PEP 8, type hints, no print() in library code.** VERIFIED.

Type hints on all public methods and properties. No `print()` in `src/heretic/skilningr/`.
`cli.py` contains `print()` calls — this is the CLI entry point (acceptable).

**G-4: No emoji.** VERIFIED. None found in new files.

**G-5: Forge's field-name drift risk (Fragility #1) — assessment.** RESOLVED / MOOT.

The INTERFACE.md §L5.5 (Skilningr) documents Approach B: "SkilningrConfig and SmidjaConfig are
canonical definitions in `heretic.skilningr.config_model`; grunnr.config.py imports them."
`grunnr/config.py:194-197` confirms: `from heretic.skilningr.config_model import SkilningrConfig, SmidjaConfig`.
`cli.py:124-131` constructs `SmidjaConfig(enabled=..., host=..., ...)` directly from the
hydrated grunnr snapshot fields — which is the SAME SmidjaConfig imported into grunnr.
There is no separate stub. The "drift risk" Forge flagged requires two independent definitions
to drift. Since grunnr re-exports the canonical type from skilningr, only one definition exists.
Fragility #1 is moot. VERIFIED RESOLVED.

---

## Section H — Tests

**H-1: Python test count.** VERIFIED.

`python -m pytest tests/ -q`: **686 passed, 29 warnings in 2.86s**. Zero failures.
Target was ≥607 Python + 81 frontend = 688 total. Python baseline was 569 (v0.5.1); 686 − 569 = 117 net new.

**H-2: Frontend test count.** VERIFIED.

`npm test -- --run`: **91 passed (3 test files)**. Target was ≥81. Baseline was 78; 91 − 78 = 13 net new.

**H-3: TypeScript strict mode.** VERIFIED.

`npx tsc --noEmit` exits with no output (0 errors).

**H-4: Vite build.** VERIFIED.

`npm run build`: **163.44 kB bundle, 1.03s**. Clean. No errors.

**H-5: CLI smoke.** VERIFIED.

- `python -m heretic version` → `0.1.0.dev0`
- `python -m heretic --help` → parser renders correctly
- `python -m heretic status` → reports HVILD, config search path (no heretic.yaml in this
  environment — expected; not a regression)

**H-6: Auth-invariant test spot-check.** VERIFIED.

`test_client_init_token_not_in_repr` (test_smidja_client.py:113) — sets token to
`"super-secret-token-xyz"`, calls `repr()` and `str()`, asserts value absent. PASSES.
`test_token_not_in_logs_during_auth_error` (line 642) — constructs client with real token,
triggers `_raise_for_auth`, asserts exception string does not contain the token. PASSES.
`test_token_not_in_repr_after_construction` (line 658) — second repr/str check. PASSES.

**H-7: Multi-round cap test spot-check.** VERIFIED.

`test_tool_call_round_capped_by_max_rounds` (test_cli_tool_use.py:81) — exercises a
3-round cap with a mock dispatcher that always returns tool calls. Asserts `rounds == max_rounds`
after loop exits. The test correctly models the loop break condition. PASSES.

**H-8: API-discrepancy endpoint path tests.** VERIFIED.

`test_vroid_open_posts_to_correct_path` (test_smidja_client.py:554) — asserts
`"/v1/brunhand/vroid/open_project"` in path and `"vroid-open"` NOT in path.
`test_vroid_export_posts_to_correct_path` (line 580) — same pattern for export_vrm.
Both PASS with explicit assertion messages naming the TASK §4 discrepancy.

---

## Section I — vroid wait_timeout_seconds Flow-Through (Fragility #4)

**I-1: wait_timeout_seconds parameter exists and is included in body.** VERIFIED.

`client.py:364` — `vroid_open(self, project_path: str, wait_timeout_seconds: float = 60.0)`.
Line 384 — `"wait_timeout_seconds": wait_timeout_seconds` in `_build_envelope(...)` call.
The value IS passed to the daemon. `sense.py:322-325` passes `wait_timeout_seconds` from
tool args: `args.get("wait_timeout_seconds", 60.0)`. The code path is complete and correct.

**I-2: Severity.** NIT.

No test asserts that a non-default `wait_timeout_seconds` value (e.g., 90.0) appears in the
request body. `test_vroid_open_sends_project_path` (line 603) only checks `project_path`.
The timeout flow-through is obviously correct from code inspection; the gap is merely that
no test explicitly verifies a custom value arrives in the envelope body. The correctness is
not in doubt; the coverage is absent. NIT — v0.6.x backlog.

---

## Section J — Drift Backlog

**J-1: serve.py tool-call wiring (Forge's Fragility #3).** Logged as N-1 above.
v0.6.0 cleanup task. No new work needed in Skilningr or frontend — only `_async_serve`
wiring in `cli.py`.

**J-2: Bifröst chunk detection string heuristic (Forge's Fragility #2).** Logged as C-3 above.
Assessed NOTABLE, not SERIOUS. The heuristic is downstream of Bifröst's structured SSE parser
and the risk is low in normal operation. Preferred fix: check parsed JSON for `"type": "tool_call"`
field on the structured dict rather than string-searching raw bytes. Defer to v0.6.0.x.

**J-3: vroid wait_timeout_seconds test coverage.** Logged as X-1 (NIT). One test fixture
needed. v0.6.x.

---

## Findings Table

| ID | Severity | Location | Finding | Evidence |
|---|---|---|---|---|
| N-1 | NOTABLE | `cli.py:_async_serve` + `serve.py` | serve mode does not construct a Skilningr dispatcher; `_handle_send_message` passes no `tools=` arg and silently drops all tool_call chunks from Bifröst. Smiðja tools never activate in serve mode. | `cli.py:1004-1040`; `grep` on `serve.py` returns zero Skilningr symbols. |
| C-3 | NOTABLE (not SERIOUS) | `cli.py:423` | `chunk.startswith("{") and '"type": "tool_call"' in chunk` is a string heuristic that could misroute a text response containing the substring. Assessed low risk because Bifröst's `_parse_sse_stream` is a structured parser and only yields completed tool_call JSON at that path. | `bifrost/client.py:354-452`; `cli.py:422-444`. |
| X-1 | NIT | `tests/test_smidja_client.py` | No test asserts a non-default `wait_timeout_seconds` value flows through to the request body for `vroid_open` / `vroid_export`. The code is correct; the coverage gap is minor. | `client.py:384, 411`; absence of assertion in `test_vroid_open_sends_project_path`. |

---

## Prior Finding Status

| Milestone | Finding | Status in v0.6 |
|---|---|---|
| v0.5.1 N-1 | 7 skipped config tests (placeholder) | These are now the Skilningr tests; all pass — N-1 RESOLVED |
| v0.5.1 N-2 | BUFFER_FULL timing bound loose | Not in v0.6 scope — still open, v0.5.x backlog |
| v0.5.1 X-1 | getattr defensive guard | Not in v0.6 scope — still open |
| v0.5.1 X-2 | heretic.example.yaml missing continuous + attach_policy | Not in v0.6 scope — still open |

---

*Sólrún Hvítmynd, Auditor — 2026-05-08*
*v0.6 Hands at the Forge — the hand is forged; it reaches; it holds under examination.*
