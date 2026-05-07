# HERETIC — Expanded Roadmap

**Authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding (second documentation pass)
**Derives from:** `TASK_HERETIC_v0.1_BOOTSTRAP.md` §6, `docs/BODY_MANIFESTO.md`, `docs/architecture/ARCHITECTURE.md`, `docs/PRIOR_PLANNING_TRIAGE.md`
**Branch:** development
**Status:** canonical doc-set record — update each milestone at scope entry

---

> *The body does not awaken all at once. It grows limb by limb, sense by sense, until it is whole enough to receive the spirit and worthy of the spirit's trust. This roadmap is the chronicle of that growth — not a promise, but a shape.*

---

## How to Read This Roadmap

Each milestone row in §1 is a self-contained vertical slice. The columns record:

- **Codename** — the Skald-given name from `NAMING.md` and the manifesto aesthetic
- **Layers / components** — which layers first appear or substantially change
- **Exit criteria** — what must be demonstrably true before the milestone is sealed
- **Dependencies** — which prior milestones must be sealed first
- **Cross-repo deps activated** — which external projects (Seidr-Smidja, ChatterBox, MindSpark, WYRD) first touch HERETIC at this milestone
- **Plunder targets** — which plunder maps from `docs/plunder/` must be acted on (dependency installed, contract verified, attribution confirmed)
- **Open architectural questions** — questions that must be resolved at or before scope entry; pulled from Architect and Cartographer flags in the architecture docs
- **Estimated effort** — calendar weeks at sustainable solo pace; carry-over from TASK file where noted

The roadmap has four bands:
- **Foundation band** — v0.0–v0.4 (bones + voice + UI; the minimal inhabitable body)
- **Senses band** — v0.5–v0.9 (sight, forge, files, web, art; the body gains its faculties)
- **Full body band** — v0.10–v1.0 (social embodiment, mail, custom limbs; first full release)
- **Stretch band** — v1.x+, v2.x (new limbs by community; photoreal stretch goals)

---

## §1. Milestone Table

---

### v0.0 — Grunnr Sáð (Foundation Seeded)

| Field | Detail |
|---|---|
| **Codename** | *Grunnr Sáð* — "the foundation seeded"; the ground is prepared, the vision is sealed |
| **Layers / components** | L0 Grunnr (config schema only, no running code) — documentation layer |
| **Exit criteria** | All v0.0 doc-set files sealed and pushed: `BODY_MANIFESTO.md`, `NAMING.md`, `MIMISBRUNNR.md`, `PRIOR_PLANNING_TRIAGE.md`, `ARCHITECTURE.md`, `LAYER_INTERFACES.md`, `AGENT_AGNOSTIC_PROTOCOL.md`, `CEREMONY.md`, `SENSE_CONTRACTS.md`, `DOMAIN_MAP.md`, `DATA_FLOW.md`, `SYSTEM_OVERVIEW.md`, all 8 plunder maps, `THIRD_PARTY_NOTICES.md`, this `ROADMAP.md`. MIT license confirmed. `heretic.yaml` schema draft merged. |
| **Dependencies** | None — this is the root |
| **Cross-repo deps activated** | None (docs only) |
| **Plunder targets** | All 8 plunder maps authored and reviewed. No code plundered yet; maps exist to prepare the v0.1 build. |
| **Open architectural questions** | None blocking — this milestone's exit criteria are all documentation. The questions flagged below are inherited by the milestones that first require their answers. |
| **Estimated effort** | ~1 week (largely complete 2026-05-07; plunder maps + THIRD_PARTY_NOTICES.md + ROADMAP.md close it) |

**Status as of 2026-05-07:** Substantially complete. Plunder maps, THIRD_PARTY_NOTICES.md, and ROADMAP.md closing out now.

---

### v0.1 — Fyrsta Samfélag (First Communion)

| Field | Detail |
|---|---|
| **Codename** | *Fyrsta Samfélag* — "first communion"; the first time the body speaks to the spirit |
| **Layers / components** | L0 Grunnr (config loading, logging, version), L1 Bifröst (CLI loop, agent connection, tool call dispatch skeleton) |
| **Exit criteria** | `heretic.yaml` loads cleanly from env / XDG / home search path. L0 Config struct typed and tested. L1 Bifröst connects to Hermes at `100.101.39.30:8643/v1` over Tailscale. A minimal CLI turn works: user types → message sent to agent → streaming response received → printed to terminal. Reconnect backoff and ceremonial connect/disconnect work. `heretic probe` tool call round-trip succeeds (Hermes calls a test MCP tool; HERETIC routes and returns result). All L0 + L1 code has test coverage ≥ 80%. |
| **Dependencies** | v0.0 (doc set sealed, Bifröst protocol confirmed from `AGENT_AGNOSTIC_PROTOCOL.md`) |
| **Cross-repo deps activated** | Hermes Agent on Pi — first live connection. No other cross-repo deps yet. |
| **Plunder targets** | `MCP_SDK_PLUNDER_MAP.md` → `pip install mcp` (or `cargo add mcp`) for the sense hub skeleton. `HERMES_AGENT_PLUNDER_MAP.md` → confirm tool-call format and `tools` array (not deprecated `functions`) against live Hermes endpoint. `TAURI_PLUNDER_MAP.md` → Tauri project initialized (Tauri scaffold runs; UI layer dormant). |
| **Open architectural questions** | **Q1: Rust vs Python for L0/L1.** Architecture doc flags Rust (via Tauri backend) as the implementation language for L0–L3. This must be confirmed before Forge starts. If Python is chosen for the CLI prototype, that is a temporary scaffold only — L0/L1 production code is Rust. **Resolve at v0.1 scope entry.** **Q2: Hermes tool-call format.** Confirm that live Hermes at `100.101.39.30:8643/v1` uses `tools` array (not deprecated `functions` key) and returns `finish_reason: tool_calls` with `role: tool` message handling. Verify with a minimal probe call before v0.1 Forge session. |
| **Estimated effort** | 1–2 weeks |

---

### v0.2 — Fyrsta Rödd Út (First Voice Out)

| Field | Detail |
|---|---|
| **Codename** | *Fyrsta Rödd Út* — "first voice out"; Hermes speaks in the room |
| **Layers / components** | L2 Rödd — Tunga (TTS) only. ChatterBox client added to voice layer. |
| **Exit criteria** | Agent response text is sent to ChatterBox at `100.66.178.105:7851` via HTTP. Audio plays through the configured speaker. TTS enable/disable flag in `heretic.yaml` works. Graceful fallback (text-only) when ChatterBox endpoint is unreachable. Warm-path SLO for TTS round-trip logged and compared against target (<400ms to audio start on local Tailscale). |
| **Dependencies** | v0.1 (L1 Bifröst returning streamed text) |
| **Cross-repo deps activated** | ChatterBox TTS at `100.66.178.105:7851` — first live TTS integration. |
| **Plunder targets** | No new plunder code. `THIRD_PARTY_NOTICES.md` ChatterBox entry updated once license is confirmed (**License verification TBD** — Auditor action required before this milestone closes). |
| **Open architectural questions** | **Q3: ChatterBox license.** `THIRD_PARTY_NOTICES.md` marks ChatterBox as License Verification TBD. Must be resolved before v0.2 ships. If ChatterBox is GPL-licensed, the external-service runtime pattern (call over HTTP, never import source) already cleanly isolates it — but the notice must be correct. **Q4: ChatterBox OpenAI-compat TTS endpoint.** Does ChatterBox expose an `/v1/audio/speech` endpoint (OpenAI-compat TTS), or does it use its own request format? Verify against the live instance before Forge starts. This affects how L2 Tunga constructs its HTTP calls. |
| **Estimated effort** | 1 week |

---

### v0.3 — Fyrsta Hlust (First Listening)

| Field | Detail |
|---|---|
| **Codename** | *Fyrsta Hlust* — "first hearing"; the body listens and carries the words across the bridge |
| **Layers / components** | L2 Rödd — Hlust (STT). Whisper.cpp subprocess management, VAD, transcript emission. |
| **Exit criteria** | Microphone captures audio. VAD segments speech turns correctly (configurable threshold). Whisper.cpp subprocess spawns, receives audio, returns transcript. Transcript is injected as user-role message into L1 Bifröst conversation. STT enable/disable flag works. Whisper model path configurable in `heretic.yaml`. End-to-end voice turn test: speak → transcript → Hermes reply → (text output at minimum; TTS if v0.2 also running). Warm-path SLO: VAD-to-transcript <600ms for short utterances on the test hardware. |
| **Dependencies** | v0.1 (L1 Bifröst), v0.2 (TTS operational — recommended but not hard-required; STT alone is testable) |
| **Cross-repo deps activated** | None new. whisper.cpp is a standalone runtime, not a cross-repo dep. |
| **Plunder targets** | `WHISPER_CPP_PLUNDER_MAP.md` — confirm Whisper.cpp binary or Python binding choice. **Q5 (below) must be resolved first.** Whisper.cpp model files are user-downloaded separately; `heretic.yaml` path config is the integration point. |
| **Open architectural questions** | **Q5: Whisper.cpp integration strategy.** Two options: (A) invoke the `whisper-cpp` binary as a subprocess (simplest, most portable); (B) use the Python `whispercpp` binding (more integration, less subprocess overhead). The plunder map notes this as an open question. Resolve before Forge starts: preference is Option A (subprocess) for isolation and portability, but test if latency is acceptable on the target hardware (Windows 11, laptop without discrete GPU). **Q6: VAD strategy.** Use Whisper.cpp's built-in VAD, or add a separate VAD library (e.g., Silero VAD via Python)? The plunder map flags this. Resolve at v0.3 scope entry. |
| **Estimated effort** | 1–2 weeks |

---

### v0.4 — Summonarhringar (Summoning Circle)

| Field | Detail |
|---|---|
| **Codename** | *Summonarhringar* — "the summoning circle"; the threshold where human and ceremony meet |
| **Layers / components** | L4 Vébond / Eldahús — Tauri React frontend. Full ceremony UI: light/extinguish, status indicators, voice waveform, sense toggles. L0 Tauri shell fully operational (not just scaffolded). |
| **Exit criteria** | Tauri app launches. Norse dark theme rendered. "Light the Candle" button triggers Kynding → Tengsl ceremony states. "Extinguish" triggers Slokna. Layer status panel reflects actual L1/L2/L5 health. Voice waveform displays during active STT. Sense enable/disable toggles reflect `heretic.yaml` state. Error/warning toasts surface from L0/L1 event bus. All UI interactions are event-driven via Tauri IPC; no direct Rust calls from JS. WebView2 verified on Windows 11 target (per `TAURI_PLUNDER_MAP.md` note). App cold-start to Hvíld state within 2s on target hardware. |
| **Dependencies** | v0.1 (L0/L1), v0.2 (TTS events for UI feedback), v0.3 (STT for waveform) |
| **Cross-repo deps activated** | None new. Tauri is a build-time framework dep, already scaffolded from v0.1. |
| **Plunder targets** | `TAURI_PLUNDER_MAP.md` → confirm WebView2 presence on Windows (Edge must be installed). React frontend dependency audit: add `tailwindcss` + Norse icon set to `THIRD_PARTY_NOTICES.md` as vendored permissive deps. |
| **Open architectural questions** | **Q7: Frontend framework.** React is specified in `ARCHITECTURE.md`. Confirm this at v0.4 scope entry — no alternative is currently proposed, but Tauri supports other frameworks (SolidJS, Svelte). If React is confirmed, Tailwind CSS for styling is the natural companion. Norse icon set source needs plunder-map entry (confirm license before use). **Q8: Tauri IPC event schema.** Define the typed IPC event set (Rust → TS and TS → Rust) before building UI components. Freezing this contract at v0.4 entry prevents drift later. Candidate events: `ceremony::state_changed`, `layer::health_changed`, `voice::activity`, `agent::token_chunk`, `sense::call_started`, `sense::call_completed`. |
| **Estimated effort** | 2–3 weeks |

**The Foundation Band (v0.0–v0.4) is the minimal inhabitable body.** After v0.4 closes, the spirit can be summoned, spoken to, and replied to through voice, in a proper ceremonial window. Senses begin in v0.5.

---

### v0.5 — Fyrsta Sjón (First Sight)

| Field | Detail |
|---|---|
| **Codename** | *Fyrsta Sjón* — "first sight"; the body opens its eyes |
| **Layers / components** | L3 Sjón (screen capture), L5 Skilningr MCP hub (first live MCP sense launched). L1 Bifröst tool call dispatch activated for the first real sense. |
| **Exit criteria** | Screen capture running on configurable interval. DXGI/WASAPI on Windows confirmed. Frame injected into conversation as image-role content when `vision.inject_in_context: true`. Sjón MCP sense (`auga.capture`, `auga.region`) responds to agent tool calls. Tool call round-trip: agent requests capture → Skilningr routes → Sjón returns base64 PNG → agent receives. Frame buffer (ring buffer depth configurable). Cold-path: optional file-save of frames for audit. |
| **Dependencies** | v0.4 (L4 UI — sense status panel must work before senses go live), v0.1 (L1 tool dispatch) |
| **Cross-repo deps activated** | None new. Screen capture is OS-native. |
| **Plunder targets** | No new plunder maps. Confirm which Rust screen-capture crate is used (`scap`, `screenshots`, or `display-info` + DXGI FFI) — add to `THIRD_PARTY_NOTICES.md` at scope entry with verified license. |
| **Open architectural questions** | **Q9: Screen capture crate.** Select and plunder-assess the Rust screen-capture library before Forge starts. Prefer a crate with MIT or Apache-2.0 license, Windows DXGI support, and an active maintenance history. Document selection in `THIRD_PARTY_NOTICES.md`. |
| **Estimated effort** | 1–2 weeks |

---

### v0.6 — Hönd at Smiðju (Hands at the Forge)

| Field | Detail |
|---|---|
| **Codename** | *Hönd at Smiðju* — "hands at the forge"; the spirit reaches into three-dimensional creation |
| **Layers / components** | L5.5 Smiðja — MCP wrapper around Seidr-Smidja Brúarhönd v0.1 (8 CLI subcommands + 3 MCP tools). First cross-repo MCP integration. |
| **Exit criteria** | Smiðja MCP sense starts and registers its tool schemas with Skilningr. Agent can call `smidja.*` tools. Tool calls route to Seidr-Smidja Brúarhönd daemon via existing Brúarhönd HTTP interface. Round-trip test: agent calls `smidja.screenshot` → Brúarhönd captures → result returned to agent. Config: Brúarhönd endpoint URL in `heretic.yaml`. Graceful degradation when Brúarhönd daemon is not running (sense health monitor reports DOWN; other senses unaffected). |
| **Dependencies** | v0.5 (L5 Skilningr MCP hub live), v0.4 (sense status panel), v0.1 (tool dispatch) |
| **Cross-repo deps activated** | **Seidr-Smidja** (`C:/Users/volma/runa/Seidr-Smidja`) — Brúarhönd v0.1 daemon must be running independently. HERETIC does not manage Seidr-Smidja's process; user runs it separately. |
| **Plunder targets** | No new plunder maps (Seidr-Smidja is Volmarr's own MIT project — see `THIRD_PARTY_NOTICES.md`). Confirm Brúarhönd HTTP API contract against `e3f126d` HEAD before implementing L5.5 wrapper. |
| **Open architectural questions** | **Q10: Brúarhönd API version pinning.** Seidr-Smidja Brúarhönd is at v0.1. The `seidr brunhand` HTTP interface (REST at 127.0.0.1) may evolve. L5.5 Smiðja should record the Brúarhönd API version it was built against and log a warning if the running daemon reports a different version at connection time. Define version-negotiation behavior at v0.6 scope entry. |
| **Estimated effort** | 2 weeks |

---

### v0.7 — Skrár og Þjóðbrak (Files and Terminal)

| Field | Detail |
|---|---|
| **Codename** | *Skrár og Þjóðbrak* — "files and the machine's voice"; the spirit can touch stored memory and shape the machine directly |
| **Layers / components** | L5.1 Minni (filesystem MCP), L5.2 Skepja (terminal MCP). Two senses simultaneously. |
| **Exit criteria** | Minni MCP sense: `minni.read`, `minni.write`, `minni.list`, `minni.search` tools registered. Path sandbox enforced (no traversal above allowed root). Write operations confirm before execution when `minni.confirm_writes: true`. Skepja MCP sense: `skepja.run` tool registered. Command allow-list and working-dir sandbox enforced. Timeout enforced (no hanging commands). Both senses pass health monitor heartbeat. Agent can request a file read and a shell command in the same turn and receive both results. |
| **Dependencies** | v0.5 (L5 Skilningr MCP hub), v0.6 (second MCP sense already integrated — confirms multi-sense routing works) |
| **Cross-repo deps activated** | None new. Filesystem and shell are OS-native. |
| **Plunder targets** | No new plunder maps. Confirm MCP SDK version at scope entry. |
| **Open architectural questions** | **Q11: MCP SDK version pinning.** `MCP_SDK_PLUNDER_MAP.md` flags version verification as TBD. Resolve: which specific version of the `mcp` pip package (or Rust crate) is the build target for L5 sense subprocesses? Lock this at v0.7 scope entry; record in `THIRD_PARTY_NOTICES.md`. |
| **Estimated effort** | 1–2 weeks |

---

### v0.7.5 — Fyrsta Drykkur við Brunninum (First Drink at the Well)

| Field | Detail |
|---|---|
| **Codename** | *Fyrsta Drykkur við Brunninum* — "first drink at the well"; the spirit gains access to structured knowledge |
| **Layers / components** | L5.9 Mímisbrunnr — file-index backend (light tier) + download manager for ZIM files + starter Norse corpus pack. |
| **Exit criteria** | `mimisbrunnr.search` and `mimisbrunnr.retrieve` tools registered and functional against file-index backend. Norse starter pack (ZIM or JSONL) downloaded and indexed on first run. Agent can query the library and receive a passage. ZIM ingest pipeline (`parser_zim.py`) handles at least one sample ZIM file without crash. `libzim` installed as optional runtime dep via `pip install libzim`; graceful degradation if absent (sense reports NOT_AVAILABLE). `THIRD_PARTY_NOTICES.md` libzim entry confirmed. Optional: MindSpark backend wired if `mimisbrunnr.backend: mindspark` configured (full MindSpark integration is v0.10 — this is a stub). |
| **Dependencies** | v0.7 (Skilningr multi-sense proven), v0.5 (MCP sense hub pattern established) |
| **Cross-repo deps activated** | None at light tier. MindSpark ThoughtForge activation deferred to v0.10. |
| **Plunder targets** | `LIBZIM_PLUNDER_MAP.md` → confirm `pip install libzim` installs correctly on Windows 11. Confirm GPL compliance boundary at install time (dynamic import, not vendored). `KIWIX_TOOLS_PLUNDER_MAP.md` → python-libzim PyPI SPDX **License verification TBD** — Auditor action required before this milestone closes. Run `pip show libzim` and confirm SPDX identifier. |
| **Open architectural questions** | **Q12: kiwix-serve vs direct libzim binding.** Mímisbrunnr can read ZIM files via (A) direct Python libzim bindings (`from libzim import Archive`) or (B) subprocess-spawn `kiwix-serve` and query over localhost HTTP. Option A is faster; Option B is cleaner GPL boundary. Both are legally acceptable. Decision must be made at v0.7.5 scope entry; resolve and document in `KIWIX_TOOLS_PLUNDER_MAP.md` Verification Status. |
| **Estimated effort** | 2–3 weeks |

---

### v0.8 — Opið Vef (The Open Web)

| Field | Detail |
|---|---|
| **Codename** | *Opið Vef* — "the open web"; the spirit can navigate the world's roads |
| **Layers / components** | L5.3 Leið (browser MCP). Playwright or Puppeteer integration. Mímisbrunnr full source manifest catalog. |
| **Exit criteria** | Leið MCP sense: `leid.navigate`, `leid.click`, `leid.type`, `leid.screenshot`, `leid.query` tools registered. Domain allow-list enforced (no navigation outside user-configured domains unless explicitly permitted). Browser subprocess management (spawn, crash-restart). Agent can navigate to a URL, take a screenshot, and extract text. Mímisbrunnr manifest updated with Tier 1 and Tier 2 sources (Wikipedia ZIM, Project Gutenberg, Norse lore sources — see `docs/MIMISBRUNNR.md`). |
| **Dependencies** | v0.7 (Skilningr multi-sense), v0.7.5 (Mímisbrunnr pattern established) |
| **Cross-repo deps activated** | None new. Playwright/Puppeteer are JS runtime deps for the browser sense subprocess. |
| **Plunder targets** | Add Playwright (Apache-2.0) or Puppeteer (Apache-2.0) to `THIRD_PARTY_NOTICES.md` — confirm license at scope entry. Add to plunder map index if a formal plunder map is needed. |
| **Open architectural questions** | **Q13: Playwright vs Puppeteer for Leið.** Playwright (Microsoft, Apache-2.0, multi-browser) or Puppeteer (Google, Apache-2.0, Chromium-only) — both are permissive. Playwright is preferred (broader browser support, better async architecture). Confirm choice at v0.8 scope entry. |
| **Estimated effort** | 2 weeks |

---

### v0.9 — Málari (The Painter)

| Field | Detail |
|---|---|
| **Codename** | *Málari* — "the painter"; the spirit's hand on canvas |
| **Layers / components** | L5.4 Hönd (Photopea MCP). Depends on L5.3 Leið as transport. |
| **Exit criteria** | Hönd MCP sense: `hond.open_image`, `hond.apply_operation`, `hond.export` tools registered. Photopea loaded in browser subprocess (via Leið). Agent can open an image, call a Photopea JavaScript API operation via `app.echoToOE()`, and export the result. Hönd-Leið dependency correctly isolates: Hönd calls Leið as a transport only; Hönd never calls other Leið tools. |
| **Dependencies** | v0.8 (L5.3 Leið operational — Hönd depends on it as transport) |
| **Cross-repo deps activated** | None new. Photopea is a web app; Leið is the transport. |
| **Plunder targets** | None new. Verify Photopea JavaScript API surface (`app.echoToOE()` automation API) against current live version before Forge starts — see `DOMAIN_MAP.md` open question for L5.4. |
| **Open architectural questions** | **Q14: Photopea automation API currency.** `DOMAIN_MAP.md` flags: "Photopea's automation surface (`app.echoToOE()` JavaScript API) needs verification against the current live version before L5.4 implementation begins." Audit and document this at v0.9 scope entry. If Photopea has changed or deprecated the API, adjust L5.4 design accordingly before Forge. |
| **Estimated effort** | 2 weeks |

**The Senses Band (v0.5–v0.9) closes here.** The body has sight, forge, files, terminal, web navigation, and painting. The full creative and informational senses are live.

---

### v0.10 — Langhúsið Ytra (The Longhouse Beyond)

| Field | Detail |
|---|---|
| **Codename** | *Langhúsið Ytra* — "the longhouse beyond"; the spirit's social body in the world of shared presence |
| **Layers / components** | L5.6 Líkami (VRChat MCP). L5.9 Mímisbrunnr — MindSpark backend activated. |
| **Exit criteria** | Líkami MCP sense: `likami.set_expression`, `likami.trigger_animation`, `likami.speak_osc` tools registered. VRChat OSC integration functional. Agent can move the avatar's expression via tool call. Mímisbrunnr MindSpark backend: `mimisbrunnr.backend: mindspark` config activates MindSpark ThoughtForge v1.2.0 as the vector search backend. `mimisbrunnr.search` returns semantically ranked results from MindSpark's indexed corpus. |
| **Dependencies** | v0.7 (multi-sense Skilningr), v0.7.5 (Mímisbrunnr base established), v0.5 (MCP pattern) |
| **Cross-repo deps activated** | **MindSpark ThoughtForge** (`C:/Users/volma/runa/MindSpark_ThoughtForge`, v1.2.0) — wired as optional Mímisbrunnr backend via HTTP. HERETIC calls MindSpark's HTTP interface; never imports its Python source. License: MIT (Volmarr's own). Optional: **WYRD Protocol** (`C:/Users/volma/runa/WYRD-Protocol`) — if user enables L5.8 custom MCP with WYRD as the server, the world-model sense becomes available. This is user-configured, not HERETIC-owned. |
| **Plunder targets** | `LIBZIM_PLUNDER_MAP.md` → MindSpark integration adds `sentence-transformers` (Apache-2.0, **License verification TBD**) and possibly `faiss-cpu` (MIT, **License verification TBD**) as optional runtime deps via MindSpark. Confirm and add to `THIRD_PARTY_NOTICES.md`. |
| **Open architectural questions** | **Q15: VRChat OSC vs SDK.** `DOMAIN_MAP.md` flags: "VRChat API surface for agent-driven avatar control (OSC vs SDK vs both) needs verification at v0.10 scope entry." OSC is simpler and does not require VRChat SDK integration; SDK allows more control but adds a dependency layer. Audit VRChat's current OSC support and SDK availability before Forge. **Q16: MindSpark HTTP interface.** MindSpark v1.2.0 has a defined HTTP API. Confirm endpoint, request/response schema, and auth model before wiring into Mímisbrunnr at v0.10. |
| **Estimated effort** | 2–3 weeks |

---

### v0.11 — Bréfasamtök (Correspondence)

| Field | Detail |
|---|---|
| **Codename** | *Bréfasamtök* — "the letter-gathering"; the spirit's formal channel to the wider world |
| **Layers / components** | L5.7 Boð (AgentMail MCP). SMTP + IMAP integration. |
| **Exit criteria** | Boð MCP sense: `bod.send`, `bod.read_inbox`, `bod.read_message`, `bod.reply` tools registered. SMTP send functional. IMAP read functional. Credentials loaded from env vars (never from `heretic.yaml` plaintext). Agent can read an email and send a reply via tool calls. Domain and recipient allow-list enforced (no email to unconfigured addresses). |
| **Dependencies** | v0.7 (Skilningr multi-sense proven — this is a simpler sense than most) |
| **Cross-repo deps activated** | None new. SMTP/IMAP are protocol libraries only. |
| **Plunder targets** | Add email library (Python `aiosmtplib` + `aioimaplib`, MIT) to `THIRD_PARTY_NOTICES.md` at scope entry. |
| **Open architectural questions** | None blocking — Boð is a straightforward protocol integration. The only design question is whether to use OAuth2 (for Gmail/Outlook) or SMTP+IMAP app passwords; this is a config option, not an architecture question. |
| **Estimated effort** | 1 week |

---

### v1.0 — Fyrsta Birtingarmynd (First Manifestation)

| Field | Detail |
|---|---|
| **Codename** | *Fyrsta Birtingarmynd* — "first manifestation"; the body is whole, the gate is open |
| **Layers / components** | L5.8 Nýr Limr (custom MCP plugin slot). Full system polish. Public release prep. |
| **Exit criteria** | Nýr Limr plugin slot: user can define a custom MCP server in `heretic.yaml` with `command`, `args`, `env`; it starts, registers its tools, and they are callable. HERETIC never needs to know what the plugin does — it is a black box. Full system integration test: all senses active simultaneously, all layers stable, voice round-trip works, agent uses multiple senses in one turn. README updated to reflect current state. `THIRD_PARTY_NOTICES.md` fully audited — all "License verification TBD" entries resolved. MIT license confirmed clean. `CHANGELOG.md` first version entry. Packaging: installable binary for Windows 11 via Tauri bundler. Release notes authored. All canonical docs still match the code (Scribe verification pass). |
| **Dependencies** | All prior milestones v0.0–v0.11 |
| **Cross-repo deps activated** | All prior cross-repo slots active. WYRD Protocol potentially wired as an example custom MCP via L5.8 in the release documentation. |
| **Plunder targets** | Final audit of all 8 plunder maps against actual code. All "License verification TBD" entries in `THIRD_PARTY_NOTICES.md` resolved. |
| **Open architectural questions** | **Q17: Plugin security boundary.** L5.8 Nýr Limr loads user-provided MCP server processes. Define the security posture: does HERETIC sandbox these processes (limited network, limited filesystem)? Or is it user-trusts-their-own-plugins (no sandbox, explicit warning in docs)? For v1.0, the pragmatic answer is the latter — document it clearly. A future version can add sandboxing. Resolve at v1.0 scope entry. |
| **Estimated effort** | 2–3 weeks |

---

### v1.x+ — Nýir Liðir (New Limbs)

| Field | Detail |
|---|---|
| **Codename** | *Nýir Liðir* — "new limbs"; the body grows as the community grows |
| **Layers / components** | Whatever senses users build via L5.8, whatever refinements emerge from release feedback |
| **Nature** | Rolling community-driven development. No fixed scope. Each new sense should go through the standard Mythic Engineering sense lifecycle: Skald names it, Architect defines its boundary, Cartographer maps its connections, Forge builds it, Auditor tests it, Scribe records it. |
| **Exit criteria** | Per-sense, per-feature. No milestone-level exit criteria for this band. |
| **Cross-repo deps** | Whatever the community or Volmarr chooses. WYRD Protocol as a first-class L5.8 plugin is the most likely early v1.x expansion. |
| **Estimated effort** | Rolling, open |

---

### v2.x — (Tafarlegar Draumer) Deferred Dreams

| Field | Detail |
|---|---|
| **Codename** | *Tafarlegar Draumer* — "deferred dreams"; the grander visions that the body is not yet ready for |
| **Nature** | Stretch goals. Only if user/community demand is clear and Volmarr decides to open them. None of these should begin until v1.0 is fully stable. |
| **Contents** | See §4 Deferred Features List for the why behind each deferral. In brief: UE5 photoreal environment, MetaHuman avatar rendering, in-window VRM (three-vrm), multi-user coven ceremonies. |
| **Exit criteria** | Not defined. Each would require a full new Skald/Architect design pass before Forge. |

---

## §2. Phase-Gate Work Breakdown Structure

*Inherited and adapted from `proposed_system_report/08` WBS format — see `PRIOR_PLANNING_TRIAGE.md` CARRY FORWARD note.*

Each phase-gate is a checkpoint where the current band of milestones must be evaluated before opening the next band. The gate is not bureaucracy — it is the Auditor asking: "does what we built match what we said we would build?"

---

### Gate 0 — Foundation Sealed (after v0.4)

| Checklist item | Owner |
|---|---|
| All v0.0 docs are sealed and accurate against current code state | Scribe |
| L0 Grunnr config system has ≥ 80% test coverage | Auditor |
| L1 Bifröst connects to Hermes live, tool call round-trip proven | Auditor |
| L2 Rödd voice turn works end-to-end (speak → Hermes reply → speak back) | Auditor |
| L4 Vébond ceremony UI matches `docs/CEREMONY.md` state machine | Auditor |
| `THIRD_PARTY_NOTICES.md` — no "License verification TBD" entries for v0.0–v0.4 deps | Scribe |
| All Q1–Q8 open architectural questions resolved and documented | Architect |
| `TASK_HERETIC_v0.1_BOOTSTRAP.md` §2 pending items: pre-manifesto triage done, codex branches dispositioned | Scribe |
| Git: all v0.0–v0.4 work on `development`; tag `v0.4.0` | Forge |

**If gate passes:** Senses Band (v0.5–v0.9) opens.

---

### Gate 1 — Senses Band Complete (after v0.9)

| Checklist item | Owner |
|---|---|
| All five senses (Sjón, Smiðja, Minni, Skepja, Leið, Hönd, Mímisbrunnr) pass health monitor heartbeat | Auditor |
| Multi-sense agent turn proven: agent uses ≥ 2 senses in one tool-call round-trip | Auditor |
| Graceful degradation confirmed: disabling any sense does not crash others | Auditor |
| L5.4 Photopea API currency confirmed (Q14 resolved) | Architect |
| GPL compliance verified for libzim / kiwix-tools: no GPL code in `vendor/`; python-libzim PyPI SPDX resolved | Scribe + Auditor |
| `THIRD_PARTY_NOTICES.md` — all v0.5–v0.9 deps confirmed | Scribe |
| Q9–Q14 resolved and documented | Architect |
| Tag `v0.9.0` | Forge |

**If gate passes:** Full Body Band (v0.10–v1.0) opens.

---

### Gate 2 — v1.0 Release (after v1.0)

| Checklist item | Owner |
|---|---|
| All "License verification TBD" entries in `THIRD_PARTY_NOTICES.md` resolved — zero TBD entries remain | Scribe |
| MIT license grant clean — no GPL/AGPL code in `vendor/` or `heretic/` | Auditor |
| All 15 canonical docs match the current code state | Scribe |
| Full integration test: all 9 senses active, agent uses 3+ senses in one session | Auditor |
| L5.8 Nýr Limr plugin slot tested with a user-provided example MCP server | Auditor |
| Q17 security boundary documented in README | Architect |
| `CHANGELOG.md` v1.0 entry complete | Scribe |
| Windows 11 installable binary packages tested | Forge |
| `README.md` post-manifesto update complete (pre-manifesto framing superseded notice present) | Scribe |
| Tag `v1.0.0` | Forge |

**If gate passes:** v1.x+ rolling band opens. Community can build.

---

## §3. Risk Register

*Top 5 risks per milestone band. Risk level: High (H), Medium (M), Low (L). Mitigation strategies are architectural, not operational.*

---

### Band: Foundation (v0.0–v0.4)

| # | Risk | Level | If realized | Mitigation |
|---|---|---|---|---|
| R-F1 | **Hermes tool-call format mismatch.** Hermes at `100.101.39.30:8643/v1` uses deprecated `functions` key instead of `tools` array, or returns non-standard `tool_calls` structure. | H | L1 Bifröst tool dispatch broken from day one. | Verify with a minimal probe call before Forge starts on v0.1 (Q2). `HERMES_AGENT_PLUNDER_MAP.md` documents this as an open question to resolve at v0.1 scope entry. |
| R-F2 | **Tailscale connectivity unreliable on Windows.** HERETIC's warm path depends on Tailscale WireGuard routing to the Pi at `100.101.39.30`. If Tailscale drops or Windows firewall blocks it, L1 Bifröst cannot connect. | H | No agent connection possible. | L1 Bifröst must expose a fallback direct-HTTPS mode. `heretic.yaml` `bifrost.tailscale.prefer: false` allows direct endpoint config. Test both modes at v0.1. |
| R-F3 | **ChatterBox license is GPL.** If ChatterBox TTS is GPL-licensed (or uses GPL components), the current external-HTTP pattern is still safe (we call it over a network, never import its source), but `THIRD_PARTY_NOTICES.md` must be corrected before v0.2 ships. | M | Incorrect license notice; potentially embarrassing at v1.0 if uncorrected. | Resolve ChatterBox license (Q3) at v0.2 scope entry — before code ships. The external-service pattern is legally safe regardless; the risk is documentation only. |
| R-F4 | **Rust vs Python language choice for L0/L1 prototype.** If v0.1 starts as a Python CLI prototype and Tauri Rust backend is added later, there is a risk of permanent Python scaffolding remaining in production. | M | Two-language split in the core; maintenance burden. | Q1 must be resolved at v0.1 scope entry. If Python prototype is chosen, mark it explicitly as a throw-away scaffold with a defined cutover point (v0.4 Tauri migration). |
| R-F5 | **VAD latency too high for conversational use.** Whisper.cpp VAD on Windows without GPU acceleration may add > 1000ms to the warm-path SLO, breaking the <1200ms target. | M | Voice conversation feels laggy; degraded UX. | Q5 and Q6 (Whisper integration + VAD strategy) resolved before v0.3 Forge. Benchmark VAD on target hardware (Windows 11 laptop, no discrete GPU) with a 10-second clip before full implementation. If latency fails, try Silero VAD as an alternative. |

---

### Band: Senses (v0.5–v0.9)

| # | Risk | Level | If realized | Mitigation |
|---|---|---|---|---|
| R-S1 | **libzim GPL isolation violated by accident.** A future contributor adds `import libzim` at the top level of a HERETIC source file (not isolated to `parser_zim.py`), unintentionally spreading the GPL import footprint. | H | License contamination — HERETIC's MIT grant is compromised. | The GPL Risk Register in `LIBZIM_PLUNDER_MAP.md` documents this. Architecture rule: `import libzim` is only ever inside `heretic/sense_hub/library/mimisbrunnr/`, behind `try/except ImportError`. CI must lint for `import libzim` outside the allowed module. |
| R-S2 | **python-libzim PyPI SPDX is not GPL-3.0 — it may be GPL-2.0-or-later (same as the C++ lib).** If the pip package's SPDX identifier is different from the repository claim, `THIRD_PARTY_NOTICES.md` has the wrong entry. | M | Incorrect license record; possible compliance issue if SPDX is something unexpected. | `KIWIX_TOOLS_PLUNDER_MAP.md` flags this as License verification TBD — Auditor action required before v0.7.5. Run `pip show libzim` at first install and verify. |
| R-S3 | **Seidr-Smidja Brúarhönd API changes before v0.6.** Seidr-Smidja is actively developed. The HTTP interface that L5.5 Smiðja wraps may change between now and v0.6. | M | L5.5 wrapper broken at the seam. | Q10: version-negotiation check. At L5.5 connection time, compare daemon-reported Brúarhönd API version against the version L5.5 was built against. Log warning if different; fail loudly if incompatible. |
| R-S4 | **Photopea changes or restricts its JavaScript automation API.** Photopea is a commercial web app; its `app.echoToOE()` API is not contractually guaranteed. | M | L5.4 Hönd broken or requires significant rework. | Q14 audit at v0.9 scope entry — before any Forge work. If the API has changed, adjust the driver. If it has been removed, investigate alternative canvas automation strategies. |
| R-S5 | **MCP SDK version mismatch between L5 senses.** If different senses are built against different versions of the `mcp` pip package and the MCP protocol version they negotiate differs, the router may fail to dispatch correctly. | M | Tool calls fail silently or with cryptic errors. | Q11: lock MCP SDK version at v0.7 scope entry. All senses use the same pinned version. Record in `requirements.txt` / `pyproject.toml`. |

---

### Band: Full Body (v0.10–v1.0)

| # | Risk | Level | If realized | Mitigation |
|---|---|---|---|---|
| R-B1 | **VRChat OSC API does not support the required avatar control surface.** If VRChat's OSC implementation does not expose expression blendshapes or avatar state at the level needed, L5.6 Líkami is limited. | H | L5.6 has fewer usable tools than expected; agent social embodiment is limited. | Q15 audit at v0.10 scope entry. If OSC is insufficient, investigate VRChat SDK (heavier dependency). If neither is sufficient, scope L5.6 down to basic presence (join/leave, chat, minimal expression) and note the limitation in docs. |
| R-B2 | **MindSpark HTTP interface changed in a v1.3+ update.** MindSpark is actively developed. Its HTTP API may change between now and v0.10. | M | L5.9 MindSpark backend wiring fails. | Q16: pin MindSpark to v1.2.0 in config docs and test against that version. Note upgrade path in `THIRD_PARTY_NOTICES.md`. |
| R-B3 | **"License verification TBD" entries remain unresolved at v1.0.** If ChatterBox, python-libzim, faiss-cpu, or sentence-transformers licenses are not confirmed before the v1.0 release gate, `THIRD_PARTY_NOTICES.md` ships with incomplete notices. | M | Legal risk at distribution; potential embarrassment; may require recall. | Gate 2 checklist item: zero TBD entries allowed at v1.0. The Scribe pass before release closes this. |
| R-B4 | **L5.8 Nýr Limr plugin executes malicious user-provided MCP server.** A user-provided plugin server has full process-level access on the laptop. If a malicious plugin is loaded, it could exfiltrate data. | M | Security incident for the user. | Q17: v1.0 documents clearly that user-provided plugins are fully trusted and have no sandbox. The README must include a prominent security note. Future sandboxing is a v1.x hardening task. |
| R-B5 | **THIRD_PARTY_NOTICES.md missing an attribution for a dep added during Senses/Full-Body builds.** Fast Forge sessions may add a new pip package without updating the notices file. | L | Attribution gap; minor compliance issue. | Scribe closing ritual: every Forge session that adds a new dependency must produce a `THIRD_PARTY_NOTICES.md` addendum before the commit is sealed. Auditor verifies at each gate. |

---

### Band: Stretch (v1.x+, v2.x)

| # | Risk | Level | If realized | Mitigation |
|---|---|---|---|---|
| R-X1 | **Community-built L5.8 plugins introduce GPL dependencies.** A popular community MCP plugin might `pip install` GPL packages in its subprocess. | M | Legal confusion about HERETIC's license (HERETIC itself is MIT; the plugin is the user's). | Document clearly: HERETIC loads plugins as black-box external processes. The plugin's license is the user's/author's concern, not HERETIC's. HERETIC never imports plugin source code. |
| R-X2 | **UE5 / MetaHuman v2.x stretch goal opens a licensing minefield.** Epic's Unreal Engine license is not open-source. | H (if opened) | v2.x must treat UE5 as an external application (same pattern as VRChat) — never bundle UE5 code. | v2.x is only opened if demand is clear. The body-not-brain principle applies: HERETIC talks to a running UE5 process via an external API, never links it. |
| R-X3 | **Scope creep from v1.x community requests toward brain features.** Users may request HERETIC own persona systems, agent memory, character cards. | M | HERETIC drifts from its manifesto. | The manifesto is sealed. Any proposal to add brain features to HERETIC must be explicitly rejected with reference to `BODY_MANIFESTO.md`. These features belong to the spirit (the agent), not the body. |
| R-X4 | **in-window VRM (three-vrm) remains technically tempting.** three-vrm (MIT) is a well-maintained WebGL library. The temptation to add avatar rendering inside HERETIC's window may resurface. | L | In-window VRM added despite manifesto ruling it out. | The deferred-features list (§4) records the decision and its reasoning. The manifesto says the spirit's avatar lives in VRChat (L5.6), not in HERETIC's window. |
| R-X5 | **WYRD Protocol API changes before L5.8 integration.** WYRD Protocol is at v1.0.0 — stable, but Volmarr may extend it. | L | L5.8 WYRD custom MCP config needs updating. | WYRD as a custom MCP plugin is user-configured; config changes are a user responsibility. HERETIC's L5.8 Nýr Limr slot is protocol-agnostic. |

---

## §4. Deferred Features List

These features were considered for v1.0 and explicitly dropped. The reasoning is preserved so future sessions do not re-litigate settled decisions.

---

### D-1: Persona System

**What it would have been:** HERETIC owning a character identity layer — storing the agent's name, personality summary, voice style, and preferred interaction patterns. From the April 2026 brain-framing plans: a `persona-compiler` service that injects persona context into every prompt.

**Why dropped:** The manifesto's principle: *"The spirit brings its mind."* The persona belongs to the agent (spirit), not to the body. HERETIC does not own who the agent is. If Hermes has a persona, that persona lives in Hermes — in its system prompt, its model weights, its memory on the Pi. HERETIC does not know it and should not. Implementing a persona layer in HERETIC would mean the body presumes to define the spirit's identity. That is the wrong architecture.

**Who owns it instead:** The inhabiting agent. Users configure persona in the agent (e.g., Hermes system prompt, OpenClaw character settings). If a skill like Viking_Girlfriend_Skill_for_OpenClaw is running, it owns the persona. HERETIC receives whoever arrives through the Bifröst and does not ask for identification.

**Future path:** Not planned. If users genuinely need a persona-injection helper, it would be a L5.8 custom MCP plugin, not a HERETIC core feature.

---

### D-2: Agent Memory

**What it would have been:** HERETIC owning a conversation persistence and memory compaction layer — storing the agent's conversation history, running semantic summaries, and injecting compressed memory into the context window across sessions.

**Why dropped:** The manifesto's principle: *"The spirit brings its mind."* Conversation history belongs to the agent. Hermes on the Pi manages its own conversation state. HERETIC does not persist the `messages` array; it sends a fresh context on each ceremony (or the agent carries its own continuation). If users want persistent memory, they configure their agent accordingly.

**Who owns it instead:** The agent runtime (Hermes, OpenClaw). MindSpark ThoughtForge (`C:/Users/volma/runa/MindSpark_ThoughtForge`) is a memory system — but it is the agent's memory, accessed optionally via Mímisbrunnr's MindSpark backend (L5.9) as a read-only knowledge source, not as HERETIC's memory persistence.

**Future path:** Not planned. Memory is not HERETIC's domain.

---

### D-3: Character Cards

**What it would have been:** A standard format for defining an AI character's identity, personality, backstory, and behavioral guidelines that HERETIC stores and injects — similar to SillyTavern's character card system.

**Why dropped:** Same manifesto principle: *"the spirit IS the character."* HERETIC does not own character definitions. Additionally, SillyTavern's character card format is tightly coupled to SillyTavern's AGPL-licensed code — see `SILLYTAVERN_PLUNDER_MAP.md`. Even if character cards were desired, the SillyTavern implementation cannot be used or adapted.

**Who owns it instead:** The agent, or the user's configuration of the agent. If a user wants character card behavior, they configure it in Hermes, in OpenClaw, or in the Viking_Girlfriend_Skill. That is the spirit's domain.

**Future path:** Not planned. Character cards are not HERETIC's domain.

---

### D-4: Native Gateway RPC Adapters (Hermes Native + OpenClaw Native)

**What it would have been:** Instead of speaking OpenAI-compat HTTP to Hermes and OpenClaw, HERETIC would implement native protocol adapters for each — speaking Hermes's native gRPC/WebSocket protocol and OpenClaw's native TypeScript API directly, for lower latency and richer feature access.

**Why dropped:** The manifesto and architectural decision table: *"OpenAI-compatible is enough. Both speak it. Native RPC adapters become v2.x stretch only if needed."* The OpenAI-compat HTTP protocol works for both agents in v1. The overhead of implementing two native adapters (in addition to the standard Bifröst) is not justified by the latency benefit (50-100ms Tailscale round-trip dominates; adapter savings would be 5-10ms). Native adapters also couple HERETIC to specific agent implementations, breaking the agent-agnostic principle.

**Who owns it instead:** The Bifröst contract (`AGENT_AGNOSTIC_PROTOCOL.md`) is the standard. Any agent that speaks it can inhabit HERETIC.

**Future path:** v2.x stretch, only if measured latency analysis shows native adapters are necessary. Requires a formal case.

---

### D-5: LiteLLM Wire-Format Normalizer

**What it would have been:** A LiteLLM-based shim inside HERETIC's L1 Bifröst that would normalize multiple different LLM API formats (OpenAI, Anthropic, Cohere, Ollama, etc.) into a single internal protocol — allowing HERETIC to support any model, not just OpenAI-compat endpoints.

**Why dropped:** Dropped for v1 per architectural decision table. LiteLLM adds a significant dependency and complexity layer. v1 requires only OpenAI-compat. If a user wants to connect to Claude (Anthropic API), they run a proxy or use an OpenAI-compat shim on their side — HERETIC does not need to know. The agent-agnostic principle is satisfied by OpenAI-compat alone for v1.

**Who owns it instead:** The user's infrastructure. LiteLLM is a fine tool; it just belongs on the user's side or in the agent's setup, not in HERETIC's Bifröst.

**Future path:** v1.x if community demand is clear. Would be implemented as a L1 Bifröst adapter variant, not as a replacement for the OpenAI-compat default.

---

### D-6: In-Window VRM Avatar (three-vrm)

**What it would have been:** An embedded WebGL VRM avatar rendered inside HERETIC's Tauri window using the `three-vrm` JavaScript library (MIT) — giving the spirit a visible face within the HERETIC UI.

**Why dropped:** The manifesto: *"the agent's avatar lives in VRChat (via L5.6) — there's no need to render one in HERETIC's window."* The HERETIC UI (L4 Vébond / Eldahús) is a summoning circle — the ceremonial interface for humans to manage the body's state. It is not a social presence window. The spirit's social body is in VRChat, Blender, or wherever the spirit inhabits. Mixing a VRM renderer into the control UI confuses the roles.

**Who owns it instead:** VRChat (L5.6 Líkami) for social embodiment, or Seidr-Smidja (L5.5 Smiðja) for 3D creation. The spirit's visible form exists in the spirit's domain.

**Future path:** v2.x stretch, if users clearly want a companion face in the HERETIC window. Would require Skald and Architect to revisit the UI philosophy first.

---

### D-7: Photoreal UE5 Environment / MetaHuman

**What it would have been:** A photorealistic rendering environment using Unreal Engine 5 and MetaHuman, accessible from HERETIC, giving the spirit a photorealistic avatar and environment.

**Why dropped:** Manifesto: *"Not central. v2.x stretch only if user demand. Manifesto routes embodiment via existing apps (VRChat, Blender), not custom UE5 environment."* Unreal Engine 5 is a massive dependency (hundreds of GB), requires significant hardware (GPU), and is not open-source (Epic proprietary license). It would overwhelm the body-is-light-and-fast design principle. HERETIC's cold-start target is 2 seconds; adding a UE5 bridge would make that impossible.

**Who owns it instead:** If a user wants UE5 embodiment, they run UE5 themselves and expose an API. HERETIC could connect via L5.8 custom MCP or a future L5 UE5 sense. That is a v2.x architectural question.

**Future path:** v2.x stretch, only with clear demand and a proper Architect design pass. The body-not-brain principle still applies: HERETIC talks to a UE5 process via an API; it never bundles or ships UE5.

---

## §5. Milestone Topology Summary

```
v0.0 Grunnr Sáð (docs)
  │
  ▼
v0.1 Fyrsta Samfélag ──── L0 + L1 (CLI loop, agent connection)
  │
  ▼
v0.2 Fyrsta Rödd Út ───── L2 Tunga (TTS)
  │
  ▼
v0.3 Fyrsta Hlust ──────── L2 Hlust (STT)
  │
  ▼
v0.4 Summonarhringar ───── L4 Vébond/Eldahús (Tauri UI, ceremony)
  │
  ├──► GATE 0 — Foundation Sealed ◄──────────────────────
  │
  ▼
v0.5 Fyrsta Sjón ───────── L3 Sjón + L5 Skilningr (screen capture, first MCP)
  │
  ▼
v0.6 Hönd at Smiðju ────── L5.5 Smiðja (Seidr-Smidja Brúarhönd)
  │
  ▼
v0.7 Skrár og Þjóðbrak ── L5.1 Minni + L5.2 Skepja (filesystem + terminal)
  │
  ▼
v0.7.5 Fyrsta Drykkur ──── L5.9 Mímisbrunnr light (ZIM + Norse corpus)
  │
  ▼
v0.8 Opið Vef ──────────── L5.3 Leið (browser MCP)
  │
  ▼
v0.9 Málari ────────────── L5.4 Hönd (Photopea MCP, uses Leið transport)
  │
  ├──► GATE 1 — Senses Band Complete ◄───────────────────
  │
  ▼
v0.10 Langhúsið Ytra ───── L5.6 Líkami (VRChat) + Mímisbrunnr MindSpark backend
  │
  ▼
v0.11 Bréfasamtök ──────── L5.7 Boð (AgentMail)
  │
  ▼
v1.0 Fyrsta Birtingarmynd ─ L5.8 Nýr Limr (custom plugin) + polish + release
  │
  ├──► GATE 2 — v1.0 Release ◄────────────────────────────
  │
  ▼
v1.x+ Nýir Liðir (rolling) ─ community senses + refinements
  │
  ▼
v2.x Tafarlegar Draumer ─── stretch goals (UE5, in-window VRM — only if warranted)
```

---

*Roadmap authored by Eirwyn Rúnblóm, Scribe for Vibe Coding, 2026-05-07.*
*The body grows limb by limb. Each milestone is a new faculty, not a deadline. The spirit waits at the Bifröst gate until the body is ready to receive it — and then it enters.*
