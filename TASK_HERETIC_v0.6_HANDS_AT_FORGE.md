# TASK — HERETIC v0.6 HANDS AT THE FORGE

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-08** (immediately after v0.5.1 Periodic Sight shipped + audited + cleaned)

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1), speak (v0.2), listen (v0.3), be seen (v0.4.0), and see (v0.5+v0.5.1) to a body that can also **act** — the body gains its first hand.

L5.5 **Smiðja** is the agent's hand at the forge: an MCP-via-tool-use wrapper around Seidr-Smidja's Brúarhönd HTTP daemon (running on the same machine OR on a Tailscale-reachable VRoid host). The agent's tool calls become real GUI primitives — screenshots, clicks, hotkeys, VRoid Studio open/export, and (in v0.6.1) headless Blender renders.

The canonical contract for L5.5 lives in `docs/architecture/LAYER_INTERFACES.md §L5` and `docs/architecture/SENSE_CONTRACTS.md §Smiðja`. Seidr-Smidja's Brúarhönd is shipped + 489-test green at `runa/Seidr-Smidja` (HEAD `e3f126d`); HERETIC's job is to wrap its surface, not reimplement it.

---

## 2. Current status — 2026-05-08

**Phase:** v0.6 SHIPPED + AUDITED + CLEANED 2026-05-08. HEAD post-Wave-3-cleanup: `cc8a42d`. Tests: 691 Python + 91 frontend = 782.

### Done in v0.1+v0.2+v0.3+v0.4+v0.5+v0.5.1 (recap)
- v0.1: L0 Grunnr + L1 Bifröst + CLI
- v0.2: L2 Tunga (TTS)
- v0.3: L2 Hlust (STT)
- v0.4.0: L4 Vébond Eldahús (UI substrate)
- v0.4.1: src-tauri/ scaffold (PRE-STAGED; first compile awaits operator-installed linker — Rust 1.95.0 installed, MSVC link.exe + GNU dlltool both unavailable)
- v0.5: L3 Sjón on-demand sight
- v0.5.1: L3 Sjón periodic + ring buffer + multi-monitor

Five primary faculties live; the body sees and is seen.

### v0.6 deliverables (this milestone — scope: v0.6.0 Brúarhönd integration only)
- ~~⏳ `src/heretic/skilningr/` — L5 Skilningr substrate~~ **Done 2026-05-08 — `b4040ef` (scaffold) + `1214e5c` (implementation)**
  - ~~`__init__.py` exports~~
  - ~~`INTERFACE.md` module contract~~
  - ~~`config_model.py` — SkilningrConfig + SkilningrSenseConfig dataclasses~~
  - ~~`errors.py` — SkilningrError, SenseUnavailableError, ToolDispatchError~~
  - ~~`dispatcher.py` — ToolDispatcher~~
  - ~~`senses/smidja/` — first sense subpackage~~ **Done 2026-05-08 — `b4040ef` (scaffold) + `1214e5c` (implementation)**
    - ~~`__init__.py`~~
    - ~~`INTERFACE.md`~~
    - ~~`client.py` — BrunhandHttpClient~~ (5 TASK §4 path discrepancies corrected per Architect probe)
    - ~~`tools.py` — 6 ToolDefinitions~~ (locked at scaffold; 12 tests pass immediately)
    - ~~`sense.py` — SmidjaSense orchestrator~~
    - ~~`errors.py` — SmidjaError + child types~~
- ~~⏳ Bifröst client extension~~ **Done 2026-05-08 — `75811a2`** (structured JSON detection replacing string heuristic per Wave 3 C-3 fix — `cc8a42d`)
- ~~⏳ CLI integration — multi-round tool dispatch loop~~ **Done 2026-05-08 — `75811a2` + serve.py wire `cc8a42d`**
- ~~⏳ vebond/protocol.py — `sense.tool_call` event~~ **Done 2026-05-08 — `b4040ef`**
- ~~⏳ Frontend — LayerStatusPanel Smiðja row (Eld-amber accent)~~ **Done 2026-05-08 — `b97e67e`**
- ~~⏳ heretic.example.yaml — `skilningr:` block~~ **Done 2026-05-08 — `b4040ef`**
- ~~⏳ Tests — 35+ Python + 3+ frontend~~ **Done 2026-05-08 — +122 Python, +13 frontend. Total 782.**
- ~~⏳ docs/vision/THE_FIRST_HAND.md~~ **Done 2026-05-08 — `b324544`**
- ~~⏳ docs/cartography/DATA_FLOW.md §4.11~~ **Done 2026-05-08 — `fedae33`** (§4.11 + §16 + 7 failure modes)

### v0.6.x backlog (forward — NOT v0.6.0 scope)
- v0.6.1: Forge dispatch — headless Blender renders via Seidr-Smidja's Forge HTTP path (Mode B in Brúarhönd's three modes)
- v0.6.2: more senses (filesystem, terminal, browser)
- v0.6.x: native MCP server hosting (instead of OpenAI tool_use); when agent has MCP client

### Constraints carried
- All settings via heretic.yaml
- No absolute paths
- Cross-platform
- Modular, fault-tolerant, type-hinted
- No emoji
- **Privacy invariant for Smiðja: no caching of remote screenshots beyond what Sjón ring buffer already does; tool_call audit log is in-memory only**

---

## 3. Architectural decisions for v0.6.0

| Decision | Choice | Rationale |
|---|---|---|
| Tool transport | OpenAI tool_use (not MCP) | Works with v0.1 Bifröst already; MCP server hosting is v0.6.x stretch. Bifröst already accepts `tools` array (audit C-Q-C2). |
| HTTP client to Brúarhönd | httpx async (reuse Bifröst pattern) | Already a dependency; consistent. |
| Tool naming convention | `smidja.<action>` per SENSE_CONTRACTS.md two-part format | Sealed at v0.0 audit A-2. |
| Sense registry | dict in SkilningrConfig + ToolDispatcher | Simple dispatch by tool-name prefix |
| Auth | bearer token from env var (matches Brúarhönd) | Brúarhönd's existing model |
| Tailscale routing | endpoint string honors Tailscale hostnames + IPs | No special handling — httpx connects normally |
| Capability flag | `?tool_use` (already in protocol per v0.0 audit) | Existing flag; verify CLI honors it |
| Tool-call streaming | accumulate tool_call deltas in Bifröst client; emit one event per complete call | Matches OpenAI stream contract |
| Multi-call rounds | Loop tool_call → tool_result → next response, with `max_tool_call_rounds: 5` cap from BifrostConfig | Existing config field; honor it |
| Result format | `{"tool_call_id": "...", "role": "tool", "content": "<json string>"}` per OpenAI spec | Standard |
| Smiðja screenshot bytes | base64-encoded PNG returned in tool_result content (mirror Sjón's image format) | Reuse Sjón frame format; mention in INTERFACE.md |
| Failure mode | Tool dispatch failure → return tool_result with error JSON; do NOT crash turn | Per RULES.AI fault tolerance |
| Skald essay | YES (THE_FIRST_HAND) | New faculty — agent gains agency — major threshold worthy of seventh vision-cycle panel |

---

## 4. Brúarhönd HTTP API (probe expected; verify at scaffold time)

Per Seidr-Smidja's `docs/features/brunhand/README.md` and `src/seidr_smidja/brunhand/daemon/`:

| Path | Method | Purpose |
|---|---|---|
| `/v1/brunhand/health` | GET (no auth) | Liveness |
| `/v1/brunhand/capabilities` | GET (auth) | List of supported primitives |
| `/v1/brunhand/screenshot` | POST (auth) | PNG bytes |
| `/v1/brunhand/click` | POST (auth) | x, y, button |
| `/v1/brunhand/type` | POST (auth) | text |
| `/v1/brunhand/hotkey` | POST (auth) | keys list |
| `/v1/brunhand/vroid-open` | POST (auth) | project path |
| `/v1/brunhand/vroid-export` | POST (auth) | output path |

Auth: `Authorization: Bearer <token>` header.

The Architect should probe the live daemon (if running) OR cross-reference Seidr-Smidja's `src/seidr_smidja/brunhand/daemon/INTERFACE.md` to lock the schema before Forge codes the client.

---

## 5. Roadmap slot (from `docs/ROADMAP.md`)

> **v0.6 — Hands at the Forge** — Blender MCP + Seidr-Smidja Brúarhönd integration — L5.5 — 2 wk

### v0.6.0 exit criteria (this session)
- `heretic light` with `skilningr.smidja.enabled: true` AND agent supporting `?tool_use` exposes the 6 Brúarhönd tools to the agent in the `tools:` array
- Agent emits `tool_call` for `smidja.screenshot` (or any other) → CLI routes through Skilningr → Smiðja → Brúarhönd HTTP → result returned as tool_result
- Multi-round tool-use respected (max_tool_call_rounds cap)
- Configurable via `heretic.yaml` `skilningr.smidja.*` keys
- Graceful degradation if Brúarhönd unreachable (tool returns error JSON; turn continues)
- Test count ≥607 Python + 81 frontend = 688 total
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 6. Mythic Engineering wave plan — COMPLETE

### Wave 1 — COMPLETE (`b324544`, `fedae33`, `b4040ef`)
- **Cartographer** (Védis Eikleið) — `b4040ef` — §4.11 tool flow + §16 component diagram + 7 failure modes + auth invariant confirmation + API discrepancy flag (5 corrected)
- **Skald** (Sigrún Ljósbrá) — `b324544` — THE_FIRST_HAND seventh vision panel; receive/express/act triad named complete
- **Architect** (Rúnhild Svartdóttir) — `b4040ef` — full skilningr/ + senses/smidja/ scaffold; 5 TASK §4 discrepancies catalogued + corrected; 6 ToolDefinitions locked; Approach B config consolidation; SenseToolCall IPC event; LAYER_INTERFACES.md §L5.5; heretic.example.yaml skilningr block

### Wave 2 — COMPLETE (`1214e5c`, `75811a2`, `b97e67e`)
- **Forge** (Eldra Járnsdóttir) — BrunhandHttpClient + ToolDispatcher + SmidjaSense + CLI multi-round loop + frontend Smiðja row (Eld accent)
- **Auditor** (Sólrún Hvítmynd) — `b17c611` — PASS WITH CONCERNS: 0 blockers, 0 SERIOUS, 2 NOTABLE (N-1 serve.py; C-3 string heuristic), 1 NIT (X-1 wait_timeout). Auth invariant CLEAN. All 5 API discrepancies honored.

### Wave 3 — COMPLETE (`cc8a42d`)
- **Forge** (Eldra Járnsdóttir) — N-1 (serve.py Smiðja wire + event_bus.publish), C-3 (structured JSON parsing + 3 boundary tests), X-1 (2 wait_timeout envelope tests). 691 Python + 91 frontend = 782. 0 findings.

### Close-out — COMPLETE (this commit)
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 9 + this TASK update + memory refresh.

---

## 7. Files to be created (Forge target list)

### Python side
```
src/heretic/skilningr/
  __init__.py
  INTERFACE.md
  config_model.py     # SkilningrConfig + SkilningrSenseConfig
  errors.py
  dispatcher.py       # ToolDispatcher
  senses/
    __init__.py
    smidja/
      __init__.py
      INTERFACE.md
      client.py       # BrunhandHttpClient
      tools.py        # 6 OpenAI ToolDefinition entries
      sense.py        # SmidjaSense
      errors.py
tests/
  test_skilningr_config.py
  test_skilningr_dispatcher.py
  test_smidja_client.py
  test_smidja_tools.py
  test_smidja_sense.py
  test_cli_tool_use.py
```

### Existing files Forge updates (additive)
- `src/heretic/grunnr/config.py` — SkilningrConfig consolidation
- `src/heretic/bifrost/client.py` — tool_call delta accumulator + emit
- `src/heretic/cli.py` — tool registry + multi-round loop + dispatch
- `src/heretic/vebond/protocol.py` — `sense.tool_call` event
- `src/heretic/vebond/serve.py` — emit sense.tool_call at dispatch milestones
- `frontend/src/types/ipc.ts` — mirror sense.tool_call
- `frontend/src/store/ceremony.ts` — handler
- `frontend/src/components/LayerStatusPanel.tsx` — Smiðja row
- `pyproject.toml` — no new core deps (httpx already present); no new extra needed unless Brúarhönd needs something
- `heretic.example.yaml` — `skilningr:` block

---

## 8. Operational rules (carried, immutable)

- Branch: `development` only
- Push frequently
- No absolute paths
- No hardcoded settings — all from heretic.yaml; bearer token from env var
- Modular, fault-tolerant, cross-platform
- No emoji
- Type hints everywhere
- After EVERY completed phase: update this TASK file + memory immediately
- **Auth invariant: token comes from env var; never logged; never stored in heretic.yaml plaintext**
- **Tool result format: must match OpenAI spec (role: "tool", tool_call_id, content) so any OpenAI-compat agent can consume it**

---

## 9. Backlog carried + forward

### Pending from earlier milestones
- v0.4.1 first compile (awaits operator linker install — MSVC Build Tools or full MinGW-w64)
- v0.5.x: webcam (v0.5.2), privacy masks (v0.5.3)
- v0.5.x N-3: MssBackend cached availability (deferred from v0.5 audit)

### v0.6.x backlog (forward — all carry)
- v0.6.1: Forge dispatch — headless Blender renders via Seidr-Smidja's Forge HTTP path (Mode B in Brúarhönd's three modes); `smidja.blender_render` sense or distinct Forge sense path; gates on Seidr-Smidja v0.2 Loom→Blender translation layer
- v0.6.2: filesystem sense, terminal sense, browser sense (per L5 sense hub design; Python only, no external gates)
- v0.6.x: native MCP server hosting (instead of OpenAI tool_use); when agent has MCP client; protocol extension work required

---

## 10. How to resume after v0.6 — forward orientation

**v0.6 is fully closed. This file is a completed record. The next task file will be the authoritative resume point.**

Current state on `development`:
- HEAD: `cc8a42d` (scribe close commit follows — see latest `git log`)
- Python 691 + frontend 91 = 782 tests. 0 open findings. 0 failures.
- Primary triad (receive/express/act) complete.

**Choose one of the following next paths (Volmarr's decision):**

| Path | Task to open | First step |
|---|---|---|
| v0.6.1 Forge dispatch (headless Blender) | Open `TASK_HERETIC_v0.6.1_FORGE_DISPATCH.md` | Confirm Seidr-Smidja Loom→Blender translation layer is live; probe Forge HTTP endpoint |
| v0.7 First Drink at the Well (Mímisbrunnr) | Open `TASK_HERETIC_v0.7_MIMISBRUNNR.md` | Light tier: libzim/kiwix integration + RAG overlay for offline knowledge |
| v0.5.2 webcam | Open `TASK_HERETIC_v0.5.2_WEBCAM.md` | `SjonWebcamConfig` already declared; extend capture.py with cv2 or imageio backend |
| v0.4.1 first compile | Open existing `TASK_HERETIC_v0.4.1_TAURI_WRAP.md` | `winget install Microsoft.VisualStudio.2022.BuildTools`; then `cargo check` in `src-tauri/` |

Start any new session by:
1. Reading `docs/BODY_MANIFESTO.md` — sealed vision
2. Reading `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
3. Running `git log --oneline -10` and `git status` in `C:/Users/volma/runa/HERETIC`
4. Opening the appropriate TASK file for the chosen path

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.6 Hands at the Forge — when the body learns to act.*
