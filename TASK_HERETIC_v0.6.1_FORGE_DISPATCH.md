# TASK — HERETIC v0.6.1 FORGE DISPATCH

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.5.2 Webcam shipped + audited + cleaned at `b42294e`)

> **Closed: 2026-05-08** — SHIPPED + AUDITED + CLEANED at `5a04112`. 809 Python + 91 frontend = 900 tests. 0 open findings. See DEVLOG entry 11.

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

## 2. Final status — SHIPPED + AUDITED + CLEANED 2026-05-08

**HEAD:** `5a04112` — forge: clean v0.6.1 audit — S-1 method tests + N-1 ForgeServerError + X-1 stale test fix (Eldra Járnsdóttir)
**Test count:** 809 Python + 91 frontend = 900 total. 0 failures. 0 open audit findings.

### v0.6.1 deliverables — all complete

| Deliverable | Commit | Status |
|---|---|---|
| `forge_client.py` — ForgeHttpClient (httpx async, 5 endpoints + health, optional bearer auth) | `ea57e40` (impl) + `5a04112` (tests) | DONE |
| `SmidjaConfig.forge: ForgeConfig` — `enabled`, `endpoint`, `token_env`, `request_timeout_seconds` | `24a93da` (scaffold) | DONE |
| 3 new `SMIDJA_TOOL_DEFINITIONS` (`smidja.forge_build_avatar/get_avatar/inspect_avatar`) | `24a93da` (scaffold) | DONE |
| `SmidjaSense` dual-half lifecycle + `_route_forge` dispatch | `ea57e40` (impl) | DONE |
| `ForgeServerError` class in `errors.py` | `5a04112` (Wave 3) | DONE |
| 47 new tests (34 forge_client method-level + 13 sense dual-half dispatch) | `5a04112` (Wave 3) | DONE |
| `DATA_FLOW.md §4.11.7–9` + `§16` extended | `0349a60` (Cartographer) | DONE |
| `heretic.example.yaml` `forge:` sub-block | `ea57e40` (impl) | DONE |

### v0.6.1 wave commit log

| Commit | Role | Description |
|---|---|---|
| `1a33d97` | Runa (task open) | chore: open v0.6.1 Forge Dispatch task file |
| `0349a60` | Cartographer | cartographer: map v0.6.1 Forge dispatch + dual-half lifecycle (Védis Eikleið) |
| `24a93da` | Architect | architect: scaffold v0.6.1 ForgeHttpClient + dual-half SmidjaSense (Rúnhild Svartdóttir) |
| `ea57e40` | Forge (CAP-SALVAGE) | forge: v0.6.1 ForgeHttpClient impl + SmidjaSense dual-half (CAP-SALVAGE) |
| `24d36ce` | Auditor | audit: AUDIT_v0.6.1_FORGE_DISPATCH — PASS WITH CONCERNS |
| `5a04112` | Forge (Wave 3) | forge: clean v0.6.1 audit — S-1 method tests + N-1 ForgeServerError + X-1 stale test fix |

**Cap-incident note:** The Anthropic usage cap interrupted Wave 2 mid-test-replacement. Forge had completed the full implementation but had not yet replaced the 7 Architect `NotImplementedError` placeholder tests. The implementation was salvage-committed (`ea57e40`) with a `CAP-SALVAGE` label and the gap named explicitly. The Auditor carried doubled responsibility (standard contract verification + eye-read of the unverified implementation). Wave 3 plugged the gap with the full S-1 catalog (47 new tests). Pattern confirmed: implementation-complete salvage + thorough audit + test insertion can recover cleanly from cap-cuts.

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

## 8. Backlog forward (post-v0.6.1)

| Path | What it is | Gate |
|---|---|---|
| **v0.5.3 frontend Sjón webcam sub-badge** | Cosmetic frontend badge for active webcam source (X-1 NIT from v0.5.2 audit) | Frontend only |
| **v0.5.x periodic webcam + multi-camera + privacy masks** | Continuous webcam capture ring buffer; device selection; configurable blur/mask regions | Python + cv2 + Pillow |
| **v0.6.2 more senses** | Filesystem sense, terminal sense, browser sense — three new Skilningr senses | Python only; NEXT after v0.6.1 |
| **v0.6.x Mode C Smiðja composition** | Explicit Brúarhönd + Forge orchestration in a single multi-step tool flow | No external gate |
| **v0.6.x native MCP server hosting** | HERETIC hosts its own MCP server instead of relying on OpenAI tool_use | MCP SDK integration |
| **v0.7 Mímisbrunnr starter pack** | First Drink at the Well — offline knowledge library (libzim/kiwix + RAG overlay) | Python + libzim |
| **v0.4.1 first compile** | Tauri wrap; Rust installed; only MSVC linker absent | `winget install Microsoft.VisualStudio.2022.BuildTools` |

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.6.1 — when the workshop's headless forge runs alongside the live GUI.*
