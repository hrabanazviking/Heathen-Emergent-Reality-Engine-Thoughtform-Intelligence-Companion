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

**Phase:** v0.5 SHIPPED + AUDITED + CLEANED at `4d9d2fa`. Test baseline: Python 527 + frontend 70 = 597.

### Done in v0.5 (recap)
- `src/heretic/sjon/` — capture, encoder, orchestrator (on-demand snapshot only)
- IPC `SjonActivity` event
- CLI dual-flag gate (`?vision_in` AND `?vision_screen`)
- Frontend Sjón row with Sjón-glow blue accent
- `[vision]` extra (mss + Pillow)
- Privacy invariant locked: save_frames default False, never auto-save

### v0.5.1 deliverables (this milestone)
- ⏳ `Sjón.start_continuous_capture()` async task — loops at config.screen.interval_ms, calls capture+encode, pushes to ring buffer
- ⏳ `Sjón.stop_continuous_capture()` — stops the task cleanly
- ⏳ `Sjón.recent_frames(n: int | None = None) -> list[str]` — returns the last N data URLs from the buffer (None = all)
- ⏳ Ring buffer in `sjon.py` — collections.deque with `maxlen=config.screen.buffer_depth`
- ⏳ New config field: `sjon.screen.continuous: bool` (default False — opt-in for periodic mode)
- ⏳ New config field: `sjon.screen.attach_policy: str` (default "latest"; values "latest" | "all_buffered" | "none")
- ⏳ Multi-monitor capture: when `monitor_index = 0`, MssBackend captures the virtual all-monitors composite; when `>= 1`, individual screen
- ⏳ New helper: `MssBackend.list_monitors() -> list[dict]` (for future UI / config-tool use)
- ⏳ CLI integration: when `continuous` mode active, kick off Sjón.start_continuous_capture() at TENGSL; stop at SLOKNA; per-turn attach uses recent_frames() per attach_policy
- ⏳ vebond IPC: extend SjonActivity state machine with new states (CONTINUOUS_RUNNING, CONTINUOUS_STOPPED, BUFFER_FULL); OR add a new event SjonBuffer with depth/oldest_age fields. Architect chooses.
- ⏳ Frontend: LayerStatusItem reflects continuous mode (e.g., faster pulse, label "Sjón (continuous)" when active)
- ⏳ Tests — 25+ new Python tests (continuous task lifecycle, ring buffer behavior, attach policy paths, multi-monitor mocked) + 2-3 frontend tests
- ⏳ Total target: 555+ Python + 73+ frontend = 628+ overall

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

### Wave 1 — parallel (no Skald; no new vision essay)
- **Cartographer** (Védis Eikleið) — extend `docs/cartography/DATA_FLOW.md §4.10` with periodic-mode subsections (continuous task lifecycle, ring buffer flow, attach-policy decision tree, multi-monitor index mapping). Add §15 component-diagram update.
- **Architect** (Rúnhild Svartdóttir) — extend `src/heretic/sjon/config_model.py` with `continuous` + `attach_policy` fields + validation; update `INTERFACE.md`; choose IPC event approach (new states vs new SjonBuffer event) and update `protocol.py` + `IPC_PROTOCOL.md` accordingly; add NotImplementedError stubs in sjon.py for `start_continuous_capture()`, `stop_continuous_capture()`, `recent_frames()`, `list_monitors()`; update placeholder tests.

### Wave 2 — sequential
- **Forge** (Eldra Járnsdóttir) — implement: continuous capture task (asyncio.Task lifecycle), ring buffer (collections.deque), attach policy logic in CLI integration, multi-monitor handling, IPC state propagation, frontend continuous-mode indicator. Real Python tests + frontend Vitest tests.
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.5.1_PERIODIC_SIGHT.md`. Verify continuous task starts/stops correctly; ring buffer FIFO behavior; attach_policy paths exercised by tests; multi-monitor mapping correctness (config 0 → mss 0 composite; config N>=1 → mss N single); privacy invariant (buffer cleared on Slokna; no disk writes anywhere); backpressure (slow capture doesn't queue); throttle interaction with continuous; cross-platform.

### Wave 3 — cleanup (only if Auditor finds notables)

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 8 + update this TASK file + memory refresh.

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
- v0.4.1 first compile blocked at linker (Rust 1.95.0 installed; needs MSVC Build Tools or full MinGW-w64). See TASK_HERETIC_v0.4.1_TAURI_WRAP.md for full state.

### v0.5.x backlog (carried; NOT v0.5.1's scope)
- v0.5.2: webcam (SjonWebcamConfig activates)
- v0.5.3: privacy mask regions (blur/mask configurable areas before send)
- v0.5.x further: token-cost-aware attach policies, live continuous-context streaming

---

## 9. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. Read `docs/audit/AUDIT_v0.5.1_PERIODIC_SIGHT.md` if it exists
4. Run `git log --oneline -15` and `git status` in `C:/Users/volma/runa/HERETIC`
5. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
6. Continue from the first unchecked deliverable in §2

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.5.1 Periodic Sight — when the eye learns to keep watching.*
