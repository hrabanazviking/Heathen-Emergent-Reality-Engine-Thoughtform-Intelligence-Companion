# TASK — HERETIC v0.4 SUMMONING CIRCLE

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.3 First Listening shipped + audited at HEAD `77d49c9`)

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1), speak (v0.2), and listen (v0.3) to a body with a **face**.

The Summoning Circle (Eldahús — "fire-house") is L4 Vébond — the visible shell of the ceremony. It is the part of the body the user actually sees and touches: the Light-the-Candle button, the lifecycle indicator that pulses with the ceremony's state, the chat panel where the spirit's words appear, the layer-status indicators that reveal which faculties are alive.

Per `docs/architecture/CEREMONY.md`, `docs/vision/AESTHETIC.md`, and the manifesto, the canonical frontend stack is **Tauri + React**. The aesthetic is the modern longhouse in the dark — warm, purposeful, alive with bioluminescent accents (Eld/amber, Sjón-glow/blue, Mál-green/teal, Hvíla-grey/dormant).

---

## 2. Current status — 2026-05-07

**Phase:** v0.3 SHIPPED + AUDITED at `77d49c9`. v0.4 work begins now. Baseline: 339 tests passing.

### Done in v0.1+v0.2+v0.3 (recap, do not redo)
- v0.1: L0 Grunnr + L1 Bifröst + CLI shell — 121 tests
- v0.2: L2 Rödd Tunga (TTS via ChatterBox) — 224 tests
- v0.3: L2 Rödd Hlust (STT via Whisper.cpp) — 339 tests
- All audit findings closed
- The body now has both halves of the voice faculty; Samræður is two-directional voice

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

### v0.4.0 deliverables (this milestone)
- ⏳ `src/heretic/serve.py` — async backend: FastAPI or starlette + uvicorn (or aiohttp). Lightweight; reuses existing Bifröst/Tunga/Hlust.
- ⏳ `src/heretic/cli.py` — add `serve` subcommand
- ⏳ `frontend/` directory with package.json, vite.config.ts, tsconfig.json, tailwind.config.js
- ⏳ `frontend/src/` — React components: SummoningCircle, LifecyclePulse, ChatPanel, LayerStatusPanel, SenseTogglePanel, LightButton, ExtinguishButton, ToastSystem
- ⏳ `frontend/src/api/` — typed WebSocket client + TypeScript types for IPC events (mirror Python schema)
- ⏳ `frontend/tests/` — Vitest + React Testing Library
- ⏳ `docs/architecture/IPC_PROTOCOL.md` — typed event schema (Python ↔ TypeScript)
- ⏳ `docs/vision/THE_FIRST_FACE.md` — Skald essay (fifth panel)
- ⏳ `docs/cartography/DATA_FLOW.md` updated — UI ↔ backend WS path
- ⏳ Total tests ~370+ (339 baseline + 30+ Python + 20+ frontend)

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

## 6. Mythic Engineering wave plan

Same protocol as v0.1+v0.2+v0.3. Six roles, three waves, plus close-out.

### Wave 1 — parallel (no inter-dependencies)
- **Cartographer** (Védis Eikleið) — map the v0.4.0 UI ↔ backend flow in `docs/cartography/DATA_FLOW.md`. Add §"UI flow (v0.4.0 — Summoning Circle substrate)" with the WS connection lifecycle, event types, command flow, lifecycle event push pattern. Add a per-component diagram.
- **Skald** (Sigrún Ljósbrá) — `docs/vision/THE_FIRST_FACE.md` — vision essay (fifth panel of the cycle). Pair with WHY_HERETIC, CEREMONY_NARRATIVE, THE_FIRST_VOICE, THE_FIRST_LISTENING.
- **Architect** (Rúnhild Svartdóttir) — scaffold:
  - `src/heretic/vebond/__init__.py` + `INTERFACE.md` — the L4 Python module
  - `src/heretic/vebond/serve.py` — WebSocket server skeleton (NotImplementedError stubs)
  - `src/heretic/vebond/protocol.py` — typed pydantic-or-dataclass IPC event schema
  - `src/heretic/vebond/config_model.py` — VebondConfig dataclass (port, host, allow_remote_bind, etc.)
  - `src/heretic/vebond/errors.py` — error hierarchy
  - Update `src/heretic/cli.py` — add `serve` subcommand stub
  - Update `src/heretic/grunnr/config.py` — add `vebond` field to HereticConfig (importing from vebond.config_model, mirror the rodd consolidation pattern)
  - `frontend/` directory with package.json, vite.config.ts, tsconfig.json, tailwind.config.js, src/main.tsx, src/App.tsx, src/components/ skeleton, src/api/ skeleton, src/types/ipc.ts (mirror Python schema), index.html, README_DEV.md
  - `docs/architecture/IPC_PROTOCOL.md` — full typed event/command schema
  - Update `pyproject.toml` — add `[serve]` extra: `fastapi`, `uvicorn[standard]`, `websockets`
  - Skip-marked placeholder tests for both Python and frontend
  - Confirm package + frontend imports cleanly

### Wave 2 — sequential
- **Forge** (Eldra Járnsdóttir) — implement:
  - Python `serve.py` (FastAPI or starlette WebSocket server, async event bus integrating with existing Lifecycle/Bifrost/Tunga/Hlust)
  - CLI `serve` subcommand (loads config, starts server, prints URL)
  - All React components per the AESTHETIC.md theme
  - Tailwind theme tokens for Eld/Sjón-glow/Mál-green/Hvíla-grey
  - WS client in `frontend/src/api/`
  - Zustand store for ceremony state
  - Real Python tests (mocked WS clients) + frontend Vitest tests
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.4_SUMMONING_CIRCLE.md`. Verify: WS contract honoured both sides; aesthetic tokens match AESTHETIC.md spec; lifecycle events surface correctly; light/extinguish triggers the right transitions; tests cover happy path + WS disconnect + backend-down + invalid command; no absolute paths; no hardcoded settings.

### Wave 3 — cleanup (only if Auditor finds notables)
Per-finding dispatch.

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 5 + update this TASK file + memory refresh.

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

## 10. v0.4.x / v0.4.1 backlog (forward-looking)

- v0.4.1 Tauri shell wrap (requires Rust install — `winget install Rustlang.Rust.MSVC` or rustup)
- v0.4.x sense toggle: actually toggle senses via `heretic.yaml` rewrite + reload (currently read-only display)
- v0.4.x voice waveform: Hlust active level visualisation in the UI (event already in protocol, just no widget yet)
- v0.4.x light/dark theme switch (light theme deferred per AESTHETIC.md note)

---

## 11. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom (especially §2 architectural constraint about Rust)
3. Read `docs/audit/AUDIT_v0.4_SUMMONING_CIRCLE.md` if it exists (audit complete)
4. Run `git log --oneline -15` and `git status` in `C:/Users/volma/runa/HERETIC`
5. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
6. Continue from the first unchecked deliverable in §2

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*v0.4 Summoning Circle — when the body learns to be seen.*
