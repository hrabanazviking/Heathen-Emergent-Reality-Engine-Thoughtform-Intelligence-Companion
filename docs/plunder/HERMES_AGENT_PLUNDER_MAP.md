# Hermes Agent — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** architectural reference only — no code plundered, none planned; documents the protocol contract HERETIC speaks to Hermes

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | Hermes Agent (NousResearch) |
| Repository | https://github.com/NousResearch/hermes-agent |
| Stars | ~137k (verified 2026-05-07 — approximate) |
| Primary language | Python |
| Primary maintainer | NousResearch |
| License | MIT |
| License URL | https://github.com/NousResearch/hermes-agent/blob/main/LICENSE |
| License verification status | **Verified MIT 2026-05-07** (LICENSE file in repo confirms MIT, copyright NousResearch) |

**Physical location in HERETIC's ecosystem:** Hermes Agent runs on the Raspberry Pi (`100.101.39.30:8643/v1`). It is the primary inhabiting spirit. It is NOT part of HERETIC's codebase — it is the remote agent that HERETIC's body serves.

---

## Upstream License

**MIT License.** Permissive, compatible with HERETIC's MIT license. Even if code were plundered (which it is not), there would be no licensing obstacle.

---

## Compatibility Verdict

**CLEAN — and not applicable.** Hermes Agent is **not plundered as code**. It is the inhabiting spirit; HERETIC is the body that receives it. This map exists to document the protocol relationship, confirm the license, and record what HERETIC reads from the Hermes architecture to understand the contract it must honor.

---

## Nature of This Relationship

This is an **architectural reference plunder map**, not a source adaptation. The relationship between HERETIC and Hermes Agent is:

- Hermes Agent provides: an OpenAI-compatible API endpoint at `/v1/chat/completions`.
- HERETIC's L1 Bifröst connects to that endpoint as an HTTP client.
- The protocol between them is documented in `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md`.
- Hermes Agent's source code is never imported into, linked with, or vendored in HERETIC.
- Hermes Agent's architecture is studied to confirm that HERETIC's Bifröst contract assumptions are valid — nothing more.

The manifesto's principle governs this entirely: **"The spirit doesn't need to know what kind of body it wears. It speaks its tongue and the body listens."** And from the body's side: the body doesn't need to know what kind of spirit it hosts — it only needs to know the protocol. Hermes is one spirit among many possible spirits; HERETIC is agent-agnostic by design.

---

## What We Study (Not Plunder)

### Protocol contract verification
- Hermes Agent's OpenAI-compatible API surface — confirmed that it speaks `/v1/chat/completions` with standard `messages`, `tools`, `tool_choice: auto`, and streaming SSE responses.
- Hermes Agent's tool/function calling format — confirmed it uses the current `tools` array format (not the deprecated `functions` format). This informs L1 Bifröst's request construction.
- Hermes Agent's MCP integration capability — confirmed it can consume MCP tool schemas in the `tools` array, making HERETIC's sense MCP servers directly callable by Hermes. This is the key architectural confirmation for v0.1.
- Authentication: Bearer token in `Authorization` header — confirmed standard HTTP Bearer auth.
- Streaming: SSE `data: {...}` chunks with `data: [DONE]` termination — confirmed standard OpenAI streaming format.

### What HERETIC reads from the Hermes architecture
- The verified endpoint: `http://100.101.39.30:8643/v1` (Tailscale IP, confirmed live as of 2026-05-07).
- The model name used in requests: `coding` (as verified — configured in `heretic.yaml` as `bifrost.model`).
- The API key: `hermes` (as verified — configured as env var `HERETIC_AGENT_KEY` in the production setup; never hardcoded).
- The capability probe response: Hermes is expected to call `heretic_probe` tool when `?tool_use` is probed, confirming MCP tool support.

### What the Pi-based Hermes setup means for v0.1
- Network latency between laptop and Pi over Tailscale: ~50-100ms round trip (LAN-like over WireGuard) — this feeds directly into the warm-path SLO budget analysis in `DATA_FLOW.md`.
- Hermes runs a full Hermes-series model (GGUF-quantized or full, depending on Pi hardware) — inference latency ~200-800ms typical — factored into the v0.3 STT latency budget.
- Hermes manages conversation history on the Pi — HERETIC does not need to persist the message array across ceremonies (confirmed non-goal in `ARCHITECTURE.md` §10).

---

## What We DO NOT Plunder

- Any Hermes Agent Python source code — not needed, not desirable. The spirit brings its own implementation.
- Hermes Agent's memory architecture — HERETIC explicitly does not own agent memory (manifesto principle).
- Hermes Agent's persona or personality system — belongs to the spirit, not the body.
- Any Hermes model weights — these are NousResearch-licensed separately and are not part of the agent source code.
- Hermes Agent's system prompt templates — these are the spirit's mind, not HERETIC's concern.

---

## Local Domain Ownership

| HERETIC layer | True Name | Relationship to Hermes |
|---|---|---|
| L1 Bifröst | Bifröst (bifrost) — the shimmering bridge | The sole point of contact with Hermes. Bifröst sends `/v1/chat/completions` requests and receives responses. No other layer speaks to Hermes. |

Hermes Agent is **external to all HERETIC layers.** It is listed in `docs/architecture/ARCHITECTURE.md` §9 (Cross-Repo Plug-In Slots) as `L1 Bifröst — primary spirit, Live.`

---

## Public Interface (How HERETIC Speaks to Hermes)

The full protocol is documented in `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md`. The summary:

- HERETIC → Hermes: `POST /v1/chat/completions` with `{model, messages, tools, tool_choice, stream, max_tokens}`.
- Hermes → HERETIC: SSE stream of completion chunks, ending with `data: [DONE]`.
- Tool call loop: Hermes emits `finish_reason: tool_calls` → HERETIC dispatches to L5 Skilningr → result returned as `role: tool` message → next completion request sent.
- Heartbeat: HERETIC sends minimal keepalive every 30s (configurable, disabled by default for cloud agents to avoid billing).

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Not applicable — no Hermes code is in HERETIC's repo |
| THIRD_PARTY_NOTICES.md entry | Yes — Hermes Agent should be listed as the primary spirit backend with its MIT license and GitHub URL, noting it is an external runtime service, not distributed code |
| In-source headers | Not applicable |
| Trademark | NousResearch is the trademark holder. HERETIC may say "Hermes Agent by NousResearch is a supported agent backend" but must not imply NousResearch endorses or is affiliated with HERETIC. The body does not claim to be the spirit. |

---

## Verification Status

- License re-verified: **2026-05-07** — MIT confirmed at https://github.com/NousResearch/hermes-agent/blob/main/LICENSE
- Endpoint verified live: **2026-05-07** — `http://100.101.39.30:8643/v1` responds (confirmed in `TASK_HERETIC_v0.1_BOOTSTRAP.md` §2).
- OpenAI-compat API surface: **confirmed** — Hermes speaks the required subset. Details in `AGENT_AGNOSTIC_PROTOCOL.md`.
- Open question: Hermes Agent's tool-call format (confirm `tools` array, not deprecated `functions` key, at time of v0.1 build). Verify against live endpoint with a minimal probe call.

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*Hermes is the spirit. This map is the body's record of what it knows about the spirit who enters it first.*
*We do not take from Hermes. We receive it.*
