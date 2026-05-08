# TASK — HERETIC v0.5.1 PERIODIC SIGHT

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-08** (immediately after v0.5 First Sight shipped + audited + cleaned at HEAD `4d9d2fa`)

> **Mode: extension of v0.5.** No new faculty; deepening of an existing one. Wave plan is slimmer than v0.5: no Skald (no new vision essay needed for an extension milestone — the eye already opened in THE_FIRST_SIGHT).

---

## 1. Task scope

Extend v0.5's on-demand screen capture with **periodic capture, ring buffer recall, and multi-monitor support**.

- **Periodic capture** — Sjón runs a background task at the configured `interval_ms` (already declared in v0.5; activates here), capturing one frame each tick into a ring buffer
- **Ring buffer** — keeps the most recent `buffer_depth` frames (already declared, default 5) in memory; oldest frames evict on overflow
- **Per-turn attach policy** — when continuous mode is active AND the user sends a message, the LATEST buffered frame (not the buffer) attaches by default. Operator can opt into multi-frame attach via `attach_policy: "latest" | "all_buffered" | "none"` (default "latest")
- **Multi-monitor** — operator configures `monitor_index` to pick a screen; v0.5.1 adds list-monitors helper + multi-monitor capture (when index 0, capture all screens; when >=1, individual screen)

The privacy invariant from v0.5 carries forward: **NEVER auto-save frames to disk**. The ring buffer lives in memory only. On `Slokna`, the buffer is cleared.

What v0.5.1 does NOT add:
- Webcam (still SjonWebcamConfig stub; v0.5.2)
- Privacy mask regions (v0.5.3)
- Token-cost-aware buffer attach policies beyond "latest" / "all" / "none"
- Live frame streaming to the agent outside of user-message turns (continuous-context streaming is v1.x territory)

---

## 2. Current status — 2026-05-08

**Phase:** v0.5.1 SHIPPED + AUDITED + CLEANED 2026-05-08; HEAD post-`2f81c6f`; 569 Python + 78 frontend = 647 tests.
*(Baseline when this task opened: v0.5 SHIPPED + AUDITED + CLEANED at `4d9d2fa`. Python 527 + frontend 70 = 597.)*

### Done in v0.5 (recap)
- `src/heretic/sjon/` — capture, encoder, orchestrator (on-demand snapshot only)
- IPC `SjonActivity` event
- CLI dual-flag gate (`?vision_in` AND `?vision_screen`)
- Frontend Sjón row with Sjón-glow blue accent
- `[vision]` extra (mss + Pillow)
- Privacy invariant locked: save_frames default False, never auto-save

### v0.5.1 deliverables (this milestone)
- ~~⏳~~ **Done 2026-05-08 (`394d360`)** — `Sjón.start_continuous_capture()` async task — loops at config.screen.interval_ms, calls capture+encode, pushes to ring buffer
- ~~⏳~~ **Done 2026-05-08 (`394d360`)** — `Sjón.stop_continuous_capture()` — stops the task cleanly
- ~~⏳~~ **Done 2026-05-08 (`394d360`)** — `Sjón.recent_frames(n: int | None = None) -> list[str]` — returns the last N data URLs from the buffer (None = all)
- ~~⏳~~ **Done 2026-05-08 (`394d360`)** — Ring buffer in `sjon.py` — collections.deque with `maxlen=config.screen.buffer_depth`
- ~~⏳~~ **Done 2026-05-08 (`ce94edf`)** — New config field: `sjon.screen.continuous: bool` (default False — opt-in for periodic mode)
- ~~⏳~~ **Done 2026-05-08 (`ce94edf`)** — New config field: `sjon.screen.attach_policy: str` (default "latest"; values "latest" | "all_buffered" | "none")
- ~~⏳~~ **Done 2026-05-08 (`394d360`)** — Multi-monitor capture: `_resolve_mss_monitor_index()` pure helper encodes mode-asymmetry; index 0 + continuous → mss composite; index 0 + on-demand → mss primary; index >=1 → pass-through
- ~~⏳~~ **Done 2026-05-08 (`394d360`)** — New helper: `MssBackend.list_monitors() -> list[dict]`
- ~~⏳~~ **Done 2026-05-08 (`3d795d4`)** — CLI integration: start_continuous_capture() at TENGSL; stop at SLOKNA; per-turn attach_policy dispatch
- ~~⏳~~ **Done 2026-05-08 (`ce94edf`)** — vebond IPC: Option A chosen — three new SjonActivityState enum values (CONTINUOUS_RUNNING, CONTINUOUS_STOPPED, BUFFER_FULL)
- ~~⏳~~ **Done 2026-05-08 (`3d795d4`)** — Frontend: LayerStatusPanel reflects continuous mode ("continuous" note badge; active pulse on continuous_running and buffer_full)
- ~~⏳~~ **Done 2026-05-08 (`2f81c6f`)** — Tests: 569 Python + 78 frontend = 647 total (Wave 2: +42 Python +8 frontend; Wave 3: +8 Python via unskip+tighten+edge). Exceeds original target of 628+.

### Constraints carried from v0.1+v0.2+v0.3+v0.4+v0.5
- Privacy invariant: NEVER auto-save frames
- All settings via heretic.yaml
- No absolute paths
- Cross-platform
- Modular, fault-tolerant, type-hinted
- No emoji

---

## 3. Architectural decisions for v0.5.1

| Decision | Choice | Rationale |
|---|---|---|
| Ring buffer container | `collections.deque(maxlen=N)` | Stdlib; O(1) append + auto-evict; thread-safe for append/popleft (we use asyncio.Lock for traversal) |
| Continuous task lifecycle | Background asyncio.Task; cancellable via stop event | Standard async pattern; integrates with existing Sjón.close() |
| Capture interval enforcement | `asyncio.sleep(interval_ms/1000)` between captures | Simplest; drift-tolerant (we don't need precise periodicity) |
| Throttle interaction | min_interval_ms still enforced even in continuous mode (a stuck capture won't double-fire) | Throttle protects backend from overload |
| Attach policy default | "latest" — single most-recent frame | Mirror v0.5 behavior (one frame per turn); buffered frames available on request |
| Buffer eviction | Oldest evicted on overflow (deque maxlen behavior) | LRU-equivalent for fixed-depth buffer |
| State propagation | New SjonActivity states (CONTINUOUS_RUNNING etc.) OR new SjonBuffer event | Architect's call; pick one for IPC clarity |
| Slokna teardown | stop_continuous_capture() + clear buffer (privacy) | Frames must NOT persist past ceremony end |
| Backpressure | If capture takes longer than interval_ms, skip the next tick (don't queue captures) | Prevent runaway during system load |
| Multi-monitor index 0 | "All monitors" virtual composite per mss convention | mss index 0 IS the all-monitors composite; map config 0 → mss 0 in this mode (NOT mapping config 0 → mss 1 like v0.5 single-monitor). Document the mapping difference. |

---

## 4. Roadmap slot

> **v0.5.1 — Periodic Sight** — extension of v0.5 First Sight. ETA 1 week.

### v0.5.1 exit criteria
- `heretic light` with `sjon.screen.continuous: true` runs background capture at interval_ms
- Ring buffer of buffer_depth frames maintained
- Per-turn attach uses attach_policy correctly
- Multi-monitor: list_monitors() returns sane info; index 0 captures composite; index >=1 captures single screen
- Privacy invariant verified: buffer cleared on Slokna; never written to disk
- Test count ≥555 Python + 73 frontend = 628 total
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 5. Mythic Engineering wave plan (slim — extension milestone)

### Wave 1 — parallel (no Skald; no new vision essay) — **COMPLETE**
- **Cartographer** (Védis Eikleið) — `b33637f` — §4.10.7-§4.10.10 + §15 extended. Multi-monitor mode-asymmetry flagged as sharp edge.
- **Architect** (Rúnhild Svartdóttir) — `ce94edf` — config fields + validation; Option A IPC (three new SjonActivityState values); stubs; 15 placeholder tests; INTERFACE.md continuous subsection.

### Wave 2 — sequential — **COMPLETE**
- **Forge** (Eldra Járnsdóttir) — `394d360` (Python continuous+ring buffer+multi-monitor, 34 tests) + `3d795d4` (attach_policy CLI + frontend indicator, 8 frontend tests).
- **Auditor** (Sólrún Hvítmynd) — `2c978dc` — PASS WITH CONCERNS, 0 blockers, 52 verified, 4 findings (N-1, N-2, X-1, X-2).

### Wave 3 — cleanup — **COMPLETE**
- **Forge** (Eldra Járnsdóttir) — `2f81c6f` — N-1 (unskip 7 tests), N-2 (tighten BUFFER_FULL assert to == 1, AsyncMock pattern), X-1 (remove getattr guard), X-2 (add edge test for continuous=False+all_buffered). Python 561 → 569. 0 open findings.

### Close-out — **COMPLETE**
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 8 written; this TASK file updated; memory refreshed; heretic.example.yaml X-2 nit closed.

---

## 6. Files to be edited (Forge target list)

### Python side
- `src/heretic/sjon/config_model.py` — add `continuous`, `attach_policy` fields to SjonScreenConfig
- `src/heretic/sjon/sjon.py` — implement start_continuous_capture(), stop_continuous_capture(), recent_frames(), ring buffer
- `src/heretic/sjon/capture.py` — add `MssBackend.list_monitors()`; clarify monitor_index 0 vs >=1 semantics for continuous-vs-single-monitor mode
- `src/heretic/cli.py` — kick off continuous capture in TENGSL when `continuous` enabled; stop in SLOKNA; per-turn attach_policy logic
- `src/heretic/vebond/protocol.py` — new states OR new event for buffer state
- `src/heretic/vebond/serve.py` — emit at continuous lifecycle milestones
- `src/heretic/sjon/INTERFACE.md` — extend Hlust contract with continuous-mode prose
- `src/heretic/sjon/__init__.py` — export new types if any
- `tests/test_sjon_orchestrator.py` — extend with continuous, ring-buffer, attach-policy tests
- `tests/test_sjon_capture.py` — extend with multi-monitor / list_monitors tests
- `tests/test_cli_vision.py` — extend with continuous-mode CLI integration tests

### Frontend side
- `frontend/src/types/ipc.ts` — extend SjonActivity OR add SjonBuffer per Architect's IPC decision
- `frontend/src/store/ceremony.ts` — handle new states/events
- `frontend/src/components/LayerStatusItem.tsx` — visual differentiation for continuous mode
- `frontend/tests/components.test.tsx` — extend test coverage

### Docs (Cartographer + Architect)
- `docs/cartography/DATA_FLOW.md` §4.10 + §15 — extensions
- `docs/architecture/IPC_PROTOCOL.md` — schema update
- `docs/architecture/LAYER_INTERFACES.md` §L3 — minor update if multi-monitor semantics shift

---

## 7. Operational rules (carried, immutable)

- Branch: `development` only
- Push frequently
- No absolute paths
- No hardcoded settings — interval_ms, buffer_depth, monitor_index, attach_policy from heretic.yaml
- Modular, fault-tolerant, cross-platform
- No emoji in code or docs
- Type hints everywhere
- After EVERY completed phase: update this TASK file + memory immediately
- **Privacy invariant: NEVER auto-save frames to disk; buffer in memory only; cleared on Slokna**

---

## 8. Backlog carried + forward

### v0.4.1 backlog (still pending — NOT v0.5.1's territory)
- v0.4.1 first compile **BLOCKED AT LINKER** — Rust 1.95.0 installed (this session); MSVC link.exe absent; GNU dlltool fails CreateProcess (minimal-profile MinGW incomplete). Requires: `winget install Microsoft.VisualStudio.2022.BuildTools` (MSVC path, recommended) or full MinGW-w64 (GNU path). See `TASK_HERETIC_v0.4.1_TAURI_WRAP.md` for full state.

### v0.5.x backlog (carried; NOT v0.5.1's scope)
- v0.5.2: webcam (SjonWebcamConfig activates)
- v0.5.3: privacy mask regions (blur/mask configurable areas before send)
- v0.5.x further: token-cost-aware attach policies, live continuous-context streaming, cached MssBackend availability flag (N-3 from v0.5 audit)

---

## 9. How to orient a future session (v0.5.1 is COMPLETE)

**v0.5.1 is fully shipped, audited, and cleaned. This task file is sealed.**

To resume work on HERETIC in a future session:

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md` — current quick-facts
3. Read `docs/DEVLOG.md` — most recent entry (entry 8, 2026-05-08)
4. Run `git log --oneline -10` and `git status` in `C:/Users/volma/runa/HERETIC`
5. Choose forward path:
   - **v0.6 Hands at the Forge** — Blender MCP via Seidr-Smidja Brúarhönd (`C:\Users\volma\runa\Seidr-Smidja`); opens `TASK_HERETIC_v0.6_HANDS_AT_THE_FORGE.md`
   - **v0.5.2 webcam** — extends Sjón with camera capture; `SjonWebcamConfig` is already declared
   - **v0.4.1 first compile** — install MSVC Build Tools or MinGW-w64, then `cargo check` in `src-tauri/`; full checklist in `TASK_HERETIC_v0.4.1_TAURI_WRAP.md §10`

HEAD at close: `2f81c6f` (forge: clean v0.5.1 audit). Python 569 + frontend 78 = 647 tests. 0 open findings.

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.5.1 Periodic Sight — when the eye learns to keep watching.*
