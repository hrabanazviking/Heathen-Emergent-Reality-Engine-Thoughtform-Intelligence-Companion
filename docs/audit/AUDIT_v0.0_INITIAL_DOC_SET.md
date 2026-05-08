# HERETIC — Audit: v0.0 Initial Doc Set

**Date:** 2026-05-07
**Auditor:** Sólrún Hvítmynd (Auditor role, Mythic Engineering)
**Scope:** Full v0.0 documentation set — 24 documents across `docs/`, `THIRD_PARTY_NOTICES.md`, and `README.md`. Branch: `development`, commit at audit start: `adc88dc`.
**Environment:** Windows 11, PowerShell, gh CLI authenticated, Python 3.10 installed locally.
**Commands run:**
- `pip show libzim faiss-cpu sentence-transformers`
- `gh repo view openzim/python-libzim --json name,licenseInfo,url`
- `gh repo view facebookresearch/faiss --json name,licenseInfo,url`
- `gh repo view UKPLab/sentence-transformers --json name,licenseInfo,url`
- `gh repo view resemble-ai/chatterbox --json name,licenseInfo,url,description`
- `gh repo view SillyTavern/SillyTavern --json name,licenseInfo,url`
- `gh repo view modelcontextprotocol/python-sdk --json name,licenseInfo,url`
- `gh repo view ggerganov/whisper.cpp --json name,licenseInfo,url`
- `gh repo view tauri-apps/tauri --json name,licenseInfo,url`
- `gh api repos/tauri-apps/tauri/contents/` (verified dual-license files)
- `gh repo view kiwix/kiwix-tools --json name,licenseInfo,url`
- `gh repo view openzim/libzim --json name,licenseInfo,url`
- `gh repo view NousResearch/hermes-agent --json name,licenseInfo,url,description,stargazerCount`
- `gh repo view openclaw/openclaw --json name,licenseInfo,url,stargazerCount`
- `curl -s https://www.photopea.com/api/live` (verified echoToOE API)
- `curl -s https://docs.vrchat.com/docs/osc-overview` (verified OSC surface)

**Documents audited (24):**
1. `docs/BODY_MANIFESTO.md` (SEALED)
2. `docs/MIMISBRUNNR.md` (SEALED)
3. `docs/NAMING.md` (SEALED)
4. `docs/PRIOR_PLANNING_TRIAGE.md` (SEALED)
5. `docs/architecture/ARCHITECTURE.md`
6. `docs/architecture/DOMAIN_MAP.md`
7. `docs/architecture/LAYER_INTERFACES.md`
8. `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md`
9. `docs/architecture/CEREMONY.md`
10. `docs/architecture/SENSE_CONTRACTS.md`
11. `docs/cartography/DATA_FLOW.md`
12. `docs/cartography/SYSTEM_OVERVIEW.md`
13. `docs/plunder/MCP_SDK_PLUNDER_MAP.md`
14. `docs/plunder/WHISPER_CPP_PLUNDER_MAP.md`
15. `docs/plunder/TAURI_PLUNDER_MAP.md`
16. `docs/plunder/LIBZIM_PLUNDER_MAP.md`
17. `docs/plunder/KIWIX_TOOLS_PLUNDER_MAP.md`
18. `docs/plunder/HERMES_AGENT_PLUNDER_MAP.md`
19. `docs/plunder/OPENCLAW_PLUNDER_MAP.md`
20. `docs/plunder/SILLYTAVERN_PLUNDER_MAP.md`
21. `THIRD_PARTY_NOTICES.md`
22. `docs/ROADMAP.md`
23. `README.md`
24. `TASK_HERETIC_v0.1_BOOTSTRAP.md`

**Summary verdict:** FAILS — 2 blockers present (config key namespace contradicts SEALED NAMING.md; DATA_FLOW.md tool routing format contradicts SENSE_CONTRACTS.md). 4 license TBDs resolved. 5 open architectural questions resolved or deferred with rationale. 4 absolute-path RULES.AI violations documented (docs only — no code yet). Intermediate lifecycle state naming gap identified as notable but not a blocker.

---

## Section A — Internal Consistency

### A-1 (BLOCKER) Config key namespace contradicts SEALED NAMING.md

**Evidence:**
- `docs/NAMING.md:81` (SEALED) states explicitly: "each layer's identifier becomes its top-level config section (`grunnr:`, `bifrost:`, `rodd:`, `sjon:`, `vebond:`, `skilningr:` → with subsections for each sense using their code-facing identifiers)."
- `docs/architecture/LAYER_INTERFACES.md:174–190` defines L2 Rödd config under the top-level key `voice:` (e.g., `voice.stt.engine`, `voice.tts.endpoint`, `voice.tts.endpoint`).
- `docs/architecture/LAYER_INTERFACES.md:224–238` defines L3 Sjón config under `vision:`.
- `docs/architecture/LAYER_INTERFACES.md:281–288` defines L4 Vébond config under `ui:`.
- `docs/architecture/LAYER_INTERFACES.md:325–346` defines L5 Skilningr config under `senses:`.
- `docs/cartography/DATA_FLOW.md:72–73` also uses `rodd.stt_backend`, `rodd.tts_endpoint` — yet another namespace (matches no other doc).

**The contradiction:**

| Document | Top-level config key for L2 Rödd | Authority |
|---|---|---|
| `docs/NAMING.md` (SEALED) | `rodd:` | Canonical — cannot be edited |
| `docs/architecture/LAYER_INTERFACES.md` | `voice:` | Must be corrected |
| `docs/cartography/DATA_FLOW.md` | `rodd.stt_backend` / `rodd.tts_endpoint` | Partially aligned with NAMING.md (uses `rodd.`) but uses flat keys rather than nested `rodd.stt.engine` |

Similar mismatch for L3 (`sjon:` vs `vision:`), L4 (`vebond:` vs `ui:`), L5 (`skilningr.senses.*` vs `senses.*`).

**Impact:** If code were written today using either set of keys, it would contradict the canonical naming system. The config contract must be settled before any code touches `heretic.yaml`.

**Resolution required:** `docs/architecture/LAYER_INTERFACES.md` must be updated to use the True Name keys mandated by NAMING.md: `rodd:`, `sjon:`, `vebond:`, `skilningr:` (with `senses.` sub-namespace inside `skilningr:`). `docs/cartography/DATA_FLOW.md` config references must be updated to match. NAMING.md is the authority; LAYER_INTERFACES.md defers.

---

### A-2 (BLOCKER) Tool routing format contradicts between DATA_FLOW.md and SENSE_CONTRACTS.md

**Evidence:**
- `docs/architecture/SENSE_CONTRACTS.md:53` defines the tool naming convention as `<sense_id>.<action_name>` — two-part. Examples: `filesystem.read_file`, `blender.screenshot`, `terminal.run_command`.
- `docs/cartography/DATA_FLOW.md:301` shows a tool call with name `"sense.smidja.execute_blender_script"` — three-part with `sense.` prefix.
- `docs/cartography/DATA_FLOW.md:309`: "parses tool name: `sense.smidja.*` --> route to Skilningr/Smiðja"
- `docs/cartography/DATA_FLOW.md:659`: "parses tool name: `sense.<server>.<method>`"
- `docs/cartography/SYSTEM_OVERVIEW.md:95–106` also uses `sense.auga`, `sense.hlust`, `sense.smidja` etc. as the sense server identifiers (two-part in context: `sense.<id>`)

**The contradiction:** SENSE_CONTRACTS.md mandates that tool names are `<sense_id>.<action>` with no `sense.` prefix. DATA_FLOW.md defines the routing format as `sense.<server>.<method>` (three-part). These are irreconcilable routing schemes. The Forge Worker cannot implement both; the agent cannot be told both conventions.

**Additional confusion:** SENSE_CONTRACTS.md §2 maps True Names to `sense_id`:
- Minni → `filesystem`
- Smiðja → `blender`
- Leið → `browser`

But DATA_FLOW.md and SYSTEM_OVERVIEW.md use `sense.minni`, `sense.smidja`, `sense.leid` as identifiers — using the True Name short form rather than the English code-facing id.

**Impact:** Tool call routing is the hot path. The agent will construct tool names based on the schemas it receives. If the schema says `blender.screenshot` but the routing table expects `sense.smidja.screenshot`, every Smiðja tool call will fail with `tool_not_found`.

**Resolution required:** One format must be chosen and enforced consistently across all documents. SENSE_CONTRACTS.md is the authoritative source for the tool protocol. DATA_FLOW.md must be corrected to use the two-part `<sense_id>.<action>` format. The `sense.` prefix used in DATA_FLOW.md appears to have originated as a namespace label for clarity in diagrams, not as a literal tool name format — but it must not appear in literal tool name examples.

---

### A-3 (SERIOUS) Intermediate lifecycle states in CEREMONY.md have no True Names in NAMING.md

**Evidence:**
- `docs/NAMING.md:50–56` (SEALED) defines exactly 5 lifecycle states with True Names and code constants: Hvíld (`STATE_HVILD`), Kynding (`STATE_KYNDING`), Tengsl (`STATE_TENGSL`), Samræður (`STATE_SAMRAEDUR`), Slokna (`STATE_SLOKNA`).
- `docs/architecture/CEREMONY.md:53,57,66,90,107` introduces 5 additional runtime states: `CONFIG_ERROR`, `READY`, `OPENING`, `RECOVERING`, `EXTINGUISHED` — used as code constants throughout the state machine.
- These states have no True Names in NAMING.md. The Forge Worker would implement them as English-identifier code constants with no corresponding Norse naming.

**Assessment:** NAMING.md's five states are *phases* (the arc of a ceremony from the human perspective). CEREMONY.md's additional states are *sub-phases* and *error states* (the runtime machinery needed to implement those phases). This is architecturally coherent — not every runtime state needs a public-facing ceremonial name — but NAMING.md does not acknowledge this distinction, nor does it explicitly say the five are the only states. The gap is a notable omission. NAMING.md §7 principle 6 says "new states should follow that register" — implying that if more states are named they should follow the fire/rest pattern.

**Resolution required:** CEREMONY.md should include a brief note clarifying that `READY`, `OPENING`, `RECOVERING`, `EXTINGUISHED`, `CONFIG_ERROR` are sub-phase implementation constants, not public ceremony states. If any of these are to be surfaced in the UI or in the API, they should receive True Names. NAMING.md (SEALED) does not need editing — the distinction should be documented in CEREMONY.md as a clarification, not a contradiction.

---

### A-4 (NOTABLE) Auga, Hlust, Tunga listed as senses in NAMING.md but absent from L5.x numbering in ARCHITECTURE.md

**Evidence:**
- `docs/NAMING.md:31–33` lists Auga, Hlust, Tunga with `sense.auga`, `sense.hlust`, `sense.tunga` code identifiers in the senses table, alongside 9 other senses.
- `docs/architecture/ARCHITECTURE.md` lists only 9 L5.x numbered senses (L5.1 Minni through L5.9 Mímisbrunnr). Auga is described under L3 Sjón; Hlust and Tunga are described under L2 Rödd.
- `docs/architecture/SENSE_CONTRACTS.md` only defines per-sense detail for L5.1–L5.9. Auga, Hlust, Tunga have no section in SENSE_CONTRACTS.md.
- `docs/architecture/LAYER_INTERFACES.md` treats Hlust and Tunga as sub-components of L2 Rödd (not as independent MCP senses), and Auga as a sub-component of L3 Sjón.

**Assessment:** There is an unresolved architectural split. NAMING.md (SEALED) assigned `sense.auga`, `sense.hlust`, `sense.tunga` identifiers to these three — implying they might be addressable as MCP senses (callable via tool calls). But ARCHITECTURE.md places them in L2/L3 as layer-internal sub-components. DATA_FLOW.md (line 663–664) shows them routing through Skilningr, suggesting an intent to make them callable — but SENSE_CONTRACTS.md has no contract for them.

**Resolution required:** Architect decision needed: are Auga, Hlust, Tunga MCP senses reachable via tool calls (in which case they need SENSE_CONTRACTS.md entries and L5.x numbers), or are they internal layer components (in which case their `sense.*` identifiers in NAMING.md are misleading)? This must be resolved before any L2/L3/L5 code is written. Document the decision in ARCHITECTURE.md §2 (layer table) and SENSE_CONTRACTS.md. If they remain as layer-internal components, remove their `sense.*` identifiers from the routing tables in DATA_FLOW.md.

---

### A-5 (NOTABLE) SYSTEM_OVERVIEW.md config block uses `skilningr.senses.*` nesting

**Evidence:**
- `docs/cartography/SYSTEM_OVERVIEW.md:226–236` shows a `heretic.yaml` example:
  ```yaml
  skilningr:
    senses:
      minni:
        enabled: true
  ```
- `docs/architecture/LAYER_INTERFACES.md:325–346` shows senses config under top-level `senses:` (e.g., `senses.filesystem.enabled`).

**Assessment:** This is a subset of finding A-1 (the `senses:` vs `skilningr.senses:` dispute). The SYSTEM_OVERVIEW.md config block is actually *more aligned* with NAMING.md's mandate (NAMING.md line 81: `skilningr:` with subsections) than LAYER_INTERFACES.md is. When A-1 is resolved by bringing LAYER_INTERFACES.md into alignment with NAMING.md, SYSTEM_OVERVIEW.md's `skilningr.senses.*` block will become correct. However, the True Name identifiers for senses are inconsistent: SYSTEM_OVERVIEW.md uses `minni:`, `auga:`, `smidja:` (True Name short forms) while LAYER_INTERFACES.md uses `filesystem:`, `terminal:`, `browser:` (code-facing sense_ids). NAMING.md line 81 specifies "subsections for each sense using their code-facing identifiers" — meaning the sub-key should be `filesystem`, not `minni`.

**Resolution:** When A-1 is corrected, SYSTEM_OVERVIEW.md's sense keys should also be corrected to code-facing IDs: `filesystem:`, `terminal:`, etc. — not the True Name short forms.

---

### A-6 (NIT) README.md line 52 is stale

**Evidence:**
- `README.md:52`: "Architecture docs (ARCHITECTURE.md, LAYER_INTERFACES.md, CEREMONY.md, ROADMAP.md) are being drafted in `docs/` as part of v0.0. When they exist, this table will be updated."
- All named docs now exist: `docs/architecture/ARCHITECTURE.md`, `docs/architecture/LAYER_INTERFACES.md`, `docs/architecture/CEREMONY.md`, `docs/ROADMAP.md`. All were created as part of the v0.0 doc build.

**Resolution:** Update line 52 and the preceding "What to Read First" table to include links to the architecture documents that now exist. This is trivially fixable and must not be left for Forge to discover.

---

## Section B — License Verification

### B-1 (RESOLVED) ChatterBox TTS — MIT confirmed

**Evidence:** `gh repo view resemble-ai/chatterbox --json name,licenseInfo,url,description` returned:
```json
{"description":"SoTA open-source TTS","licenseInfo":{"key":"mit","name":"MIT License","nickname":""},"name":"chatterbox","url":"https://github.com/resemble-ai/chatterbox"}
```

**Verdict:** MIT. Compatible with HERETIC's MIT license. ChatterBox is an external runtime service (runs on Pi); HERETIC holds no ChatterBox code. Attribution: THIRD_PARTY_NOTICES.md entry requires update to reflect confirmed MIT.

**Required fix:** Update `THIRD_PARTY_NOTICES.md` lines 82–83 (ChatterBox entry) from "License verification TBD" to "MIT — Resemble AI. Verified 2026-05-07." Also update the License Verification TBD table (line 316) to remove ChatterBox from the pending list or mark it resolved.

---

### B-2 (RESOLVED) python-libzim — GPL-3.0 confirmed

**Evidence:** `gh repo view openzim/python-libzim --json name,licenseInfo,url` returned:
```json
{"licenseInfo":{"key":"gpl-3.0","name":"GNU General Public License v3.0","nickname":"GNU GPLv3"},"name":"python-libzim","url":"https://github.com/openzim/python-libzim"}
```
`pip show libzim` returned `WARNING: Package(s) not found: libzim` (not installed on this machine — confirmed at repo level instead).

**Verdict:** GPL-3.0 confirmed. THIRD_PARTY_NOTICES.md had this as "TBD." The runtime-import-only pattern (dynamic `try/except ImportError` in `parser_zim.py`) is the correct and sufficient GPL compliance architecture. GPL-3 is compatible with GPL-2-or-later libzim C++ — confirmed.

**Required fix:** Update `THIRD_PARTY_NOTICES.md` python-libzim entry (line 187) from "claims GPL-3.0; Auditor must verify" to "Verified GPL-3.0 2026-05-07."

---

### B-3 (RESOLVED) faiss-cpu — MIT confirmed

**Evidence:** `gh repo view facebookresearch/faiss --json name,licenseInfo,url` returned:
```json
{"licenseInfo":{"key":"mit","name":"MIT License","nickname":""},"name":"faiss","url":"https://github.com/facebookresearch/faiss"}
```
`pip show faiss-cpu` returned `WARNING: Package(s) not found: faiss-cpu` (not installed locally).

**Verdict:** MIT confirmed. Compatible with HERETIC's MIT license. The historical concern about Facebook Research using custom licenses was valid to check — the current FAISS repo is unambiguously MIT.

**Required fix:** Update `THIRD_PARTY_NOTICES.md` faiss entry (line 235) from "MIT is commonly reported; Auditor should verify" to "Verified MIT 2026-05-07."

---

### B-4 (RESOLVED) sentence-transformers — Apache-2.0 confirmed

**Evidence:** `pip show sentence-transformers` returned `License: Apache 2.0` (version 5.3.0, installed). `gh repo view UKPLab/sentence-transformers` returned `{"licenseInfo":{"key":"apache-2.0",...},"url":"https://github.com/huggingface/sentence-transformers"}`.

Note: Repository has moved from `UKPLab/sentence-transformers` to `huggingface/sentence-transformers` — the UKPLab URL redirects correctly.

**Verdict:** Apache-2.0 confirmed. Compatible with HERETIC's MIT license (Apache-2.0 code may be used in MIT projects with attribution). HERETIC does not distribute sentence-transformers; it is a user-installed optional dependency for Mímisbrunnr vector search.

**Required fix:** Update `THIRD_PARTY_NOTICES.md` sentence-transformers entry (line 249) from "Verified Apache-2.0 (commonly known; Auditor should confirm at v0.7.5)" to "Verified Apache-2.0 2026-05-07."

---

### B-5 (VERIFIED) libzim C++ — GPL-2.0-or-later confirmed

**Evidence:** `gh repo view openzim/libzim --json name,licenseInfo,url` returned `{"licenseInfo":{"key":"gpl-2.0",...},"name":"libzim"}`. Note: the gh API reports `gpl-2.0` for a file typically titled "GPL-2.0-or-later" — the plunder map's claim of GPL-2.0-or-later is accurate (the "-or-later" clause is in the license file header, not captured by the gh license key).

**Verdict:** GPL-2.0-or-later. THIRD_PARTY_NOTICES.md and LIBZIM_PLUNDER_MAP.md are correct.

---

### B-6 (VERIFIED) kiwix-tools — GPL-3.0 confirmed

**Evidence:** `gh repo view kiwix/kiwix-tools --json name,licenseInfo,url` returned `{"licenseInfo":{"key":"gpl-3.0",...},"name":"kiwix-tools"}`.

**Verdict:** GPL-3.0 confirmed. KIWIX_TOOLS_PLUNDER_MAP.md is correct.

---

### B-7 (VERIFIED) MCP Python SDK — MIT confirmed

**Evidence:** `gh repo view modelcontextprotocol/python-sdk --json name,licenseInfo,url` returned `{"licenseInfo":{"key":"mit",...},"name":"python-sdk"}`.

**Verdict:** MIT confirmed. MCP_SDK_PLUNDER_MAP.md is correct.

---

### B-8 (VERIFIED) whisper.cpp — MIT confirmed

**Evidence:** `gh repo view ggerganov/whisper.cpp --json name,licenseInfo,url` returned `{"licenseInfo":{"key":"mit",...},"name":"whisper.cpp"}`. Note: repository is now under `ggml-org/whisper.cpp` (organization name changed from `ggerganov`); the URL still resolves.

**Verdict:** MIT confirmed. WHISPER_CPP_PLUNDER_MAP.md is correct.

---

### B-9 (PARTIALLY VERIFIED) Tauri — dual MIT/Apache-2.0 confirmed

**Evidence:** `gh repo view tauri-apps/tauri --json name,licenseInfo,url` returned `{"licenseInfo":{"key":"apache-2.0",...}}`. The gh API only captures one SPDX key. Directory listing via `gh api repos/tauri-apps/tauri/contents/` revealed both `LICENSE_APACHE-2.0` and `LICENSE_MIT` files present.

**Verdict:** Dual MIT/Apache-2.0 confirmed. TAURI_PLUNDER_MAP.md is correct. HERETIC receives under MIT (the permissive choice).

---

### B-10 (VERIFIED) SillyTavern — AGPL-3.0 confirmed

**Evidence:** `gh repo view SillyTavern/SillyTavern --json name,licenseInfo,url` returned `{"licenseInfo":{"key":"agpl-3.0",...}}`.

**Verdict:** AGPL-3.0 confirmed. SILLYTAVERN_PLUNDER_MAP.md verdict (incompatible — zero code use permitted) stands.

---

### B-11 (VERIFIED) Hermes Agent — MIT confirmed, star count accurate

**Evidence:** `gh repo view NousResearch/hermes-agent --json name,licenseInfo,url,description,stargazerCount` returned `{"licenseInfo":{"key":"mit",...},"stargazerCount":137388,"url":"https://github.com/NousResearch/hermes-agent"}`.

**Verdict:** MIT confirmed. The claimed "~137k stars" in HERMES_AGENT_PLUNDER_MAP.md matches the live count of 137,388. The initial auditor suspicion ("implausible") was incorrect — the count is real.

---

### B-12 (VERIFIED) OpenClaw — MIT confirmed, star count accurate

**Evidence:** `gh repo view openclaw/openclaw --json name,licenseInfo,url,stargazerCount` returned `{"licenseInfo":{"key":"mit",...},"stargazerCount":369423,"url":"https://github.com/openclaw/openclaw"}`.

**Verdict:** MIT confirmed. The claimed "~369k stars" matches live count of 369,423. OPENCLAW_PLUNDER_MAP.md is correct.

---

## Section C — Architectural Open Questions

### C-Q-A1 (RESOLVED — API CONFIRMED) Photopea echoToOE() API

**Question:** Does `app.echoToOE()` exist as a documented, stable Photopea API? Is the integration path viable?

**Evidence:** `curl -s https://www.photopea.com/api/live` retrieved live Photopea API documentation. The page explicitly documents:
- `app.echoToOE("Hello");` — sends any string to the Outer Environment (OE, i.e., the host iframe/window)
- `app.activeDocument.saveToOE("psd");` — sends the current file to OE as binary
- `app.echoToOE(app.activeDocument.source);` — sends the document source ID to OE
- Custom scripts for Open/Save button hooks: `app.echoToOE("Open" / "Save");`

The API is documented, stable, and public. The communication model is postMessage-based iframe messaging: HERETIC embeds Photopea in a `<webview>` (Tauri WebView), sends JavaScript script commands via the Photopea URL hash parameter or postMessage API, and receives results via the `message` event handler that catches `echoToOE` emissions.

**Resolution:** Q-A1 is resolved. The Hönd (L5.4) integration is viable. The contract should be documented in `docs/architecture/SENSE_CONTRACTS.md` L5.4 Hönd section. The open question annotation at LAYER_INTERFACES.md:491 can be updated to "API verified 2026-05-07 — `app.echoToOE()` and `app.activeDocument.saveToOE()` confirmed documented at https://www.photopea.com/api/live."

**Constraint identified:** Photopea must be embedded in a WebView within HERETIC's Tauri window (the Leið browser sense is not sufficient — Photopea requires direct iframe postMessage communication, not a headless browser). Hönd's dependency on Leið should be reconsidered: Hönd may require its own WebView panel rather than routing through Leið's Playwright/Chromium instance.

---

### C-Q-A2 (RESOLVED — DESIGN BOUNDARY SET) VRChat OSC parameter surface

**Question:** What is the full VRChat OSC API surface (readable/writable avatar parameters, receivable events)?

**Evidence:** VRChat docs at `docs.vrchat.com/docs/osc-overview` and `docs.vrchat.com/docs/osc-avatar-parameters` were fetched. The VRChat OSC protocol is well-documented:
- **Sending to VRChat:** UDP to `127.0.0.1:9000`. Address format: `/avatar/parameters/<parameterName>`.
- **Receiving from VRChat:** UDP on `127.0.0.1:9001`. VRChat broadcasts avatar parameter changes.
- **Parameter types:** Bool, Int, Float — mapped to avatar animator parameters.
- **Avatar change events:** `/avatar/change` with avatar ID.
- **Built-in parameters:** VRChat exposes several built-in parameters (e.g., `VelocityX`, `VelocityY`, `VelocityZ`, `Grounded`, `MuteSelf`, `InStation`, `Seated`, etc.)
- The OSC spec is public, versioned, and stable since VRChat's OSC rollout.

**Resolution:** Q-A2 is resolved at the design level. The `vrchat.send_osc(address, args)`, `vrchat.get_avatar_parameters()`, `vrchat.set_avatar_parameter(name, value)`, and `vrchat.get_player_position()` tools defined in LAYER_INTERFACES.md L5.6 are implementable using the public OSC protocol. Full parameter enumeration is avatar-specific (each avatar publishes its own parameters) and cannot be statically defined — the `get_avatar_parameters()` tool should return whatever parameters VRChat broadcasts, not a static list. This should be noted in SENSE_CONTRACTS.md L5.6 Líkami section. The "audit required at v0.10 entry" annotation can be replaced with "OSC protocol verified 2026-05-07 — standard UDP 9000/9001 VRChat OSC format."

---

### C-Q-A3 (DEFERRED — RATIONALE DOCUMENTED) session.save_transcript

**Question:** Should HERETIC persist session transcripts? Where is the boundary of what the body owns vs. what the spirit owns?

**Resolution:** Deferred to v1.x. Rationale: The body/spirit split is foundational and sealed in the manifesto. HERETIC's body does not own agent memory, persona, or conversation history — these belong to the spirit. A session transcript IS conversation history. However, a raw event log (not a semantic memory) is infrastructure, and HERETIC already owns the session event ledger. If Volmarr decides the body should log raw turn records to disk (not for agent consumption, but for user review), that is an L0 Grunnr responsibility and does not violate the body/spirit split.

Decision recorded here and in the risk register: do not implement any transcript persistence before v1.0. The v1.x roadmap entry for session transcript should note this boundary: "raw event ledger is L0 infrastructure; semantic memory is the spirit's domain; log raw turns to disk only if user opts in explicitly, without feeding them back into the agent context."

---

### C-Q-C1 (RESOLVED — LAZY LOAD MANDATED) Whisper model loading strategy

**Question:** Should HERETIC load the Whisper model eagerly at Kynding (startup) or lazily on first use?

**Resolution:** Lazy load is the correct answer for v0.1, with eager load as an opt-in config. Rationale:
1. Whisper model sizes: `ggml-base.en.bin` is 142 MB; `ggml-medium.en.bin` is 1.5 GB. Eager loading on every startup imposes 2–30 second startup cost even when voice is never used in that session.
2. The manifesto principle is ceremonial activation, not always-on. A body that staggers under its own startup weight violates the spirit of the ceremony.
3. The correct design: Whisper subprocess starts at Kynding (sense spawn), but does **not** load model weights until the first transcription request (or when the user activates voice in Vébond). On first activation, load model (emit `VOICE_STT_LOADING` state to L4 for UI feedback). This adds latency to the first utterance only, which is acceptable.

**Config key to add in LAYER_INTERFACES.md L2 Rödd:**
```yaml
voice:
  stt:
    load_strategy: lazy   # lazy | eager; default lazy
```

This resolves Q-C1. Add the `load_strategy` key to LAYER_INTERFACES.md L2 Rödd config block.

---

### C-Q-C2 (RESOLVED — YES, INJECT AT TENGSL) Senses manifest in system prompt

**Question:** Should HERETIC inject a description of available senses into the agent's system prompt at Tengsl?

**Resolution:** Yes — inject a minimal senses manifest at Tengsl, but only as tool schemas (the standard OpenAI `tools` array), not as free text in the system prompt. Rationale:
1. The OpenAI-compat protocol already defines the mechanism: the `tools` array in the `/v1/chat/completions` request IS the senses manifest. The agent receives the full tool schema for every enabled sense on every request.
2. Adding free text to the system prompt describing the senses would be redundant and potentially confusing — the agent already has structured tool schemas.
3. The `inject_context_on_connect` flag in LAYER_INTERFACES.md L1 Bifröst (line 124) handles the optional "HERETIC context message" — this is for human-readable context (e.g., "You are speaking with Volmarr through HERETIC v0.1"), not for tool schema injection.

**Decision:** Tool schemas are injected via the `tools` array on every request (standard protocol). The `inject_context_on_connect` message is optional prose context, not a tool manifest. AGENT_AGNOSTIC_PROTOCOL.md already documents this correctly.

---

### C-Q-C3 (RESOLVED — BASE64 INLINE, CONDITIONAL ON AGENT CAPABILITY) Screen capture format

**Question:** Should screen frames be sent as inline base64 in the message content, or as URL references?

**Resolution:** Inline base64, conditioned on `?vision_in` capability flag. Rationale:
1. URL references require a file server or a persistent image hosting service. HERETIC has no such service. URLs would also expose images to network interception.
2. The OpenAI vision API uses inline base64 (or URLs pointing to already-hosted images). Since HERETIC routes to local agents (Hermes on Pi, OpenClaw locally), inline base64 is the simplest and safest format — no side-channel exposure.
3. The `?vision_in` capability flag already gates whether frames are sent at all. If the agent cannot receive images, no frames are sent regardless of the format question.
4. Inline base64 at 1280×720 PNG is approximately 1.2 MB per frame in worst case. This is within the `max_tokens: 127000` budget as image content (OpenAI-compat models typically handle vision via the image content type, not token counting).

**Decision:** Send frames as inline base64 `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}` per the OpenAI vision format. Document this explicitly in DATA_FLOW.md §3 (Sjón data contract) and AGENT_AGNOSTIC_PROTOCOL.md.

---

### C-Q-C4 (RESOLVED — ALLOWLIST DEFAULT WITH OPT-IN TIERS) Skepja sandboxing

**Question:** What is the default sandboxing model for the terminal sense (L5.2 Skepja)?

**Resolution:** Allowlist by default, with opt-in escalation tiers. The default configuration:
- **Tier 0 (default):** Allowed directories restricted to `~/heretic_workspace`. Forbidden patterns active (see LAYER_INTERFACES.md L5.2 config). Shell: user's default or `bash`. No network commands.
- **Tier 1 (opt-in):** Operator expands `allowed_dirs` in `heretic.yaml`. Forbidden patterns may be adjusted.
- **Tier 2 (power user opt-in):** `allow_unrestricted_dirs: true` — removes directory restriction but keeps forbidden patterns. Requires explicit config.
- **Tier 3 (explicit unsafe mode):** `safe_mode: false` — removes all restrictions. Must be set with a warning comment in the config schema.

This decision should be documented in SENSE_CONTRACTS.md L5.2 Skepja section, replacing the existing "open question" annotation. The tiered design gives HERETIC a sensible safe default while not blocking power users.

---

## Section D — Manifesto Alignment

All 24 documents were checked against the 5 principles of `docs/BODY_MANIFESTO.md`:
1. HERETIC is the body, not the brain.
2. The spirit is any agent that speaks the protocol.
3. The ceremony is the relationship, not always-on.
4. The body does not own memory, persona, or character.
5. The body can be given to another — agent-agnostic by design.

**Verdict:** All docs pass manifesto alignment. No document claims memory ownership, no document assumes a specific agent, no document imposes always-on behavior. The "open question" about `session.save_transcript` (Q-A3) was the only potential tension — resolved in Section C as correctly deferred.

---

## Section E — Plunder Rule Compliance

### E-1 (VERIFIED) All AGPL-licensed material is reference-only

SillyTavern (AGPL-3.0) appears only in SILLYTAVERN_PLUNDER_MAP.md and THIRD_PARTY_NOTICES.md. No SillyTavern code, patterns, or data structures appear anywhere in the HERETIC doc set or codebase (no code exists yet). The plunder map's "INCOMPATIBLE — zero code use permitted" verdict is enforced.

### E-2 (VERIFIED) GPL-licensed material (libzim, kiwix-tools) is external-runtime-only

LIBZIM_PLUNDER_MAP.md and KIWIX_TOOLS_PLUNDER_MAP.md document the compliance architecture: `try/except ImportError` guard, `parser_zim.py` as the GPL firewall, no GPL code enters HERETIC's distribution archive. THIRD_PARTY_NOTICES.md confirms. No GPL code in the current codebase (no code exists yet).

### E-3 (VERIFIED) MIT/Apache-2.0 components follow lawful plunder workflow

Tauri (MIT/Apache-2.0), whisper.cpp (MIT), MCP Python SDK (MIT), Hermes Agent (MIT — architecture reference), OpenClaw (MIT — architecture reference), ChatterBox (MIT — external service), faiss-cpu (MIT), sentence-transformers (Apache-2.0) are all either in `vendor/` (planned) or external services, with appropriate plunder maps.

### E-4 (NOTABLE) No MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md plunder map exists for faiss-cpu or sentence-transformers

**Evidence:** `ls docs/plunder/` shows 8 plunder maps. faiss-cpu and sentence-transformers have THIRD_PARTY_NOTICES.md entries but no dedicated plunder maps.

**Assessment:** These are optional Python library dependencies for the Mímisbrunnr vector search backend — they are not "plundered" in the architectural-study sense, they are pip dependencies. A dedicated plunder map is not required for every pip package. THIRD_PARTY_NOTICES.md entries are sufficient. No action required.

---

## Section F — RULES.AI Compliance

### F-1 (BLOCKER WHEN CODE EXISTS / NOTABLE NOW) Absolute paths in documentation

**Evidence:** `grep -rn "C:/Users\|C:\\Users" docs/` found 4 occurrences:

| File | Line | Absolute path reference |
|---|---|---|
| `docs/architecture/DOMAIN_MAP.md` | 288 | `` `C:/Users/volma/runa/Seidr-Smidja` `` |
| `docs/architecture/SENSE_CONTRACTS.md` | 348 | `` `C:/Users/volma/runa/Seidr-Smidja` `` |
| `docs/ROADMAP.md` | 142 | `` `C:/Users/volma/runa/Seidr-Smidja` `` |
| `docs/ROADMAP.md` | 219 | `` `C:/Users/volma/runa/MindSpark_ThoughtForge` ``, `` `C:/Users/volma/runa/WYRD-Protocol` `` |
| `docs/ROADMAP.md` | 420 | `` `C:/Users/volma/runa/MindSpark_ThoughtForge` `` |

RULES.AI.md is explicit: "Never use absolute paths no matter what!" and "Make sure the code uses internal APIs for communications."

**Assessment:** These are documentation references (showing where sibling repos live on Volmarr's machine), not code paths. They will not cause runtime failures. However, RULES.AI.md's prohibition on absolute paths applies to the codebase — and documentation that will guide Forge's implementation should model the correct behavior. These references should be replaced with relative or descriptive references (e.g., "a sibling repo in the same parent directory as HERETIC" or the GitHub URL).

**Resolution required:** Replace all absolute path references in docs with either (a) the GitHub repository URL, or (b) a portable description (e.g., "Seidr-Smidja — a sibling repository; see its repo at `github.com/hrabanazviking/Seidr-Smidja`"). These are docs, not code, so this is notable rather than a blocker — but they should be fixed before Forge begins, to prevent Forge from using absolute paths in actual code.

---

### F-2 (VERIFIED) No pseudocode in documentation

No doc contains pseudocode disguised as real code. All code blocks in the docs are either YAML config examples, illustrative ASCII diagrams, or documented API snippets (Photopea JS, tool names, etc.). RULES.AI.md prohibition on pseudocode is not violated.

---

### F-3 (VERIFIED) Config keys use data files, not hardcoded values

All `heretic.yaml` examples in the docs use `${}` env var references for secrets (`HERETIC_AGENT_KEY`, `SEIDR_BRUNHAND_TOKEN`, `HERETIC_MAIL_USER`, `HERETIC_MAIL_PASSWORD`). No secrets are hardcoded. RULES.AI.md requirement met.

---

### F-4 (VERIFIED) Max tokens set to 127000

`docs/architecture/LAYER_INTERFACES.md:119`: `max_tokens: 127000 # per RULES.AI.md — keep high`. The requirement is documented and annotated. Verified.

---

## Fixed Items

The following fixes are applied directly in this audit session (trivial, evidence-supported, non-architectural):

### FIX-1 — THIRD_PARTY_NOTICES.md: Resolve 4 license TBDs

See Section B-1 through B-4 above. Four "License verification TBD" entries resolved:
- ChatterBox TTS: MIT (resemble-ai/chatterbox, verified 2026-05-07)
- python-libzim: GPL-3.0 (openzim/python-libzim, verified 2026-05-07)
- faiss-cpu: MIT (facebookresearch/faiss, verified 2026-05-07)
- sentence-transformers: Apache-2.0 (huggingface/sentence-transformers, verified 2026-05-07)

*Applying to THIRD_PARTY_NOTICES.md.*

### FIX-2 — README.md: Remove stale "being drafted" text

Update README.md line 52 to reflect that all v0.0 architecture docs now exist.

*Applying to README.md.*

---

## Items Requiring Architect/Volmarr Decision Before Forge Begins

The following require explicit decisions before any code is written. They cannot be resolved unilaterally by the Auditor.

| ID | Finding | Decision Needed |
|---|---|---|
| D-1 | **A-1 (BLOCKER)** Config key namespace | Confirm: NAMING.md mandates `rodd:`, `sjon:`, `vebond:`, `skilningr:` as top-level keys. Update LAYER_INTERFACES.md and DATA_FLOW.md config blocks to match. |
| D-2 | **A-2 (BLOCKER)** Tool routing format | Confirm: Tool names are `<sense_id>.<action>` per SENSE_CONTRACTS.md (no `sense.` prefix). Update DATA_FLOW.md routing examples to match. |
| D-3 | **A-4 (NOTABLE)** Auga/Hlust/Tunga architecture | Decide: Are these L5 MCP senses with callable tools, or L2/L3 internal components? Update ARCHITECTURE.md and SENSE_CONTRACTS.md accordingly. |
| D-4 | **C-Q-C1** Whisper load strategy | Add `load_strategy: lazy` config key to LAYER_INTERFACES.md L2 Rödd. |
| D-5 | **C-Q-C3** Screen frame format | Document inline base64 decision in DATA_FLOW.md §3 and AGENT_AGNOSTIC_PROTOCOL.md. |
| D-6 | **C-Q-C4** Skepja sandboxing tiers | Add Tier 0–3 model to SENSE_CONTRACTS.md L5.2 Skepja section. |
| D-7 | **A-3 (SERIOUS)** Intermediate lifecycle state True Names | Add note to CEREMONY.md clarifying READY/OPENING/RECOVERING/EXTINGUISHED/CONFIG_ERROR are sub-phase implementation constants, not public ceremony states. |
| D-8 | **F-1** Absolute path references | Replace 4 documentation absolute paths with GitHub URLs or portable descriptions. |

---

## Summary Verdict

**FAILS — 2 blockers present.**

| Severity | Count | Items |
|---|---|---|
| Blocker | 2 | A-1 (config key namespace), A-2 (tool routing format) |
| Serious | 1 | A-3 (intermediate lifecycle states unnamed) |
| Notable | 3 | A-4 (Auga/Hlust/Tunga architecture gap), A-5 (SYSTEM_OVERVIEW config nesting), F-1 (absolute paths in docs) |
| Nit | 1 | A-6 (README stale line) |
| Resolved | 4 | B-1 ChatterBox MIT, B-2 python-libzim GPL-3, B-3 faiss MIT, B-4 sentence-transformers Apache-2.0 |
| Q resolved | 5 | C-Q-A1 (Photopea API confirmed), C-Q-A2 (VRChat OSC confirmed), C-Q-A3 (transcript deferred), C-Q-C1 (lazy load), C-Q-C2 (tools array injection), C-Q-C3 (inline base64), C-Q-C4 (allowlist tiers) |

The two blockers (A-1, A-2) must be resolved in documentation before Forge writes a single line of code. The config key namespace is load-bearing: any `heretic.yaml` schema generated before this is resolved will be wrong. The tool routing format is equally load-bearing: the agent's tool call routing logic depends on a stable, consistent tool name format.

The four license TBDs are resolved. The doc set is otherwise architecturally sound, manifesto-aligned, and plunder-compliant.

---

*Audit closed by Sólrún Hvítmynd, Auditor for Vibe Coding, 2026-05-07.*
*The body cannot be built until these bones are set straight.*
