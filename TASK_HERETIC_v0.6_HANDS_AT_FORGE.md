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

**Phase:** v0.5.1 SHIPPED + AUDITED + CLEANED. Test baseline: Python 569 + frontend 78 = 647.

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
- ⏳ `src/heretic/skilningr/` — L5 Skilningr substrate (the sense hub layer; v0.6.0 hosts only Smiðja but designed to host more senses later)
  - `__init__.py` exports
  - `INTERFACE.md` module contract
  - `config_model.py` — SkilningrConfig + SkilningrSenseConfig dataclasses
  - `errors.py` — SkilningrError, SenseUnavailableError, ToolDispatchError
  - `dispatcher.py` — ToolDispatcher: routes incoming tool_call (OpenAI format) to registered sense; returns tool_result
  - `senses/smidja/` — first sense subpackage
    - `__init__.py`
    - `INTERFACE.md` 
    - `client.py` — BrunhandHttpClient (httpx-based wrapper of Seidr-Smidja's Brúarhönd HTTP API at `/v1/brunhand/*`)
    - `tools.py` — ToolDefinition list (OpenAI tools schema for screenshot, click, type, hotkey, vroid_open, vroid_export)
    - `sense.py` — SmidjaSense orchestrator
    - `errors.py` — SmidjaError + child types
- ⏳ Bifröst client extension — `send_message()` accepts the existing `tools` array (already wired), new path: when streaming response yields tool_call deltas, accumulate them and emit a typed event for the CLI to dispatch
- ⏳ CLI integration — at TENGSL, build the tool registry from enabled senses; pass `tools` to send_message; on tool_call, dispatch via ToolDispatcher → Smiðja → Brúarhönd HTTP; feed result back as `tool_result` user-role message; loop until agent terminates with normal stop
- ⏳ vebond/protocol.py — new event `sense.tool_call` (state, sense, tool_name, call_id) so the UI shows what tools the agent is invoking
- ⏳ Frontend — LayerStatusPanel adds Smiðja row (Eld-amber accent for "active hand" semantics? Or new color from AESTHETIC.md) showing tool_call activity
- ⏳ heretic.example.yaml — new `skilningr:` block with `smidja:` sub-block (endpoint, token_env, enabled, host_name)
- ⏳ Tests — 35+ new Python tests (mocked Brúarhönd HTTP, dispatcher routing, tool-call accumulation, capability gating) + 3+ frontend tests; total target 607+ Python + 81+ frontend = 688+
- ⏳ docs/vision/THE_FIRST_HAND.md — Skald essay (seventh panel of vision cycle)
- ⏳ docs/cartography/DATA_FLOW.md §4.11 — tool flow diagram

### v0.6.x backlog (forward — NOT v0.6.0 scope)
- v0.6.1: Forge headless Blender path (the second Seidr-Smidja half); separate sense `smidja.blender_render` or distinct sense
- v0.6.2: more senses (filesystem, terminal, browser)
- v0.6.x: native MCP server hosting (instead of OpenAI tool-use); when agent supports MCP client

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

## 6. Mythic Engineering wave plan

Standard pattern (similar to v0.5; full six roles since this is a NEW faculty).

### Wave 1 — parallel (no inter-dependencies)
- **Cartographer** (Védis Eikleið) — `docs/cartography/DATA_FLOW.md §4.11 "Tool flow (v0.6 — outbound, on agent demand)"` showing: agent emits tool_call delta → Bifröst accumulator → ToolDispatcher → SmidjaSense → BrunhandHttpClient → Tailscale → Brúarhönd daemon → VRoid Studio host → response → tool_result back to agent. Add §16 Smiðja component diagram. Document the multi-round loop and the cap.
- **Skald** (Sigrún Ljósbrá) — `docs/vision/THE_FIRST_HAND.md` — seventh panel (after WHY_HERETIC, CEREMONY_NARRATIVE, THE_FIRST_VOICE, THE_FIRST_LISTENING, THE_FIRST_FACE, THE_FIRST_SIGHT). What it means for the body to act, not only perceive. Agency vs receptivity. The hand that reaches into the world the user shares with the spirit. The covenant of consent for action (configured opt-in, audit log). 2500-3500 words.
- **Architect** (Rúnhild Svartdóttir) — scaffold:
  - `src/heretic/skilningr/` — L5 Skilningr substrate (dispatcher, registry, errors, INTERFACE.md, config_model)
  - `src/heretic/skilningr/senses/smidja/` — Smiðja sense (BrunhandHttpClient skeleton, ToolDefinition list, sense.py orchestrator skeleton, errors.py)
  - Update grunnr/config.py with SkilningrConfig consolidation (Approach B)
  - Update vebond/protocol.py with `sense.tool_call` event
  - Update IPC_PROTOCOL.md with new event + naming bridge entries
  - Update LAYER_INTERFACES.md §L5 with Smiðja-specific notes (the first sense within Skilningr)
  - heretic.example.yaml — new `skilningr:` block
  - Skip-marked placeholder tests (~20)
  - Confirm clean import; 569 Python tests still passing

### Wave 2 — sequential
- **Forge** (Eldra Járnsdóttir) — implement:
  - BrunhandHttpClient (httpx async; bearer-token auth; per-endpoint typed methods; error mapping; timeouts from config)
  - ToolDefinition list — exactly 6 OpenAI-format tool schemas matching Brúarhönd primitives
  - SmidjaSense (open/close, dispatch tool_call to client method, encode result)
  - ToolDispatcher (route by tool-name prefix; aggregate tool_calls across deltas; emit `sense.tool_call` events)
  - Bifröst extension — detect tool_call deltas in stream; accumulate; emit per complete call; loop until agent stops or max_tool_call_rounds reached
  - CLI integration — register tools at TENGSL when enabled; pass tools list to send_message; route tool_calls; loop multi-round
  - Frontend LayerStatusPanel Smiðja row
  - Real Python tests (mocked Brúarhönd HTTP via respx OR httpx mock; mocked dispatcher; tool-call streaming) + frontend Vitest
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.6_HANDS_AT_FORGE.md`. Verify: tool schema matches OpenAI spec; tool_call routing correct; multi-round capped at max_tool_call_rounds; auth header set; bearer token sourced from env (not config plain text); failure modes (Brúarhönd down, auth fail, timeout, malformed response) all return tool_result with error JSON, never crash turn; capability gating; cross-platform; INTERFACE.md matches code.

### Wave 3 — cleanup (only if Auditor finds notables)

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 9 + update this TASK file + memory refresh.

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
- v0.4.1 first compile (awaits operator linker install)
- v0.5.x: webcam (v0.5.2), privacy masks (v0.5.3)

### v0.6.x backlog (forward)
- v0.6.1: Forge dispatch — headless Blender renders via Seidr-Smidja's Forge HTTP path (Mode B in Brúarhönd's three modes)
- v0.6.2: filesystem sense, terminal sense, browser sense (per L5 sense hub design)
- v0.6.x: native MCP server hosting (instead of OpenAI tool_use); when agent has MCP client

---

## 10. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. Read `docs/audit/AUDIT_v0.6_HANDS_AT_FORGE.md` if it exists
4. Run `git log --oneline -15` and `git status` in `C:/Users/volma/runa/HERETIC`
5. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
6. Continue from the first unchecked deliverable in §2

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.6 Hands at the Forge — when the body learns to act.*
