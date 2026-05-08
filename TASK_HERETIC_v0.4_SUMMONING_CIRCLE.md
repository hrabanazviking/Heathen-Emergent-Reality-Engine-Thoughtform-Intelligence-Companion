# TASK — HERETIC v0.4 SUMMONING CIRCLE

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.3 First Listening shipped + audited at HEAD `77d49c9`)

> **Status: v0.4.0 SHIPPED + AUDITED 2026-05-07; v0.4.1 Tauri wrap PENDING (Rust install required)**

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1), speak (v0.2), and listen (v0.3) to a body with a **face**.

The Summoning Circle (Eldahús — "fire-house") is L4 Vébond — the visible shell of the ceremony. It is the part of the body the user actually sees and touches: the Light-the-Candle button, the lifecycle indicator that pulses with the ceremony's state, the chat panel where the spirit's words appear, the layer-status indicators that reveal which faculties are alive.

Per `docs/architecture/CEREMONY.md`, `docs/vision/AESTHETIC.md`, and the manifesto, the canonical frontend stack is **Tauri + React**. The aesthetic is the modern longhouse in the dark — warm, purposeful, alive with bioluminescent accents (Eld/amber, Sjón-glow/blue, Mál-green/teal, Hvíla-grey/dormant).

---

## 2. Current status — 2026-05-07

**Phase:** v0.4.0 SHIPPED + AUDITED at `08890ee`. Python 424 + frontend 59 = 483 total tests passing. 0 open findings. v0.4.1 Tauri wrap deferred pending Rust install.

### Done in v0.1+v0.2+v0.3 (recap, do not redo)
- v0.1: L0 Grunnr + L1 Bifröst + CLI shell — 121 tests
- v0.2: L2 Rödd Tunga (TTS via ChatterBox) — 224 tests
- v0.3: L2 Rödd Hlust (STT via Whisper.cpp) — 339 tests
- All audit findings closed
- The body now has both halves of the voice faculty; Samræður is two-directional voice

### Done in v0.4.0 (this milestone — complete)
- ~~v0.4.0 Python WebSocket backend (`heretic serve`)~~ Done 2026-05-07 (`9cc4b62`)
- ~~`frontend/` directory with full React + Vite + TypeScript + Tailwind stack~~ Done 2026-05-07 (`824da42`)
- ~~Norse aesthetic per AESTHETIC.md (all hex tokens verified verbatim)~~ Done 2026-05-07 (`d9186ab`)
- ~~13 React components: SummoningCircle through ConnectionIndicator~~ Done 2026-05-07 (`d9186ab`)
- ~~WebSocket client + Zustand ceremony store~~ Done 2026-05-07 (`3838b25`)
- ~~`docs/architecture/IPC_PROTOCOL.md` — authoritative typed schema~~ Done 2026-05-07 (`824da42`, updated `edf68ee`)
- ~~`docs/vision/THE_FIRST_FACE.md` — fifth panel of vision cycle~~ Done 2026-05-07 (`e3874fd`)
- ~~`docs/cartography/DATA_FLOW.md` §4.8 + §13~~ Done 2026-05-07 (`b3209db`)
- ~~Audit PASS WITH CONCERNS, 0 blockers — all 1 SERIOUS + 3 NOTABLE resolved~~ Done 2026-05-07 (`5ead989`, cleaned `edf68ee` + `08890ee`)
- **Final tests: Python 424 + frontend 59 = 483 total. HEAD `08890ee`.**

### v0.4 ARCHITECTURAL CONSTRAINT (read first)

**Rust toolchain is NOT installed on this machine.** Probed 2026-05-07: `rustc: command not found`, `cargo: command not found`. Tauri requires Rust + native build tooling. This session cannot build the Tauri shell.

**Therefore v0.4 ships in two sub-milestones:**

- **v0.4.0 — Eldahús Substrate (THIS SESSION):**
  - Python `heretic serve` command — async WebSocket + REST backend wrapping the existing Bifröst/Tunga/Hlust orchestration
  - `frontend/` directory — Vite + React + TypeScript + Tailwind CSS
  - Norse aesthetic per AESTHETIC.md (dark theme, Eld/Sjón-glow/Mál-green accents, Cinzel + Inter + JetBrains Mono fonts)
  - Summoning Circle ring component, lifecycle state visual, chat panel, layer-health panel, sense-toggle panel, light/extinguish controls
  - Frontend connects via WebSocket to localhost backend
  - Runs via `npm run dev` (browser dev mode) — fully functional ceremony in browser
  - Tests for both halves (Python pytest + frontend Vitest)

- **v0.4.1 — Tauri Wrap (DEFERRED, separate session, requires Rust install):**
  - `src-tauri/` Rust+Tauri shell wrapping the React frontend
  - Tauri spawns Python `heretic serve` as a sidecar
  - WebView2 verified on Windows 11
  - Native window with Norse window chrome
  - Build artifacts (.msi installer for Windows; .dmg for macOS; .deb/.AppImage for Linux)
  - This requires Volmarr to install rustup first (or run `winget install Rustlang.Rust.MSVC`)

This is honest scope. v0.4.0 ships the body that has a face the user can interact with via browser; v0.4.1 wraps that face in native Tauri chrome once tooling is available. The frontend code does not change between them — Tauri just hosts the same React app.

### v0.4.0 deliverables (this milestone — ALL COMPLETE 2026-05-07)
- ~~`src/heretic/vebond/` — L4 Python module with EventBus + WebSocket server~~ Done
- ~~`src/heretic/cli.py` — `serve` subcommand added~~ Done
- ~~`frontend/` directory with package.json, vite.config.ts, tsconfig.json, tailwind.config.js~~ Done (44 files)
- ~~`frontend/src/` — 13 React components per AESTHETIC.md~~ Done
- ~~`frontend/src/api/` — typed WS client + TypeScript types mirroring protocol.py~~ Done
- ~~`frontend/tests/` — Vitest + React Testing Library (59 tests)~~ Done
- ~~`docs/architecture/IPC_PROTOCOL.md` — full typed schema + vocabulary bridge~~ Done
- ~~`docs/vision/THE_FIRST_FACE.md` — Skald essay (fifth panel)~~ Done
- ~~`docs/cartography/DATA_FLOW.md` §4.8 + §13~~ Done
- ~~Audit verdict PASS WITH CONCERNS, 0 blockers~~ Done — all findings resolved

### Constraints carried from v0.1+v0.2+v0.3
- All settings via `heretic.yaml` (no hardcoding)
- No absolute paths
- Cross-platform (Windows / Linux / macOS)
- Modular, fault-tolerant, type-hinted
- Fault tolerance: backend handles WS disconnect cleanly; frontend handles backend-down cleanly
- Backend and frontend remain independently runnable: backend runs in headless mode, frontend connects to existing backend
- No emoji in code or docs

---

## 3. IPC protocol decision

**Choice: WebSocket on `ws://localhost:8642/ws`** (default, configurable via `vebond.ws_port`).

Rationale:
- Bidirectional streaming (lifecycle events + agent token deltas + voice activity flow to UI; commands flow up)
- Works in browser without Tauri (this session)
- Continues to work under Tauri (Tauri spawns Python sidecar listening on localhost)
- Simpler than SSE+REST hybrid; easier to mock in tests
- No reverse-proxy or auth layer needed for v0.4.0 (localhost only)

### Event schema (preliminary — Architect locks this in `docs/architecture/IPC_PROTOCOL.md`)

**Server → Client (push events):**
- `ceremony.state_changed` — `{from: LifecycleState, to: LifecycleState, timestamp: ISO8601}`
- `bifrost.health` — `{status: "open"|"closed"|"opening"|"failed", endpoint: str, latency_ms: int|null}`
- `tunga.activity` — `{state: "idle"|"synthesizing"|"speaking"|"failed"}`
- `hlust.activity` — `{state: "idle"|"loading"|"listening"|"transcribing"|"failed", level_db: float|null}`
- `agent.token` — `{role: "assistant", text_delta: str, sequence_id: int}`
- `agent.turn_complete` — `{turn_id: str, finish_reason: str}`
- `error` — `{level: "warn"|"error", source: str, message: str}`

**Client → Server (commands):**
- `light` — `{}` — initiate Kynding → Tengsl ceremony
- `extinguish` — `{}` — initiate Slokna shutdown
- `send_message` — `{text: str}` — user message into the turn loop
- `toggle_sense` — `{sense_id: str, enabled: bool}` — defer to v0.4.x; v0.4.0 only reads heretic.yaml
- `cancel_turn` — `{turn_id: str}` — abort the in-flight turn

### Authentication

Localhost only. No auth in v0.4.0. (Tauri's WebView is the only client when v0.4.1 lands.) If a future operator binds to non-localhost they must opt in via `vebond.allow_remote_bind: true` and supply an auth token.

---

## 4. Frontend architecture

### Stack
- **Vite** — build tool (faster than CRA, native ESM)
- **React 18** — UI framework
- **TypeScript** — types everywhere
- **Tailwind CSS** — utility-first; pairs naturally with Norse-aesthetic custom theme tokens
- **Zustand** — minimal state store (smaller than Redux; right for a single ceremony's state)
- **clsx** — conditional class composition

### NOT included
- No styled-components / emotion (Tailwind covers it)
- No Redux / RTK
- No three.js (no in-window VRM per manifesto)
- No router (single-page app for v0.4.0; v0.4.x may add multiple panels)

### Component tree (proposed; Architect locks at scaffold)

```
<App>
  <ToastSystem />
  <SummoningCircle>          ← center stage; the visual heart
    <LifecyclePulse />       ← the ring's glow + breathing animation
    <CenterCrest />          ← the Eld-flame or sigil
  </SummoningCircle>
  <SidePanel orientation="left">
    <LayerStatusPanel>       ← Bifröst / Tunga / Hlust health
      <LayerStatusItem />×N
    </LayerStatusPanel>
    <SenseTogglePanel />     ← read-only in v0.4.0; toggle in v0.4.x
  </SidePanel>
  <SidePanel orientation="right">
    <ChatPanel>
      <ChatHistory />
      <ChatInput />          ← text input; voice cue when Hlust active
    </ChatPanel>
  </SidePanel>
  <BottomBar>
    <LightButton />          ← the Light-the-Candle action
    <ExtinguishButton />     ← the Slokna action
    <ConnectionIndicator />  ← WS connected / disconnected
  </BottomBar>
</App>
```

---

## 5. Roadmap slot (from `docs/ROADMAP.md`)

> **v0.4 — Summonarhringar (Summoning Circle)** — L4 Vébond / Eldahús — Tauri React frontend — 2-3 weeks

### v0.4.0 exit criteria (this session)
- `heretic serve` command starts a localhost WebSocket server
- `frontend/` runs via `npm run dev`
- React app connects to backend, displays lifecycle state, sends light/extinguish/send_message commands
- Norse dark theme renders per AESTHETIC.md
- Chat panel streams agent token deltas in real time
- Layer-status panel reflects actual L1/L2 health
- Light button triggers Kynding → Tengsl ceremony; Extinguish triggers Slokna
- Connection-indicator shows WS state
- Test count ≥370 (Python 339 + 30+ new Python; ~20+ new frontend Vitest tests)
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

### v0.4.1 exit criteria (deferred, separate session)
- Rust + Cargo installed
- `src-tauri/` directory with `tauri.conf.json` + Rust main crate
- Tauri builds successfully on Windows 11 + WebView2
- Native window opens; React frontend renders inside it
- Tauri spawns Python `heretic serve` as sidecar (bundled or dev-detected)
- `cargo tauri build` produces a .msi installer

---

## 6. Mythic Engineering wave plan — COMPLETE

Same protocol as v0.1+v0.2+v0.3. Six roles, three waves, plus close-out.

### Wave 1 — parallel (no inter-dependencies) — COMPLETE (`e3874fd`, `b3209db`, `824da42`)
- ~~**Cartographer** (Védis Eikleið) — DATA_FLOW.md §4.8 + §13 + SYSTEM_OVERVIEW~~ Done `b3209db`
- ~~**Skald** (Sigrún Ljósbrá) — THE_FIRST_FACE.md (fifth panel)~~ Done `e3874fd`
- ~~**Architect** (Rúnhild Svartdóttir) — vebond/ scaffold + frontend/ 44-file tree + IPC_PROTOCOL.md + grunnr/config.py VebondConfig + pyproject [serve] extra~~ Done `824da42`

### Wave 2 — sequential — COMPLETE (`9cc4b62`, `3838b25`, `d9186ab`, `5ead989`)
- ~~**Forge** (Eldra Járnsdóttir) — serve.py + EventBus + CLI serve + ~85 Python tests~~ Done `9cc4b62`
- ~~**Forge** — ws-client.ts + ceremony.ts Zustand store~~ Done `3838b25`
- ~~**Forge** — 13 Eldahús React components + 56 frontend Vitest tests~~ Done `d9186ab`
- ~~**Auditor** (Sólrún Hvítmynd) — AUDIT_v0.4_SUMMONING_CIRCLE.md (PASS WITH CONCERNS, 0 blockers, 1 SERIOUS, 3 NOTABLE)~~ Done `5ead989`

### Wave 3 — cleanup — COMPLETE (`edf68ee`, `08890ee`)
- ~~**Architect** — N-1 (health field added to IPC_PROTOCOL.md §1) + N-3 (§8 Vocabulary Bridge mapping table)~~ Done `edf68ee`
- ~~**Forge** — S-1 (turn_id linking — store now uses local activeTurnId for DOM lookup; streaming messages finalize correctly) + N-2 (CSS @import order fixed)~~ Done `08890ee`

### Close-out — COMPLETE
- ~~**Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 5 + update this TASK file + memory refresh~~ Done 2026-05-07

---

## 7. Files to be created (Forge target list)

### Python side
```
src/heretic/vebond/
  __init__.py
  INTERFACE.md
  config_model.py     # VebondConfig
  errors.py           # VebondError, BindError, etc.
  protocol.py         # Pydantic models for all events + commands
  serve.py            # FastAPI app + WebSocket endpoint + EventBus
tests/
  test_vebond_config.py
  test_vebond_protocol.py
  test_vebond_serve.py
```

### Frontend side
```
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  tailwind.config.js
  postcss.config.js
  index.html
  README_DEV.md
  src/
    main.tsx
    App.tsx
    types/
      ipc.ts                    # mirror Python protocol.py
    api/
      ws-client.ts              # typed WS client
      events.ts                 # event handler registry
    store/
      ceremony.ts               # zustand store
    components/
      SummoningCircle.tsx
      LifecyclePulse.tsx
      CenterCrest.tsx
      LayerStatusPanel.tsx
      LayerStatusItem.tsx
      SenseTogglePanel.tsx
      ChatPanel.tsx
      ChatHistory.tsx
      ChatInput.tsx
      LightButton.tsx
      ExtinguishButton.tsx
      ConnectionIndicator.tsx
      ToastSystem.tsx
    styles/
      theme.css                 # CSS variables matching AESTHETIC.md
      index.css
  tests/
    components.test.tsx
    ws-client.test.ts
    ceremony-store.test.ts
```

---

## 8. Operational rules (carried, immutable)

- Branch: `development` only
- Push frequently
- No absolute paths
- No hardcoded settings — port/host/etc. via `heretic.yaml`
- Modular, fault-tolerant, cross-platform
- No emoji in code or docs
- Type hints (Python) + types (TypeScript) everywhere
- Each subagent commits with their own attribution line
- After EVERY completed phase: update this TASK file + memory immediately

---

## 9. v0.3.x backlog (carried from v0.3 close — none open)

v0.3 closed clean. No carryforward items.

---

## 10. v0.4.x / v0.4.1 backlog (forward-looking — updated 2026-05-07)

- **v0.4.1 Tauri shell wrap** — requires Rust install first: `winget install Rustlang.Rust.MSVC` or rustup. Once installed: `src-tauri/` directory, `tauri.conf.json`, Rust main crate, Tauri spawns Python `heretic serve` as sidecar, WebView2 on Windows 11, native window with Norse chrome, `.msi` build. The React frontend does not change — Tauri is only the frame.
- **v0.4.x sense toggles** — `toggle_sense` currently returns a warning event (correct deferred behavior per spec). Real toggle requires `heretic.yaml` rewrite + reload mechanism. The IPC command schema is already in place.
- **v0.4.x voice waveform widget** — `hlust.activity.level_db` is already in the protocol and the store. Only the frontend visualizer widget is missing.
- **v0.4.x `ceremony_button_confirm` wire** — config key exists (`VebondConfig.ceremony_button_confirm` defaults to `true`) but is never exposed to the frontend over the WS protocol. ExtinguishButton sends without confirmation in v0.4.0. Either expose the flag or remove from spec until wired.
- **v0.4.x NIT X-1** — heartbeat sends a text frame `{"type":"_ping"}` instead of a WebSocket control PING frame. Functionally fine for browser and Tauri WebView; spec says "ping frame." Low priority.
- **v0.4.x NIT X-2** — reconnect backoff max is 16s in code; DATA_FLOW.md §4.8.4 says 30s. Align code or doc. Low priority.
- **v0.4.x light/dark theme switch** — light theme deferred per AESTHETIC.md note.

---

## 11. How to resume in a future session (updated 2026-05-07 — v0.4.0 complete)

v0.4.0 is sealed. The next session begins one of two paths:

### Path A — v0.4.1 Tauri Wrap (if Rust is now installed)
1. Confirm: `rustc --version` and `cargo --version` both return a version string
2. Read `docs/BODY_MANIFESTO.md` and `docs/architecture/IPC_PROTOCOL.md`
3. Read `docs/audit/AUDIT_v0.4_SUMMONING_CIRCLE.md §H-3` (Tauri WebView compatibility notes — no blocking issues found)
4. Run `git log --oneline -5` to confirm HEAD is `08890ee` or later
5. Open a new task file `TASK_HERETIC_v0.4.1_TAURI_WRAP.md` before writing any code
6. Build `src-tauri/` skeleton (Architect), then wire sidecar spawn, then build .msi (Forge), then audit

### Path B — v0.5 First Sight (screen capture, L3 Sjón)
1. Read `docs/BODY_MANIFESTO.md` and `docs/NAMING.md` (L3 = Sjón, sense = Auga)
2. Read `docs/architecture/SENSE_CONTRACTS.md §Auga`
3. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
4. Run `git log --oneline -5` and `python -m pytest tests/ -q` to verify clean baseline
5. Open `TASK_HERETIC_v0.5_FIRST_SIGHT.md` before any code
6. The choice of path is Volmarr's

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*v0.4 Summoning Circle — when the body learns to be seen.*
