# TASK — HERETIC v0.5 FIRST SIGHT

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-08** (immediately after v0.4.1 Tauri Wrap pre-staged + audited at HEAD `fed2478`)

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1), speak (v0.2), listen (v0.3), and be seen (v0.4.0) to a body that can also **see**.

L3 Sjón is the agent's sight — screen capture, captured locally, encoded inline as base64 PNG, injected into the agent's turn as image content per the OpenAI vision format. The body offers what its eyes show; the spirit interprets.

The canonical contract for L3 Sjón lives in `docs/architecture/LAYER_INTERFACES.md §L3` — the `sjon:` config block, output event `vision::frame(base64_png, timestamp, source)`, and capability flag `?vision_screen` already exist. Webcam support is part of the v1.x roadmap, not v0.5.

Per the audit C-Q-A1 / C-Q-C3 resolutions sealed in v0.0:
- Frames are sent **inline base64** as `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}` per OpenAI vision format
- `?vision_in` (renamed from `?vision_screen` in agent-protocol per v0.4.1 cleanup of `?voice_in`/`?voice_out` — verify naming) gates whether frames are sent at all

---

## 2. Current status — 2026-05-08

**Phase:** v0.5 SHIPPED + AUDITED + CLEANED 2026-05-08; HEAD post-`7a84098`; 527 Python + 70 frontend = 597 tests. All findings closed. Scribe close complete.

### Done in v0.1+v0.2+v0.3+v0.4.0+v0.4.1 (recap, do not redo)
- v0.1: L0 Grunnr + L1 Bifröst + CLI shell — 121 tests
- v0.2: L2 Rödd Tunga (TTS via ChatterBox) — +103 → 224 tests
- v0.3: L2 Rödd Hlust (STT via Whisper.cpp) — +115 → 339 tests
- v0.4.0: L4 Vébond Eldahús substrate (Python WebSocket + React frontend) — +85 Python, +59 frontend → 424 + 59 = 483 tests
- v0.4.1: src-tauri/ scaffold (PRE-STAGED; awaits Rust install) — no executable change to test counts
- All audit findings closed
- The body can be summoned in browser; the spirit can speak and listen; the user can see the ceremony

### v0.5 deliverables (this milestone)
- DONE `src/heretic/sjon/` — L3 Sjón Python module
  - `__init__.py` — exports
  - `INTERFACE.md` — module contract
  - `config_model.py` — SjonConfig, SjonScreenConfig, SjonWebcamConfig dataclasses (webcam declared, NOT implemented in v0.5; matches v0.2's RoddSttConfig declared-but-deferred pattern)
  - `errors.py` — SjonError, ScreenCaptureError, BackendUnavailableError, FrameEncodingError, PermissionDeniedError
  - `capture.py` — ScreenCaptureBackend ABC + MssBackend (cross-platform via `mss` library, MIT) + NullBackend; `best_available()` factory chain
  - `encoder.py` — frame → PNG bytes → base64 data URL; resize/crop helpers; **max_width_override + max_height_override params added in Wave 3 (S-1 fix)**
  - `sjon.py` — Sjón orchestrator: capture-on-demand for v0.5, ring buffer (configured depth, default 5), throttling (no captures faster than `interval_ms` per config); **oversize retry now passes halved dims via encoder override (S-1 fix, Wave 3)**
- DONE Bifröst integration — `capability_vision_screen` body-state flag on OpenAICompatClient; content array per §2.1
- DONE CLI integration — dual-flag gate (vision_in AND vision_screen), multimodal content array in turn loop, Sjón init/close
- DONE vebond/protocol.py — SjonActivity event (idle/capturing/encoding/failed) + event_emitter wired in serve mode
- DONE Frontend — Sjón row in LayerStatusPanel, LayerStatusItem "active" state with animate-pulse, sjonState in ceremony store
- DONE Tests — 100 new Python tests + 11 new frontend tests (Wave 2: 74+26; Wave 3: +3); total 527 Python + 70 frontend = 597 overall
- DONE docs/vision/THE_FIRST_SIGHT.md — Skald essay, sixth panel of vision cycle (`e7c4b02`)
- DONE docs/cartography/DATA_FLOW.md §4.10 + §15 — Cartographer sight flow + Sjón component diagram (`a982fc9`)
- DONE docs/audit/AUDIT_v0.5_FIRST_SIGHT.md — Auditor PASS WITH CONCERNS; 0 blockers; S-1 + N-1 + N-2 all resolved (`e390d78` audit; `7a84098` S-1+N-1 fix)
- DONE DEVLOG entry 7 — Scribe canonical session record (this close, Eirwyn Rúnblóm)

### Constraints carried from v0.1+v0.2+v0.3+v0.4
- All settings via `heretic.yaml` (no hardcoding)
- No absolute paths
- Cross-platform (Windows / Linux / macOS)
- Modular, fault-tolerant, type-hinted
- Fault tolerance: if Sjón can't capture, lifecycle does not crash — proceed without frame, log warning
- No emoji in code or docs

---

## 3. Screen capture library — decision

**Choice: `mss` (MIT, cross-platform).**

Rationale:
- Cross-platform: Windows + macOS + Linux from one API
- MIT licensed
- Lightweight: ~50KB, single dependency, no native build requirements
- Returns raw BGRA frames as bytes — easy to convert to PIL Image and PNG-encode
- Active maintenance, well-tested

Alternatives considered + rejected:
- **`PIL.ImageGrab`** — Windows + macOS only; Linux requires X server; bad for cross-platform
- **`pyautogui.screenshot()`** — wraps Pillow; same Linux issue
- **`mss-python`** — same library, just a name disambiguation
- **OS-native via subprocess** (e.g., `screencapture` on macOS, `gnome-screenshot` on Linux) — fragile, requires per-OS handling

`mss` goes in the `[voice]` extra alongside sounddevice/numpy/pywhispercpp/webrtcvad/Pillow. **Pillow** is the second new dep — needed for PIL Image manipulation (resize, crop, PNG encoding). Both go in the new `[vision]` extra (or absorbed into `[voice]` since both are sense-related — Architect's call).

---

## 4. Frame format — sealed by audit

Per `docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md` C-Q-C3 (RESOLVED):
- Inline base64 PNG, NOT URL references
- Format: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,<bytes>"}}`
- Sent inline with the user message in the `content` array (multimodal message format)
- Default capture: full primary screen; resize to 1280×720 max (configurable); PNG compression level 6 (good ratio, fast encode)
- Approximate size: 1280×720 PNG ≈ 1.2 MB worst-case; well within reasonable limits

---

## 5. Capture trigger model — v0.5 decision

**v0.5 ships ON-DEMAND capture only.** Specifically:

- Per-turn capture: when the user submits a message AND `config.sjon.screen.enabled` AND `?vision_in` capability is set on the connected agent, Sjón captures one frame, encodes, attaches to the user message
- No auto-interval capture in v0.5 (the `interval_ms` config field is reserved for v0.5.x periodic capture)
- No agent-on-demand capture (`auga.snapshot` MCP tool) — that's L5 Skilningr territory, deferred to v0.7+
- Throttle: no captures within `min_interval_ms` (default 1000ms) of the previous to prevent rapid-fire spam

This is the mirror of v0.2 Tunga's "speak when the response streams" behavior: v0.5 Sjón is "show when the user speaks."

The Auditor (Sólrún) at v0.0 sealed the format; the Architect locks the trigger model here. v0.5.x can add periodic-capture-streaming once we know what works.

---

## 6. Architectural decisions for v0.5

| Decision | Choice | Rationale |
|---|---|---|
| Screen capture lib | `mss` (MIT) | Cross-platform; lightweight; no native build |
| Image encoder | `Pillow` (HPND/MIT-style) | Industry standard for PNG; handles resize/crop |
| Capture trigger | On-demand at user-message-send | v0.5 minimum viable; periodic deferred to v0.5.x |
| Frame format | Inline base64 PNG (per audit C-Q-C3) | Sealed in v0.0 audit |
| Default resolution | 1280×720 max | Balances detail vs token cost |
| Multi-monitor | Primary monitor only by default; configurable | Privacy default; user opts into multi-mon |
| Webcam support | Declared in config but not implemented | v1.x; matches v0.2 RoddSttConfig pattern |
| L5 Auga MCP wrapper | Out of scope for v0.5 | v0.7+ when L5 Skilningr ships |
| Failure mode | Continue turn without frame; log warning | Per RULES.AI fault tolerance — sight is augmentation, not blocking |
| Privacy invariant | NEVER auto-save frames to disk | `save_frames: false` default; opt-in only; even when opt-in, save only to ephemeral session-scoped temp dir |

---

## 7. Roadmap slot (from `docs/ROADMAP.md`)

> **v0.5 — First Sight** — Screen capture sense — L3 — 1-2 wk

### v0.5 exit criteria
- `heretic light` with `sjon.screen.enabled: true` AND agent supporting vision sends a screen frame attached to each user message
- Frame is correctly encoded as inline base64 PNG matching the OpenAI vision content format
- Configurable via `heretic.yaml` `sjon.screen.*` keys
- Graceful degradation if mss unavailable, screen permission denied, or encoding fails
- Test count ≥518 Python + 64 frontend = 582 total
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

### v0.5.x backlog
- v0.5.x periodic interval capture (the `interval_ms` field activates)
- v0.5.x ring buffer of recent frames (the `buffer_depth` field activates) for "what just happened" recall
- v0.5.x multi-monitor support
- v0.5.x webcam (matches the L3 webcam config block)

---

## 8. Mythic Engineering wave plan

Standard pattern.

### Wave 1 — parallel (no inter-dependencies) — COMPLETE
- **Skald** (Sigrún Ljósbrá) — `docs/vision/THE_FIRST_SIGHT.md` — sixth panel of vision cycle. COMPLETE at `e7c4b02`.
- **Cartographer** (Védis Eikleið) — `docs/cartography/DATA_FLOW.md §4.10 + §15`. COMPLETE at `a982fc9`.
- **Architect** (Rúnhild Svartdóttir) — `src/heretic/sjon/` scaffold + IPC SjonActivity + naming-bridge resolution + LAYER_INTERFACES.md §L3 cleanup. COMPLETE at `d2768c2`.

### Wave 2 — sequential — COMPLETE
- **Forge** (Eldra Járnsdóttir):
  - L3 Sjón substrate (capture + encoder + orchestrator + 74 tests). COMPLETE at `6ec4198`.
  - Bifröst capability_vision_screen + CLI dual-flag vision attach + test_cli_vision.py (26 tests). COMPLETE at `2e6b4ad`.
  - Frontend Sjón indicator (types + store + panel + 11 tests). COMPLETE at `fe1536f`.
  - TASK file closure + partial DEVLOG mark (Forge over-reach per N-2). Committed at `20fd70f`.
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.5_FIRST_SIGHT.md`. PASS WITH CONCERNS. 0 blockers. S-1 (serious) + 3 NOTABLE. COMPLETE at `e390d78`.

### Wave 3 — cleanup — COMPLETE
- **Forge** (Eldra Járnsdóttir) — S-1 fix (encoder override params + sjon.py wires them) + N-1 fix (test asserts halved dims) + 3 new encoder tests. COMPLETE at `7a84098`. Final: 527 Python + 70 frontend = 597 tests. 0 open findings.

### Close-out — COMPLETE
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 7 + TASK file update + memory refresh. COMPLETE 2026-05-08.

---

## 9. Files to be created (Forge target list)

```
src/heretic/sjon/
  __init__.py
  INTERFACE.md
  config_model.py     # SjonConfig + SjonScreenConfig + SjonWebcamConfig dataclasses
  errors.py           # SjonError + ScreenCaptureError + BackendUnavailableError + FrameEncodingError + PermissionDeniedError
  capture.py          # ScreenCaptureBackend ABC + MssBackend + NullBackend + best_available() factory
  encoder.py          # FrameEncoder: resize, crop, PNG-encode, base64; data URL helper
  sjon.py             # Sjón orchestrator: snapshot(), throttle, ring buffer
tests/
  test_sjon_config.py
  test_sjon_capture.py
  test_sjon_encoder.py
  test_sjon_orchestrator.py
  test_cli_vision.py  # CLI integration: vision attaches to message
```

Existing files Forge updates (additive):
- `src/heretic/grunnr/config.py` — add SjonConfig field via Approach B import
- `src/heretic/bifrost/client.py` — `send_message()` accepts `image_data_urls`
- `src/heretic/cli.py` — wire Sjón snapshot into `light` turn loop
- `src/heretic/vebond/protocol.py` — add SjonActivity event
- `src/heretic/vebond/serve.py` — emit SjonActivity at capture lifecycle
- `frontend/src/types/ipc.ts` — mirror SjonActivity
- `frontend/src/store/ceremony.ts` — subscribe + state
- `frontend/src/components/LayerStatusPanel.tsx` — add Sjón row
- `pyproject.toml` — add mss + Pillow to chosen extra
- `heretic.example.yaml` — verify sjon: block matches SjonConfig defaults
- `docs/architecture/IPC_PROTOCOL.md` — add SjonActivity to event schema (Architect)

---

## 10. Operational rules (carried, immutable)

- Branch: `development` only
- Push frequently
- No absolute paths
- No hardcoded settings — capture interval, resolution, etc. via `heretic.yaml`
- Modular, fault-tolerant, cross-platform
- No emoji in code or docs
- Type hints (Python) + types (TypeScript) everywhere
- Each subagent commits with their own attribution line
- After EVERY completed phase: update this TASK file + memory immediately
- **Privacy invariant: NEVER auto-save frames to disk**

---

## 11. v0.4.1 backlog (carried; not v0.5's territory)

- v0.4.1 first compile (after Rust install)
- v0.4.1.x PyInstaller bundling, code-signing, auto-updater, tray icon
- v0.4.x sense-toggle implementation (v0.5 just adds another read-only row)
- v0.4.x voice waveform widget

These remain backlog. v0.5 does not address them.

---

## 12. v0.5.x backlog (forward-looking)

- v0.5.x periodic interval capture (continuous streaming when active)
- v0.5.x ring buffer for "what just happened" recall
- v0.5.x multi-monitor support
- v0.5.x webcam (the SjonWebcamConfig block activates)
- v0.5.x privacy modes (e.g., blur/mask configurable regions before send)

---

## 13. How to resume from this point — forward orientation

v0.5 is COMPLETE. This task file is sealed. The next session opens a new task file.

**State at close:** HEAD `7a84098`. Branch `development`. 527 Python + 70 frontend = 597 tests. 0 open findings. Five primary faculties: connect (L1), speak (L2 Tunga), listen (L2 Hlust), be seen (L4), see (L3). Only "tools" and L5 sense hub remain to reach v1.0.

**Forward path — Volmarr's choice:**

**Option A — v0.6 Hands at the Forge (Blender MCP)**
- Brings L5 Skilningr's Smiðja sense (Blender) online via Seidr-Smidja Brúarhönd v0.1.
- Seidr-Smidja is at `C:/Users/volma/runa/Seidr-Smidja` on `development`. 489 tests passing. Brúarhönd v0.1 shipped 2026-05-06.
- Path B (Loom→VRoid translation) is Seidr-Smidja v0.2 territory; HERETIC v0.6 would wire to what already exists in v0.1 (Brúarhönd MCP tools: screenshot, click, vroid_export).
- HERETIC task file: `TASK_HERETIC_v0.6_HANDS_AT_THE_FORGE.md` (to be created).

**Option B — v0.5.x periodic capture**
- Activate `interval_ms` config key for continuous-streaming mode.
- Ring buffer for "what just happened" recall.
- Multi-monitor support (SjonScreenConfig `monitor_index` and multi-mon enumeration).
- Webcam (SjonWebcamConfig activates — backend not yet implemented).
- Cached availability flag in MssBackend (N-3 recommendation from audit).

**Option C — v0.4.1 first compile (Tauri)**
- Install Rust: `winget install Rustlang.Rust.MSVC` or `rustup-init.exe`.
- Then open a new session: `cargo check` in `src-tauri/`, fix any latent errors, `cargo tauri dev` to verify the window opens and the Python sidecar spawns.
- Checklist is in `TASK_HERETIC_v0.4.1_TAURI_WRAP.md §10 Path B` and `docs/audit/AUDIT_v0.4.1_TAURI_WRAP.md §Final Verdict`.

**Resume orientation for any of the above:**
1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read `docs/DEVLOG.md` entry 7 — this arc's record
3. Run `git log --oneline -10` and `git status` in `C:/Users/volma/runa/HERETIC`
4. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
5. Open the appropriate forward task file (Option A/B/C) before doing any implementation

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*Updated by Eirwyn Rúnblóm (Scribe), 2026-05-08 — close-out pass.*
*v0.5 First Sight — the body learned to see. The eye is opened; the gaze is offered.*
