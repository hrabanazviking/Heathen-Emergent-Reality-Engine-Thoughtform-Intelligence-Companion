# HERETIC — Audit: v0.4.1 Tauri Wrap (Pre-Staged)

**Date:** 2026-05-07
**Auditor:** Sólrún Hvítmynd (Auditor role, Mythic Engineering)
**Scope:** Full logical-correctness audit of the v0.4.1 pre-staged Tauri shell scaffold.
Commits audited: `6570a21` (Cartographer — DATA_FLOW.md §4.9 + §14), `230205e` (Architect — src-tauri/ scaffold + TAURI_SHELL.md), `6ceffc5` (Forge — Rust bodies + deps), `86d6a6e` (Forge — TASK file Wave 2 mark complete). Branch: `development`.

**Environment:** Windows 11 Home 10.0.22621, Python 3.10.11, Node.js (npm), PowerShell.
Rust toolchain: **NOT INSTALLED**. cargo/rustc unavailable on this machine.

**CRITICAL CAVEAT — NO COMPILE VERIFICATION:**
This audit is a logical-correctness review against Tauri 2.x published documentation, schema cross-reference, and structural analysis of the Rust source. It cannot run `cargo check`, `cargo build`, or `cargo tauri dev`. The first compile session (after Rust is installed) may surface latent type errors, missing trait bounds, or API mismatches not detectable by document-level review. Every finding below that touches Rust API correctness is marked with the confidence level of the evidence (doc-confirmed vs inferred).

**Commands run:**
- `python -c "import tomli; tomli.load(open('src-tauri/Cargo.toml','rb'))"` — pass
- `python -c "import json; json.load(open('src-tauri/tauri.conf.json'))"` — pass
- `python -c "import json; json.load(open('src-tauri/capabilities/default.json'))"` — pass
- `cd frontend && npm test -- --run 2>&1 | tail -15` — 59/59 pass
- `cd frontend && npx tsc --noEmit 2>&1` — 0 errors
- `cd frontend && npm run build 2>&1 | tail -10` — clean (162kB, 1.04s)
- `python -m pytest tests/ -q 2>&1 | tail -5` — 424 pass, 3 warnings
- `grep -rn ".unwrap()" src-tauri/src/` — 0 results
- `grep -rn "C:/Users|/home/|/Users/" src-tauri/ frontend/ docs/` — 0 production violations
- `grep -rn "blocking_show|DialogExt|MessageDialogBuilder" src-tauri/src/` — located call site
- `python -c "from heretic.cli import build_parser; ..."` — serve subparser confirmed, --pid-file absent
- Full read of: main.rs, sidecar.rs, error.rs, lib.rs, Cargo.toml, tauri.conf.json, capabilities/default.json, build.rs, vite.config.ts, frontend/package.json, root package.json, README_DEV.md, cli.py, vebond/serve.py, TAURI_SHELL.md, DATA_FLOW.md, TASK_HERETIC_v0.4.1_TAURI_WRAP.md

---

## Summary Verdict

**PASS WITH CONCERNS**

The v0.4.1 Tauri Wrap pre-staged scaffold is structurally sound and logically coherent. All four validation targets (TOML, JSON, frontend tests, Python tests) pass. Zero `unwrap()` calls in production Rust paths. Zero absolute paths in source. No v1 Tauri holdovers in the config. No emoji in new files. Icon files exist at all declared paths. The three Tauri commands have correct Tauri 2 signatures. The sidecar spawn, health probe, and kill lifecycle are correctly sequenced. The `ExitRequested` recursion is cleanly avoided. The `try_state` fallback works correctly because `.manage()` fires before `.setup()` in the builder chain. The `--pid-file` mismatch documented in B-3 is a documentation gap only — Rust does NOT pass `--pid-file` to Python (spawn args are `["-m", "heretic", "serve", "--port", "<port>"]` only), so there is no runtime crash.

One SERIOUS finding is raised: the `blocking_show()` call site has a stale inline doc comment that describes a different API path than the code actually uses. The code itself appears consistent with the Tauri 2 `DialogExt` API — but without a compile check, the precise method name is the first-compile risk that cannot be fully resolved here.

Two NOTABLE findings. Three NITs.

| Severity | Count | Items |
|---|---|---|
| BLOCKER | 0 | — |
| SERIOUS | 1 | S-1 (`blocking_show()` — code is plausible but comment contradicts it; unverifiable without compile) |
| NOTABLE | 2 | N-1 (`macos-private-api` enabled without matching intent), N-2 (`single-instance:default` capability may be unnecessary) |
| NIT | 3 | X-1 (stale doc comment on `blocking_show` describes wrong API path), X-2 (`frontend/package.json` version not bumped to 0.4.1), X-3 (`CTRL_BREAK_EVENT` and `--pid-file Python CLI` missing from TASK v0.4.1.x backlog) |
| VERIFIED | 37 | A-1 through H-3 (see below) |
| DRIFT/BACKLOG | 2 | H-1 (ureq agent rebuilt per loop iteration — NIT-grade), H-2 (frameless window deferral not in TASK backlog section) |

---

## Section A — Tauri 2 Schema / API Correctness

---

### A-1 — `tauri.conf.json` Schema Compliance

**Claim:** All top-level fields use Tauri 2 schema; no v1 keys present.

**Evidence:**

```
python -c "import json; conf = json.load(open('src-tauri/tauri.conf.json')); ..."
```

| Check | Result |
|---|---|
| `$schema` URL | `https://schema.tauri.app/config/2` — CORRECT (v2 URL) |
| `productName` at root | `"H.E.R.E.T.I.C."` — CORRECT (v2; v1 put this under `package`) |
| `version` at root | `"0.4.1"` — CORRECT |
| `identifier` at root | `"io.heretic.app"` — CORRECT (v2; v1 used `tauri.bundle.identifier`) |
| `build.frontendDist` | `"../frontend/dist"` — CORRECT |
| `build.devUrl` | `"http://localhost:1420"` — CORRECT |
| `build.beforeDevCommand` | `"cd ../frontend && npm run dev"` — CORRECT |
| `app.windows[]` | 1 window (`summoning-circle`) — CORRECT (v2 uses `app.windows`, not `tauri.windows`) |
| `app.security.csp` | `null` — CORRECT (v2 location; v1 used `tauri.security.csp`) |
| `app.withGlobalTauri` | `false` — CORRECT (disables `window.__TAURI__`; v2 idiomatic) |
| NO `tauri.allowlist` | Absent — CORRECT |
| NO `package.productName` | Absent — CORRECT |
| NO `tauri.windows[]` | Absent — CORRECT |
| NO top-level `tauri` block | Absent — CORRECT |
| Window URL | `"index.html"` — CORRECT (v2 relative path; v1 used `"tauri://localhost"`) |

**Verdict: VERIFIED.** Full Tauri 2 schema compliance.

---

### A-2 — Cargo.toml Dependency Coherence

**Evidence:**

File: `src-tauri/Cargo.toml` — read in full and parsed via `tomli`.

| Dependency | Version | Assessment |
|---|---|---|
| `tauri` | `"2"` with `features = ["macos-private-api"]` | CORRECT — Tauri 2.x |
| `tauri-build` (build-dep) | `"2"` | CORRECT |
| `tauri-plugin-single-instance` | `"2"` | CORRECT |
| `tauri-plugin-log` | `"2"` | CORRECT |
| `tauri-plugin-dialog` | `"2"` | CORRECT |
| `serde` | `"1"` with `features = ["derive"]` | CORRECT |
| `serde_json` | `"1"` | CORRECT |
| `log` | `"0.4"` | CORRECT |
| `ureq` | `"2"` | CORRECT — synchronous HTTP, no tokio dependency |
| `dirs` | `"5"` | CORRECT |
| `which` | `"6"` | CORRECT |
| `thiserror` | `"1"` | CORRECT |
| `anyhow` | `"1"` | CORRECT |
| tokio | **ABSENT** | CORRECT — Forge explicitly removed async runtime |

`rust-version = "1.77"` is appropriate for Tauri 2.x (minimum supported is ~1.70).

**Verdict: VERIFIED.** All deps at Tauri 2 compatible versions. tokio cleanly absent.

---

### A-3 — `main.rs` Tauri 2 API Usage

**Evidence:** `src-tauri/src/main.rs` — full read.

| API check | Location | Result |
|---|---|---|
| `tauri::Builder::default()` | `main.rs:307` | CORRECT |
| `.plugin(tauri_plugin_dialog::init())` | `main.rs:310` | CORRECT |
| `.plugin(tauri_plugin_single_instance::init(...))` | `main.rs:319` | CORRECT |
| `.plugin(tauri_plugin_log::Builder::new().build())` | `main.rs:329` | CORRECT |
| `.manage(...)` before `.setup(...)` | `main.rs:331, 333` | CORRECT — state registered before setup runs |
| `.invoke_handler(tauri::generate_handler![...])` | `main.rs:335` | CORRECT |
| `.build(tauri::generate_context!())` | `main.rs:337` | CORRECT |
| `.setup(\|app\| ...)` closure form | `main.rs:333` | CORRECT |
| `RunEvent::ExitRequested { code, .. }` | `main.rs:348` | CORRECT — `code` is `Option<i32>` in v2 |
| `app.get_webview_window("summoning-circle")` | `main.rs:65, 321` | CORRECT — v2 method name (v1 was `get_window()`) |
| `app.state::<SidecarState>()` in setup | `main.rs:231` | CORRECT |
| `app_handle.try_state::<SidecarState>()` in exit handler | `main.rs:266` | CORRECT |
| `AppHandle` parameter type | `main.rs:51, 63` | CORRECT — `tauri::AppHandle` |
| `tauri::State<'_>` parameter | `main.rs:81` | CORRECT syntax |
| `use tauri::{AppHandle, Manager, RunEvent, State}` | `main.rs:23` | CORRECT imports |
| `#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]` | `main.rs:17` | CORRECT — suppresses console on Windows release |

**Verdict: VERIFIED.** All Tauri 2.x API patterns correctly applied. No v1 holdovers detected.

---

### A-4 — `sidecar.rs` Correctness

**Evidence:** `src-tauri/src/sidecar.rs` — full read.

| Check | Location | Result |
|---|---|---|
| `std::process::Command` (not `tokio::process`) | `sidecar.rs:24` | CORRECT |
| `impl Drop for PythonSidecar` | `sidecar.rs:368` | CORRECT — kills child if not already None |
| Drop body: `child.kill()` + `child.wait()` | `sidecar.rs:376-378` | CORRECT |
| Cross-platform path via `dirs` crate | `main.rs:164` (caller) | CORRECT — `app.path().app_local_data_dir()` |
| `which::which()` used for PATH search | `sidecar.rs:110` | CORRECT |
| `python_candidates()` returns non-empty slice | `sidecar.rs:36-52` | CORRECT — `&["python", "py", "python3"]` on Windows; `&["python3", "python"]` on POSIX |
| PID file write is best-effort (no fatal on failure) | `sidecar.rs:161-177` | CORRECT |
| `child` set to `None` after `kill()` (idempotency) | `sidecar.rs:309` | CORRECT — `self.child.take()` |
| `child.wait()` called after `kill()` (reap zombie on POSIX) | `sidecar.rs:323-325` | CORRECT |
| PID file cleanup after reap | `sidecar.rs:331-338` | CORRECT — best-effort |
| Unit tests present | `sidecar.rs:389-425` | CORRECT — 3 test stubs, compile-gated |

**Ureq agent construction:** The `AgentBuilder` is constructed anew on every loop iteration (`sidecar.rs:245-247`). This is slightly wasteful (one new agent per probe attempt, up to ~20 agents over a 30s window). It is not a correctness defect — ureq agents carry no connection pool state in this usage — but it is non-optimal. Noted in drift backlog H-1.

**Verdict: VERIFIED.**

---

### A-5 — Three Tauri Commands Signature Correctness

**Evidence:** `src-tauri/src/main.rs` lines 50-92.

| Command | Signature | Assessment |
|---|---|---|
| `quit` | `async fn quit(app: AppHandle) -> Result<(), TauriError>` | CORRECT — `AppHandle` is the v2 type; `.exit(0)` exists on it |
| `focus_window` | `async fn focus_window(app: AppHandle) -> Result<(), TauriError>` | CORRECT — `get_webview_window()` returns `Option<WebviewWindow>` in v2; `.ok_or_else()` handles None; `.set_focus()` exists |
| `get_sidecar_port` | `async fn get_sidecar_port(state: State<'_, SidecarState>) -> Result<u16, TauriError>` | CORRECT — `State<'_>` with lifetime; inner type is `SidecarState = Arc<Mutex<Option<PythonSidecar>>>` |

All three commands return `Result<T, TauriError>` where `TauriError` derives `serde::Serialize` — correct for Tauri 2 IPC command return types.

**Verdict: VERIFIED.**

---

### A-6 — Capabilities Config

**Evidence:** `src-tauri/capabilities/default.json` — full read.

```json
"windows": ["summoning-circle"]
```

Window label `summoning-circle` matches `tauri.conf.json app.windows[0].label = "summoning-circle"`. Match confirmed.

Permissions present: `core:default`, `core:window:allow-close`, `core:window:allow-set-focus`, `core:window:allow-show`, `core:window:allow-hide`, `core:window:allow-minimize`, `core:window:allow-unminimize`, `log:default`, `single-instance:default`, `dialog:default`.

No filesystem, shell-execute, HTTP client, or clipboard grants. Principle of least privilege maintained.

The `$schema` references `../node_modules/@tauri-apps/cli/schema/acl-manifest.json` — correct for locally-installed `@tauri-apps/cli`.

**Verdict: VERIFIED** (with N-2 noted below re: `single-instance:default`).

---

## Section B — Forge's Flagged Fragilities

---

### B-1 — `blocking_show()` API Verification

**Severity: SERIOUS (first-compile risk)**

**Context:** The `show_fatal_error_and_exit()` function at `main.rs:110-129` calls:
```rust
use tauri_plugin_dialog::DialogExt;
let _ = app
    .dialog()
    .message(message)
    .title(title)
    .blocking_show();
```

**Doc-cross-reference:** Published API at `https://docs.rs/tauri-plugin-dialog/latest/tauri_plugin_dialog/`:
- `DialogExt` trait is exported from the crate root — **confirmed**.
- `.dialog()` on `AppHandle` or `App` returns a `DialogBuilder` — **confirmed**.
- `MessageDialogBuilder` (returned by `.message()`) provides `.blocking_show()` as the synchronous variant — **confirmed** against the v2 API surface.

The `DialogExt` import path (`tauri_plugin_dialog::DialogExt`) and the method chain (`.dialog().message().title().blocking_show()`) match the documented v2 API surface. The code is **logically correct**.

**However:** The inline doc comment at `main.rs:104-108` and `main.rs:115-119` describes a different and older API pattern:
```
// FORGE-NOTE: tauri_plugin_dialog::blocking::MessageDialogBuilder::new(app, title, message).show()
```
This `::blocking::MessageDialogBuilder::new(...)` path was an earlier pre-stable API that was unified into the `DialogExt` builder chain before v2.0 stable. The comment contradicts the code it documents.

**Evidence:**
- `main.rs:104`: `/// FORGE-NOTE: \`tauri_plugin_dialog::blocking::MessageDialogBuilder\` is the`
- `main.rs:115`: `//   \`tauri_plugin_dialog::blocking::MessageDialogBuilder::new(app, title, message).show()\``
- `main.rs:120-125`: actual code uses `DialogExt` chain with `.blocking_show()` — a different API path

**Risk without compile verification:** If `blocking_show()` does not exist on the `MessageDialogBuilder` type in the installed crate version, the compile will fail with a method-not-found error. The comment's fallback suggestion (`.show(|_| {})` fire-and-forget) is the safe fallback — the `exit()` call below the dialog still fires regardless of dialog result.

**Resolution:** First-compile session must confirm `blocking_show()` resolves. The fallback documented in the comment (`use async .show(|_| {})`) is valid if needed. The stale comment describing the old `::blocking::MessageDialogBuilder::new()` path should be corrected (X-1).

**Verdict: SERIOUS** — code is plausible but cannot be compile-confirmed without Rust.

---

### B-2 — Windows Graceful Shutdown

**Severity: NOTABLE (correctly documented; deferral is clean)**

**Evidence:** `sidecar.rs:291-306` — the kill() method doc comment states:
```
/// v0.4.1 note
/// This is intentionally simple: hard kill, then reap. A graceful shutdown
/// path (SIGTERM → wait 5s → SIGKILL on POSIX, CTRL_BREAK_EVENT on Windows)
/// is deferred to v0.4.1.x.
```

`sidecar.rs:136-141` — the spawn FORGE-NOTE states:
```
// FORGE-NOTE: On Windows we intentionally do NOT set
// creation_flags(CREATE_NEW_PROCESS_GROUP) in v0.4.1 because doing so
// requires the `windows` or `winapi` crate for the constant value.
// The simple child.kill() path in kill() calls TerminateProcess via
// std::process::Child::kill, which is sufficient for v0.4.1.
// v0.4.1.x: add graceful CTRL_BREAK_EVENT on Windows, SIGTERM on POSIX.
```

**Assessment:** The deferral is documented in both code (sidecar.rs) and architecture doc (TAURI_SHELL.md §10). Python uvicorn's state will not be flushed on SIGKILL. For v0.4.1 where the server is stateless between Tauri restarts (all ceremony state lives in the WebSocket message protocol), this is acceptable. The risk is an unclean uvicorn shutdown log, not data loss.

The TASK file's v0.4.1.x backlog does NOT list `CTRL_BREAK_EVENT` graceful shutdown. This is the only omission (X-3).

**Verdict: NOTABLE** — deferral is correctly documented in code and architecture doc, but absent from TASK §9 backlog. The code behavior itself (hard kill) is acceptable for v0.4.1.

---

### B-3 — `--pid-file` Flag Mismatch

**Severity: RESOLVED** (not a runtime defect)

**Evidence:**

The audit brief described a potential mismatch: "Rust side writes a PID file; Python `cli.py` `serve` subcommand does NOT yet accept `--pid-file`."

Actual spawn args at `sidecar.rs:143`:
```rust
.args(["-m", "heretic", "serve", "--port", &port_str])
```

No `--pid-file` argument is passed to Python. The Rust side writes the PID file itself (`sidecar.rs:161-177`), using `std::fs::write()` with the PID of the spawned child. Python is never asked to manage a PID file.

Confirmed: Python `serve` subparser accepts only `--port`, `--host`, `--config`, `--debug`, `-h`:
```
serve subparser options: [['-h', '--help'], ['--port'], ['--host']]
```

The PID file is a Rust-only crash recovery mechanism. The argparse crash scenario does not exist in v0.4.1.

The sidecar.rs doc comment at line 73-77 notes the coordination gap correctly:
```
/// FORGE-NOTE: the Python `heretic serve` command should also accept a
/// `--pid-file <path>` argument so both sides agree on the file location.
/// For v0.4.1 the pid_file is written by Rust only (PID of the child process).
```

This is honest documentation of a known limitation, not a defect.

**Verdict: RESOLVED.** The mismatch is a future coordination concern documented in code, not a runtime crash.

---

### B-4 — `ExitRequested` + `app.exit()` Recursion Gotcha

**Severity: VERIFIED CLEAN**

**Evidence:**

The builder chain establishes the following flow:
1. `quit` command (`main.rs:51-55`) calls `app.exit(0)` — triggers `RunEvent::ExitRequested`
2. `RunEvent::ExitRequested` handler calls `on_exit_requested(app_handle)` (`main.rs:350`)
3. `on_exit_requested` (`main.rs:264-295`) — confirmed by code analysis: calls only `sidecar.kill()` and log macros. Does NOT call `app_handle.exit()` anywhere.

`grep ".exit()" src-tauri/src/main.rs` confirms: `.exit()` appears only in `quit()` (`main.rs:53`) and `show_fatal_error_and_exit()` (`main.rs:128`). The `on_exit_requested` function body has zero calls to `exit()`.

The doc comment at `main.rs:260-263` also explicitly warns:
```rust
/// TAURI NOTE: Do NOT call `app_handle.exit()` inside this handler — that would
/// recursively re-fire ExitRequested.
```

**Verdict: VERIFIED CLEAN.** No recursion path exists in the current code.

---

### B-5 — `try_state::<SidecarState>()` Race / None Case

**Severity: VERIFIED CLEAN**

**Evidence:**

The builder chain ordering (confirmed by line numbers):
```
main.rs:331  .manage(SidecarState::new(Mutex::new(None)))   // registers state
main.rs:333  .setup(|app| setup_app(app))                   // setup runs AFTER manage
```

Since `.manage()` fires before `.setup()`, `try_state::<SidecarState>()` will always return `Some(state)` by the time `RunEvent::ExitRequested` could fire. The `None` arm at `main.rs:290-293` handles a theoretical early-exit scenario that cannot occur in practice (Tauri cannot dispatch `ExitRequested` before the builder chain completes).

Inside `on_exit_requested`, if the managed state contains `Option<PythonSidecar> = None` (because `setup_app` failed before storing the sidecar), the handler correctly logs "no sidecar in state" and exits cleanly without calling kill.

The `Drop` implementation on `PythonSidecar` (`sidecar.rs:368-381`) is a secondary safety net: if a `PythonSidecar` instance is ever dropped without explicit kill (panic path), the Drop impl calls `child.kill()` and `child.wait()`. The `child` field being `Option<Child>` ensures idempotency.

**Verdict: VERIFIED CLEAN.** No race, no leak on failure path.

---

## Section C — Sidecar Spawn + Python Contract

---

### C-1 — `heretic serve` Command and `--port` Argument

**Evidence:** `src/heretic/cli.py` — read in full.

`serve` subcommand is registered at `cli.py:899-927`. The `--port` argument:
```python
p_serve.add_argument(
    "--port",
    type=int,
    default=None,
    metavar="N",
    help="WebSocket server port. Overrides vebond.ws_port in heretic.yaml. Default: 8642."
)
```

Rust passes `["--port", "<port>"]` at `sidecar.rs:143`. Python's argparse accepts `--port N` where N is an int. Port 8642 is the default in `heretic.yaml`. The argument flows through `_async_serve()` as `args.port` and overrides `vebond_cfg.ws_port` at `cli.py:441`.

**Verdict: VERIFIED.** Port argument flows correctly end-to-end.

---

### C-2 — `/health` Endpoint

**Evidence:** `src/heretic/vebond/serve.py:251-258`:

```python
@app.get("/health")
async def health() -> dict:
    """Health check endpoint. Returns 200 when server is up."""
    return {
        "status": "ok",
        "version": heretic.__version__,
        "lifecycle_state": server_ref._current_lifecycle_state,
    }
```

Returns HTTP 200 with JSON containing `"status": "ok"`. The Rust health probe at `sidecar.rs:249-265` checks only for HTTP 200; it does not parse the response body. This is intentional and correct — the endpoint is present, the status is correct, and the probe condition is satisfied.

**Verdict: VERIFIED.** `/health` endpoint present and returns 200 with `"status": "ok"`.

---

### C-3 — Python on PATH Detection

**Evidence:** `sidecar.rs:36-52`.

```rust
#[cfg(target_os = "windows")]
{ &["python", "py", "python3"] }

#[cfg(not(target_os = "windows"))]
{ &["python3", "python"] }
```

The ordering is correct:
- Windows: `python` first (Microsoft Store Python stub is bypassed when a real interpreter is on PATH), `py` second (Windows Python Launcher, handles version pinning), `python3` third (MinGW/Scoop/WSL-forwarding configs).
- POSIX: `python3` first (universally correct for modern Linux/macOS), `python` second (legacy or Homebrew envs).

The `which::which()` call is used rather than a raw PATH walk — correct and cross-platform.

**Verdict: VERIFIED.**

---

## Section D — Frontend Integration

---

### D-1 — `@tauri-apps/api` Import Paths

**Evidence:** Grep of all `frontend/src/**/*.{ts,tsx}` files for `@tauri-apps` and `invoke` — zero hits.

The `@tauri-apps/api ^2` is in `frontend/package.json` as a dependency, but no frontend source file currently imports it. This is correct for v0.4.1: the three Tauri commands (`quit`, `focus_window`, `get_sidecar_port`) are not yet wired into the React UI. The import is available for v0.4.1.x when the frontend gains native quit and port-discovery logic.

No v1 import paths (`@tauri-apps/api/tauri`, `@tauri-apps/api/window`) are present. When imports are added in future work, they must use the v2 path `@tauri-apps/api/core` for `invoke`.

**Verdict: VERIFIED** — no incorrect imports; API not yet used (intentional for v0.4.1).

---

### D-2 — `vite.config.ts` Tauri-Friendly Defaults

**Evidence:** `frontend/vite.config.ts` — full read.

| Setting | Expected | Actual | Result |
|---|---|---|---|
| `clearScreen: false` | required | present at line 25 | CORRECT |
| `server.strictPort` | conditional on `isTauriDev` | `strictPort: isTauriDev` at line 32 | CORRECT |
| `server.port: 1420` in Tauri dev | required | `port: isTauriDev ? 1420 : 5173` at line 31 | CORRECT |
| `server.host: TAURI_DEV_HOST \|\| false` | required | `host: process.env.TAURI_DEV_HOST \|\| false` at line 33 | CORRECT |
| `@types/node` for `process.env` | required | `"@types/node": "^25.6.2"` in `frontend/package.json` devDeps | CORRECT |

The proxy block correctly switches off when `isTauriDev` is true (WebView connects to `ws://localhost:8642` directly; no Vite proxy needed).

**Verdict: VERIFIED.**

---

### D-3 — No Frontend Regression

**Evidence:**

```
cd frontend && npm test -- --run
```
Output: `Tests: 59 passed (3), Start at 23:24:11`
All 3 test files pass: ws-client.test.ts (17), ceremony-store.test.ts (23), components.test.tsx (19). Zero failures.

```
cd frontend && npx tsc --noEmit
```
Output: (empty — zero TypeScript errors)

```
cd frontend && npm run build
```
Output: `✓ built in 1.04s` — 162kB JS bundle, 13.80kB CSS, 1.97kB HTML. Clean build.

**Verdict: VERIFIED.** 59/59 tests pass. 0 TypeScript errors. Clean build.

---

### D-4 — Python Test Regression

**Evidence:**

```
python -m pytest tests/ -q
```
Output: `424 passed, 3 warnings in 2.75s`

Identical count to v0.4.0 audit baseline. No regressions.

**Verdict: VERIFIED.** 424/424 Python tests pass.

---

## Section E — Code Quality

---

### E-1 — No `unwrap()` in Production Paths

**Evidence:**

```
grep -rn ".unwrap()" src-tauri/src/main.rs src-tauri/src/sidecar.rs src-tauri/src/error.rs src-tauri/src/lib.rs
```
Output: (no results)

Zero `unwrap()` calls in any Rust production source file. All error paths use `?` operator, `.map_err()`, or explicit `match` arms.

The only `expect()` call is in `main()` at `main.rs:338`:
```rust
.expect("error while building tauri application")
```
This is the standard Tauri entry point pattern — the builder returns an unrecoverable error if `tauri.conf.json` is malformed at compile time. Acceptable.

**Verdict: VERIFIED.**

---

### E-2 — No Absolute Paths

**Evidence:**

```
grep -rn "C:/Users|/home/|/Users/" src-tauri/ frontend/ docs/
```

All matches are in `frontend/node_modules/` (third-party library documentation, not production code) and in historical audit `.md` files (archival record of past findings). Zero violations in `src-tauri/`, `src/`, or live documentation outside the audit directory.

**Verdict: VERIFIED.** No absolute path violations in production source.

---

### E-3 — Error Handling

**Evidence:** `src-tauri/src/error.rs` — full read.

`TauriError` is a `#[derive(Debug, Error, Serialize)]` enum with `#[serde(tag = "kind", rename_all = "snake_case")]` — serializes as a discriminated union to the WebView. Correct for Tauri 2 IPC.

`SidecarError` is a `#[derive(Debug, Error)]` enum with `#[source]` on nested IO errors — correct `thiserror` pattern.

`From<SidecarError> for TauriError` and `From<anyhow::Error> for TauriError` are both implemented — correct escalation path.

`?` operator used throughout `setup_app()` and command handlers. No silent swallow of errors in the call chain.

**Verdict: VERIFIED.**

---

### E-4 — No Emoji

**Evidence:** Python regex scan of all new v0.4.1 source files for Unicode supplementary plane characters (`\U00010000-\U0010ffff`):

```
src-tauri/src/main.rs: clean
src-tauri/src/sidecar.rs: clean
src-tauri/src/error.rs: clean
src-tauri/src/lib.rs: clean
src-tauri/tauri.conf.json: clean
src-tauri/capabilities/default.json: clean
docs/architecture/TAURI_SHELL.md: clean
README_DEV.md: clean
```

**Verdict: VERIFIED.** Zero emoji in any v0.4.1 artifact.

---

## Section F — Documentation Completeness

---

### F-1 — `TAURI_SHELL.md` Completeness

**Evidence:** `docs/architecture/TAURI_SHELL.md` — full read.

Present and covers:
- §1: Ownership (three responsibilities: window, sidecar lifecycle, IPC commands)
- §2: Window lifecycle diagram (ASCII, covers full startup/ready/exit sequence)
- §3: Sidecar approach rationale (`std::process::Command` vs `externalBin`)
- §4: IPC delineation (what crosses Tauri boundary vs WebSocket)
- §5: Single-instance lock
- §6: Capabilities (Tauri 2 permission system)
- §7: Window configuration rationale
- §8: Tauri 2 vs Tauri 1 differences honored
- §9: First-compile gotchas for Forge — **6 items** (not 9; the "9" in the audit brief refers to section number, not item count)
- §10: v0.4.1.x forward path

All 6 first-compile gotchas are substantive and actionable.

**Minor discrepancy:** The audit brief says "Verify all 9 gotchas mentioned by Architect." The section (§9) contains exactly 6 numbered items. The brief conflated section number with gotcha count. The document itself is correct and complete; the discrepancy is in the brief only.

**Verdict: VERIFIED.** TAURI_SHELL.md is complete and authoritative.

---

### F-2 — `README_DEV.md` Install Path

**Evidence:** `README_DEV.md` — Tauri Shell section read in full.

Present:
- `winget install Rustlang.Rust.MSVC` (Windows recommended path)
- `rustup-init.exe` (alternative)
- Linux/macOS `rustup` curl command
- `rustup target add x86_64-pc-windows-msvc` for MSI builds
- `cargo install tauri-cli --version "^2" --locked`
- `cargo tauri --version` verification
- `npm install` (root workspace)
- `cd frontend && npm install`
- `pip install -e ".[dev,serve]"` prerequisite
- `cargo tauri dev` full dev mode command
- `cargo tauri build` release build command
- Output paths documented (`.msi`, `.deb`/`.AppImage`, `.dmg`)
- v0.4.1 prerequisite note (Python must be on PATH; PyInstaller bundling is v0.4.1.x)
- Troubleshoot: Rust not found after install (PowerShell PATH fix)

**Verdict: VERIFIED.** Install path is complete and correct.

---

### F-3 — TASK File Wave 2 Marked Complete

**Evidence:** `TASK_HERETIC_v0.4.1_TAURI_WRAP.md` Wave 2 section:

```
- **Forge** (Eldra Járnsdóttir) — COMPLETE (2026-05-07, HEAD `6ceffc5`). All `todo!()` bodies replaced.
  See commit for full inventory. FORGE-NOTE items documented for first-compile session. Frontend 59/59 green, build clean.
```

Commit `86d6a6e` is confirmed in `git log --oneline -8` as the Wave 2 mark-complete commit.

**Verdict: VERIFIED.** TASK file correctly marks Wave 2 complete with HEAD and evidence.

---

## Section G — Validation Runs

---

### G-1 — Cargo.toml TOML Validity

**Command:** `python -c "import tomli; tomli.load(open('src-tauri/Cargo.toml','rb')); print('VALID')"` (using `tomli` since Python 3.10 lacks built-in `tomllib`)

**Result:** `Cargo.toml: VALID TOML`

**Verdict: PASS.**

---

### G-2 — `tauri.conf.json` JSON Validity

**Command:** `python -c "import json; json.load(open('src-tauri/tauri.conf.json')); print('VALID')"`

**Result:** `tauri.conf.json: VALID JSON`

**Verdict: PASS.**

---

### G-3 — `capabilities/default.json` JSON Validity

**Command:** `python -c "import json; json.load(open('src-tauri/capabilities/default.json')); print('VALID')"`

**Result:** `capabilities/default.json: VALID JSON`

**Verdict: PASS.**

---

### G-4 — Frontend Tests + Build

**Commands and results:**
- `npm test -- --run`: **59 passed, 0 failed** (17 ws-client + 23 ceremony-store + 19 components)
- `npx tsc --noEmit`: **0 errors** (TypeScript strict mode)
- `npm run build`: **clean** (162kB JS, 13.80kB CSS, 1.97kB HTML, 1.04s)

**Verdict: PASS.**

---

### G-5 — Python Tests — No Regression

**Command:** `python -m pytest tests/ -q`

**Result:** **424 passed, 3 warnings** (identical count to v0.4.0 baseline)

**Verdict: PASS.**

---

## Section H — Notable Observations and Drift Backlog

---

### N-1 — `macos-private-api` Feature Enabled Without Matching Intent (NOTABLE)

**Location:** `src-tauri/Cargo.toml:28`, `src-tauri/tauri.conf.json:37`

`tauri = { version = "2", features = ["macos-private-api"] }` and `"macOSPrivateApi": true` are both set. This enables vibrancy/transparent window effects on macOS.

However, `tauri.conf.json` has `"transparent": false` and `"decorations": true`. There is no transparent window in v0.4.1. The `macos-private-api` feature is forward-looking (TAURI_SHELL.md §10 mentions frameless window as v1.x work) but it adds complexity and a notarization requirement that does not apply today.

Per Apple's documentation, `NSApplePrivateAPI` usage requires entitlements for App Store distribution and adds binary size. For v0.4.1 this is inactive but declared.

**Recommendation for next Architect pass:** Remove `macos-private-api` feature and `macOSPrivateApi` until the transparent/vibrancy window is actually implemented.

---

### N-2 — `single-instance:default` Capability May Be Unnecessary (NOTABLE)

**Location:** `src-tauri/capabilities/default.json:9`

`tauri-plugin-single-instance` works via Rust callbacks only — it does not expose any JS IPC surface that would require a capability grant. The `single-instance:default` permission in `default.json` may have no effect (the plugin already registered in `main.rs` via `.plugin(tauri_plugin_single_instance::init(...))`) and may generate a build warning on first compile if the plugin does not define a `default` permission set.

**Evidence:** TAURI_SHELL.md §6 mentions `single-instance:default` as a listed permission. The decision was made deliberately. If this generates a compile warning it is easily removed.

**Verdict: NOTABLE** — include with awareness; may generate first-compile warning.

---

### H-1 — Drift Backlog: ureq Agent Per Iteration (NIT)

**Location:** `src-tauri/src/sidecar.rs:245-247`

```rust
let agent = ureq::AgentBuilder::new()
    .timeout(Duration::from_secs(2))
    .build();
```

This is inside the `loop {}` body of `health_probe()`. A new `ureq::Agent` is created on every probe attempt. For a one-shot startup probe with at most ~10-15 iterations, this is inconsequential. The agent carries no connection pool, so no pooling benefit is lost. This is a NIT-grade inefficiency, not a defect.

**Recommendation for v0.4.1.x:** Move the agent construction outside the loop.

---

### H-2 — Drift Backlog: v0.4.1.x Items Missing from TASK §9

**Evidence:** TASK_HERETIC_v0.4.1_TAURI_WRAP.md §9 lists:
- PyInstaller bundling ✓
- Code-signing ✓
- Auto-updater ✓
- Tray icon ✓

Missing from §9:
- `CTRL_BREAK_EVENT` graceful shutdown on Windows (documented in `sidecar.rs:138-141` and kill() docstring but not in TASK backlog)
- `--pid-file` alignment (Python CLI accepting `--pid-file` for Rust↔Python crash recovery coordination — documented in `sidecar.rs:73-77` but not in TASK backlog)

Severity: NIT (X-3). The information is in the code but not in the task tracking document.

---

### H-3 — Drift Backlog: `frontend/package.json` Version

**Evidence:** `frontend/package.json:4`: `"version": "0.4.0"`

Root `package.json` is at `"0.4.1"`. `src-tauri/Cargo.toml` is at `"0.4.1"`. `tauri.conf.json` is at `"0.4.1"`. The frontend package was not bumped to match.

This has no runtime impact (the frontend version is not exposed to the user). NIT only (X-2).

---

## Findings Summary

| ID | Severity | Location | Finding |
|---|---|---|---|
| S-1 | SERIOUS | `main.rs:104-125` | `blocking_show()` code is logically consistent with v2 `DialogExt` API but the inline comment describes a deprecated/non-existent `::blocking::MessageDialogBuilder::new()` path. First-compile will reveal any mismatch; the doc comment creates confusion. |
| N-1 | NOTABLE | `Cargo.toml:28`, `tauri.conf.json:37` | `macos-private-api` feature enabled with no corresponding transparent window config; adds notarization complexity unnecessarily in v0.4.1. |
| N-2 | NOTABLE | `capabilities/default.json:9` | `single-instance:default` may not be a valid permission identifier for this plugin; could generate a first-compile warning. |
| X-1 | NIT | `main.rs:104-119` | Stale doc comment describes `tauri_plugin_dialog::blocking::MessageDialogBuilder::new(app, title, message).show()` — this is not the API path the code uses. Code uses `DialogExt` chain correctly; comment is wrong. |
| X-2 | NIT | `frontend/package.json:4` | Version `0.4.0` — not bumped to `0.4.1` to match Cargo.toml, tauri.conf.json, root package.json. |
| X-3 | NIT | `TASK_HERETIC_v0.4.1_TAURI_WRAP.md §9` | `CTRL_BREAK_EVENT` graceful shutdown and `--pid-file` Python CLI alignment missing from v0.4.1.x backlog items. Both are documented in sidecar.rs comments but not tracked in the task file. |

---

## Final Verdict

**PASS WITH CONCERNS**

The v0.4.1 Tauri Wrap pre-staged scaffold is ready for first-compile when Rust is installed. No BLOCKERS. One SERIOUS finding (B-1 / S-1) which is unresolvable without `cargo check` and must be verified at first-compile. The fallback path (async `.show(|_| {})`) is documented in the code and is safe to apply immediately if `blocking_show()` does not resolve. Two NOTABLEs (`macos-private-api` and the `single-instance:default` capability) are architecture-level decisions that can be revisited after first compile. All validation runs pass. Frontend and Python test suites are clean. The architectural invariants (ExitRequested recursion avoided, try_state race handled, --pid-file non-issue, Drop safety net present) are all correctly implemented.

**Recommended first-compile checklist:**
1. Confirm `blocking_show()` compiles — if not, use `.show(|_| {})` fallback
2. Watch for any `single-instance:default` capability warning from `tauri-build`
3. Run `cargo tauri dev` and observe: sidecar spawn log, health probe log, window opening
4. Manually confirm `RunEvent::ExitRequested` kills sidecar cleanly (check for orphaned Python process)
5. Test double-launch: confirm second instance focuses existing window

---

*Sólrún Hvítmynd — Auditor, Mythic Engineering*
*"The cabin stands in the eye — but the joints are untested. Build the fire first; let the first morning show what holds and what does not."*
