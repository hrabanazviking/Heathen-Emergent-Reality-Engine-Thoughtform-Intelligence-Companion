# TASK — HERETIC v0.6.1 FORGE DISPATCH

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.5.2 Webcam shipped + audited + cleaned at `b42294e`)

> **Mode: extension of v0.6.** Adds the second half of Seidr-Smidja integration: the Forge dispatch (headless Blender pipeline) alongside Brúarhönd's live GUI control. Slim wave plan: no Skald.

---

## 1. Task scope

v0.6 integrated **Brúarhönd** (live VRoid Studio GUI control). v0.6.1 integrates **Forge dispatch** (headless Blender pipeline) — the second half of Seidr-Smidja's three modes.

Per Seidr-Smidja's Brúarhönd README:
- Mode A — Brúarhönd only (live GUI) — DONE in v0.6
- **Mode B — Forge only (headless Blender) — TARGET for v0.6.1**
- Mode C — both arms — naturally available once both halves wired

The agent receives 1-3 new tools from the workshop:
- `smidja.forge_build_avatar` — POST a Loom spec; returns avatar id + render artifacts
- `smidja.forge_get_avatar` — GET avatar metadata by id
- `smidja.forge_inspect_avatar` — POST avatar id; returns inspect output (ground-truth schema validation)
- (optional) `smidja.forge_list_assets` — GET available asset packs

Both Brúarhönd and Forge live under the same Smiðja sense — the workshop holds both the live GUI and the headless render. Tool names disambiguate by `forge_` prefix on the new tools.

---

## 2. Current status — 2026-05-08

**Phase:** v0.5.2 SHIPPED + AUDITED + CLEANED at `b42294e`. Test baseline: 750 Python + 91 frontend = 841.

### v0.6.1 deliverables
- ⏳ `src/heretic/skilningr/senses/smidja/forge_client.py` — NEW; ForgeHttpClient wrapping Seidr-Smidja's Straumur REST API (`/v1/avatars`, `/v1/inspect`, `/v1/assets`)
- ⏳ Extend `SmidjaConfig` with `forge:` sub-block — `enabled`, `endpoint` (default `http://127.0.0.1:8765`), `token_env` (optional — Straumur may not require auth on localhost), `request_timeout_seconds` (default 120 — Blender renders take time)
- ⏳ Extend `tools.py` `SMIDJA_TOOL_DEFINITIONS` with 3 new tools (`smidja.forge_build_avatar`, `smidja.forge_get_avatar`, `smidja.forge_inspect_avatar`)
- ⏳ Extend `SmidjaSense.dispatch_tool_call` to route the new tools to ForgeHttpClient
- ⏳ Lifecycle: SmidjaSense.open() probes both Brúarhönd /health AND Forge /health (when respective halves enabled); each half degrades independently
- ⏳ Tests — 25+ new Python tests; total target 775+ Python
- ⏳ docs/cartography/DATA_FLOW.md §4.11 — extend with Forge dispatch sub-section
- ⏳ heretic.example.yaml — add `forge:` sub-block under `skilningr.smidja:`

### What v0.6.1 does NOT add
- Mode C orchestration (both arms in one tool call) — agent can sequence Brúarhönd + Forge calls itself; explicit composition is v0.6.x
- Forge-side render artifact serving (HERETIC just receives URLs/IDs; user fetches from Seidr-Smidja directly)
- Loom spec generation/validation — agent provides full Loom specs as JSON

---

## 3. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Same sense or new sense | **Same sense (Smiðja)** | Workshop holds both live GUI + headless render conceptually; cleaner UX; tool names disambiguate via `forge_` prefix |
| Separate HTTP client | **Yes — ForgeHttpClient parallel to BrunhandHttpClient** | Different endpoints, different auth, different timeout profile (Blender renders slow); cleaner separation |
| Tool naming | `smidja.forge_<action>` | Two-part `smidja.<action>` convention preserved; `forge_` is a sub-prefix within the sense |
| Independent lifecycle | Each half (Brúarhönd, Forge) opens/closes independently | If Forge daemon unavailable, Brúarhönd tools still work; vice versa |
| Auth | Optional bearer token (Straumur may not require on localhost) | Mirror Brúarhönd's env-var pattern; allow None for local dev |
| Timeout | 120s default for renders | Blender renders take time; per-call timeout override available |
| Failure mode | Forge unavailable → Forge tools degrade silently to error tool_results; Brúarhönd tools continue | Per RULES.AI fault tolerance |

---

## 4. Seidr-Smidja Forge HTTP API

Per `runa/Seidr-Smidja/src/seidr_smidja/bridges/straumur/api.py` (verify at scaffold time):

| Path | Method | Purpose |
|---|---|---|
| `/v1/avatars` | POST | Build avatar from Loom spec; returns avatar id + status |
| `/v1/avatars/{id}` | GET | Get avatar metadata + render artifact URLs |
| `/v1/inspect` | POST | Inspect avatar (validate schema, return diagnostics) |
| `/v1/assets` | GET | List available asset packs |
| `/health` | GET | Liveness (typically unauthenticated) |

Architect MUST verify these against the actual Seidr-Smidja Straumur api.py before locking the schema; the Brúarhönd v0.6 wave caught FIVE TASK §4 discrepancies — same care applies here.

---

## 5. Mythic Engineering wave plan (slim)

### Wave 1 — parallel
- **Cartographer**: extend `docs/cartography/DATA_FLOW.md §4.11` with Forge dispatch sub-section §4.11.7; update §16 component diagram with ForgeHttpClient parallel to BrunhandHttpClient inside Smiðja sense
- **Architect**: scaffold `forge_client.py`; extend SmidjaConfig with `forge:` sub-block + ForgeConfig dataclass; extend `tools.py` SMIDJA_TOOL_DEFINITIONS with 3 new tool entries; extend SmidjaSense for dual-half lifecycle (each half opens independently); update INTERFACE.md; verify Seidr-Smidja Straumur API contract in source; placeholder tests

### Wave 2
- **Forge**: implement ForgeHttpClient (httpx async, /v1/avatars POST + GET, /v1/inspect POST, /v1/assets GET, /health probe); SmidjaSense.dispatch routing for new tools; CLI integration unchanged (already routes through dispatcher); 25+ tests
- **Auditor**: AUDIT_v0.6.1_FORGE_DISPATCH.md; verify dual-half independence (Brúarhönd alone, Forge alone, both); auth invariant for token (env-var-only); failure modes; cross-platform; OpenAI tool schema correctness for new tools

### Wave 3 — cleanup if needed

### Close-out
- **Scribe**: DEVLOG entry 11 + TASK update + memory refresh

---

## 6. Files to be created/extended

```
src/heretic/skilningr/senses/smidja/
  forge_client.py       NEW — ForgeHttpClient (httpx async, Seidr-Smidja Straumur REST)
  config_model.py       extend — ForgeConfig added; SmidjaConfig.forge: ForgeConfig
  tools.py              extend — 3 new tools added to SMIDJA_TOOL_DEFINITIONS
  sense.py              extend — dual-half lifecycle (Brúarhönd, Forge open independently); dispatch routing for new tools
  errors.py             extend — ForgeError, ForgeUnreachableError, ForgeTimeoutError, ForgeValidationError
  INTERFACE.md          extend with Forge dispatch section
tests/
  test_forge_client.py  NEW — 12+ tests
  test_smidja_sense.py  extend — dual-half lifecycle + new-tool dispatch tests
  test_smidja_tools.py  extend — schema tests for 3 new tools
heretic.example.yaml    extend — skilningr.smidja.forge: block
docs/cartography/DATA_FLOW.md §4.11 extend
```

---

## 7. v0.6.1 exit criteria
- 3 new Forge tools exposed to agent in tools array when `skilningr.smidja.forge.enabled: true`
- Brúarhönd half + Forge half open/close independently
- Each half degrades silently if its daemon is unreachable
- Forge tool calls produce well-formed tool_results matching OpenAI spec
- Test count ≥775 Python
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 8. Backlog forward
- v0.5.3 frontend Sjón webcam sub-badge (carry from v0.5.2)
- v0.5.x periodic webcam + multi-camera + privacy masks
- v0.6.2 more senses (filesystem, terminal, browser) — NEXT after v0.6.1
- v0.6.x native MCP server hosting
- v0.7 Mímisbrunnr starter pack
- v0.4.1 first compile (awaits operator linker install)

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.6.1 — when the workshop's headless forge runs alongside the live GUI.*
