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

**Phase:** v0.4.1 PRE-STAGED + AUDITED at `fed2478`. Baseline: Python 424 + frontend 59 = 483 tests passing. v0.4.1 awaits Rust install for first compile.

### Done in v0.1+v0.2+v0.3+v0.4.0+v0.4.1 (recap, do not redo)
- v0.1: L0 Grunnr + L1 Bifröst + CLI shell — 121 tests
- v0.2: L2 Rödd Tunga (TTS via ChatterBox) — +103 → 224 tests
- v0.3: L2 Rödd Hlust (STT via Whisper.cpp) — +115 → 339 tests
- v0.4.0: L4 Vébond Eldahús substrate (Python WebSocket + React frontend) — +85 Python, +59 frontend → 424 + 59 = 483 tests
- v0.4.1: src-tauri/ scaffold (PRE-STAGED; awaits Rust install) — no executable change to test counts
- All audit findings closed
- The body can be summoned in browser; the spirit can speak and listen; the user can see the ceremony

### v0.5 deliverables (this milestone)
- ⏳ `src/heretic/sjon/` — L3 Sjón Python module
  - `__init__.py` — exports
  - `INTERFACE.md` — module contract
  - `config_model.py` — SjonConfig, SjonScreenConfig, SjonWebcamConfig dataclasses (webcam declared, NOT implemented in v0.5; matches v0.2's RoddSttConfig declared-but-deferred pattern)
  - `errors.py` — SjonError, ScreenCaptureError, BackendUnavailableError, FrameEncodingError, PermissionDeniedError
  - `capture.py` — ScreenCaptureBackend ABC + MssBackend (cross-platform via `mss` library, MIT) + NullBackend; `best_available()` factory chain
  - `encoder.py` — frame → PNG bytes → base64 data URL; resize/crop helpers
  - `sjon.py` — Sjón orchestrator: capture-on-demand for v0.5, ring buffer (configured depth, default 5), throttling (no captures faster than `interval_ms` per config)
- ⏳ Bifröst integration — `BifrostClient.send_message()` accepts optional `image_data_urls: list[str] | None` and includes them in the OpenAI message payload as image_url content per audit C-Q-C3
- ⏳ CLI integration — `light` command's turn loop calls `sjon.snapshot()` before sending the user message IF `config.sjon.screen.enabled` AND `?vision_in` capability set; image attached to user-role message
- ⏳ vebond/protocol.py — new event `sjon.activity` with state {idle, capturing, encoding, failed}; emit at capture milestones
- ⏳ Frontend — Sjón activity indicator in LayerStatusPanel (matches Tunga/Hlust pattern with Sjón-glow blue accent)
- ⏳ heretic.example.yaml — verify `sjon:` block matches SjonConfig defaults (already partially specified in LAYER_INTERFACES.md §L3)
- ⏳ Tests — mocked mss, mocked screen capture; aim for 30+ new Python tests + 5+ frontend tests; total 518+ Python + 64+ frontend = 580+ overall
- ⏳ docs/vision/THE_FIRST_SIGHT.md — Skald essay (sixth panel of vision cycle)
- ⏳ docs/cartography/DATA_FLOW.md §4.10 — sight flow + §15 Sjón component diagram

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

### Wave 1 — parallel (no inter-dependencies)
- **Cartographer** (Védis Eikleið) — `docs/cartography/DATA_FLOW.md §4.10 "Sight flow (v0.5 — outbound, on-demand)"` showing user-message-send → SjonOrchestrator.snapshot() → MssBackend.capture() → encode (resize + PNG + base64) → attach to OpenAI image_url content → Bifröst send_message → spirit. Add §15 Sjón component diagram. Note the mirror-of-Tunga symmetry (Tunga: agent text → audio out; Sjón: screen capture → image in).
- **Skald** (Sigrún Ljósbrá) — `docs/vision/THE_FIRST_SIGHT.md` — sixth panel of the vision cycle (after WHY_HERETIC, CEREMONY_NARRATIVE, THE_FIRST_VOICE, THE_FIRST_LISTENING, THE_FIRST_FACE). What it means for the body to see what the user sees. Privacy as covenant. The mirror-versus-window distinction. ~2500-3500 words.
- **Architect** (Rúnhild Svartdóttir) — scaffold:
  - `src/heretic/sjon/` skeleton (INTERFACE.md, config_model.py, errors.py, capture.py ABC + MssBackend + NullBackend, encoder.py skeleton, sjon.py orchestrator)
  - Update grunnr/config.py with SjonConfig consolidation (Approach B import from sjon.config_model)
  - Update pyproject.toml — add `mss>=9` and `Pillow>=10` to either `[voice]` or new `[vision]` extra (your call)
  - Update vebond/protocol.py — add `SjonActivity` event with state field
  - Update IPC_PROTOCOL.md schema for the new event
  - Skip-marked placeholder tests
  - Confirm clean import + 424+ Python tests still passing

### Wave 2 — sequential
- **Forge** (Eldra Járnsdóttir) — implement:
  - `MssBackend` with full mss API integration (capture, lifecycle, multi-monitor handling)
  - `encoder.py` resize/crop/PNG-encode/base64 helpers
  - `Sjón` orchestrator with throttle + on-demand snapshot
  - Bifröst client extension: optional `image_data_urls` arg threaded through to OpenAI multimodal message format
  - CLI `light` integration: snapshot before send when conditions met
  - vebond/serve.py: emit SjonActivity events on capture lifecycle
  - Frontend: LayerStatusPanel shows Sjón row with Sjón-glow blue accent (matching aesthetic.md L3 token); subscribe to sjon.activity in ceremony store
  - Real Python tests (mocked mss, mocked Pillow encoding) + frontend Vitest tests
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.5_FIRST_SIGHT.md`. Verify: mss + Pillow integration; frame format (inline base64 PNG matches OpenAI vision content schema); capability gating (no frame sent if `?vision_in` not set); throttle works; privacy invariant (save_frames default false); fault tolerance (mss unavailable, permission denied, encode fail all degrade gracefully); cross-platform; tests cover happy + each failure path; no absolute paths; no hardcoded settings.

### Wave 3 — cleanup (only if Auditor finds notables)
Per-finding dispatch.

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 7 + update this TASK file + memory refresh.

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

## 13. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. Read `docs/audit/AUDIT_v0.5_FIRST_SIGHT.md` if it exists (audit complete)
4. Run `git log --oneline -15` and `git status` in `C:/Users/volma/runa/HERETIC`
5. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
6. Continue from the first unchecked deliverable in §2

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.5 First Sight — when the body learns to see what the user sees.*
