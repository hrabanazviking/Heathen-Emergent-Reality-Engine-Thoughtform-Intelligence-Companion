# OpenClaw — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** architectural reference only — no code plundered, none planned; documents the Tier 1 alternate spirit and its OpenAI-compat protocol surface

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | OpenClaw |
| Repository | https://github.com/openclaw/openclaw |
| Stars | ~369k (verified 2026-05-07 — approximate) |
| Primary language | TypeScript (Node.js) |
| Primary maintainer | OpenClaw community |
| License | MIT |
| License URL | https://github.com/openclaw/openclaw/blob/main/LICENSE |
| License verification status | **Verified MIT 2026-05-07** (LICENSE file in repo confirms MIT) |

**Physical location in HERETIC's ecosystem:** OpenClaw is a second-tier inhabiting agent — an alternative spirit a user may run instead of, or alongside, Hermes. Like Hermes, it runs externally (on the user's local machine, a server, or a Pi) and connects to HERETIC via L1 Bifröst. It is NOT part of HERETIC's codebase.

---

## Upstream License

**MIT License.** Permissive, compatible with HERETIC's MIT license. Even if code were plundered (which it is not), there would be no licensing obstacle.

---

## Compatibility Verdict

**CLEAN — and not applicable.** OpenClaw is **not plundered as code**. It is an alternative inhabiting spirit. This map documents the architectural reference relationship and the OpenAI-compat protocol surface HERETIC speaks to reach it.

---

## Nature of This Relationship

OpenClaw is to HERETIC what Hermes is: a spirit that inhabits the body. The relationship is identical in structure:

- OpenClaw provides an OpenAI-compatible API endpoint.
- HERETIC's L1 Bifröst connects to that endpoint.
- The protocol is the same `/v1/chat/completions` contract documented in `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md`.
- OpenClaw's source is never imported, linked, or vendored by HERETIC.

The agent-agnostic principle is explicit in the manifesto: "Any AI system that can speak OpenAI-compatible API can inhabit the body." OpenClaw is one such system.

---

## What We Study (Not Plunder)

### Protocol contract verification
- OpenClaw's OpenAI-compatible API surface — confirmed it speaks `/v1/chat/completions`. Verify specific tool-call format at time of v0.1 testing (same verification checklist as Hermes: `tools` vs `functions` format, streaming SSE, `role: tool` message handling).
- OpenClaw's MCP tool integration — confirm it processes the `tools` array and returns `tool_calls` in `finish_reason: tool_calls` format. This is essential for HERETIC's sense MCP servers to be callable via OpenClaw.
- OpenClaw's agent loop architecture — studied as an architectural reference for understanding how an OpenAI-compat agent runtime processes multi-turn tool use. This informs how HERETIC designs the tool call loop in L1 Bifröst (max rounds, error handling, partial tool result behavior).
- OpenClaw's Node.js architecture — useful reference for understanding the skill/tool system that informs how HERETIC's sense MCPs should describe themselves for maximum compatibility with TypeScript-based agents.

### What HERETIC derives from studying OpenClaw
- Confirmation that the OpenAI-compat format is truly sufficient for both primary agents (Hermes and OpenClaw) — no native adapter needed for v1 (this is a confirmed decision in `TASK_HERETIC_v0.1_BOOTSTRAP.md` §4).
- The `tool_choice: auto` pattern works correctly with OpenClaw's tool dispatch — agents running OpenClaw will call HERETIC's senses without special handling.
- OpenClaw's system prompt handling — informs how HERETIC's `inject_context_on_connect` feature should phrase the context message (compatible with OpenClaw's system prompt processing).

---

## What We DO NOT Plunder

- Any OpenClaw TypeScript/Node.js source code — not needed; language and architecture are incompatible for direct adaptation.
- OpenClaw's plugin or extension system — HERETIC's sense MCP architecture is independently designed; OpenClaw's extension model is architectural reference only.
- OpenClaw's session management or memory architecture — belongs to the spirit; not HERETIC's domain.
- OpenClaw's model routing or provider abstraction — HERETIC's Bifröst uses a single configured endpoint; LiteLLM-style routing is explicitly dropped for v1.
- Any branding, logo, or name — OpenClaw is identified only by name in documentation as a supported agent backend.

---

## Local Domain Ownership

| HERETIC layer | True Name | Relationship to OpenClaw |
|---|---|---|
| L1 Bifröst | Bifröst (bifrost) — the bridge | The sole point of contact with any agent, including OpenClaw. Same Bifröst client, same protocol, same tool schema injection. |

OpenClaw is **external to all HERETIC layers**, identical to Hermes from HERETIC's perspective. To L1 Bifröst, an OpenClaw endpoint at `http://localhost:8644/v1` looks the same as the Hermes endpoint — both speak the Bifröst contract.

---

## Public Interface (How HERETIC Speaks to OpenClaw)

Identical to Hermes: `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md` defines the full contract. OpenClaw users configure:

```yaml
bifrost:
  endpoint: "http://localhost:8644/v1"   # or wherever OpenClaw is running
  api_key: "${HERETIC_AGENT_KEY}"
  model: "<openclaw model name>"
  tailscale:
    prefer: false   # if OpenClaw is local, no Tailscale needed
```

No code changes in HERETIC are required to support OpenClaw vs Hermes — the agent-agnostic architecture means any spirit that speaks the protocol is already supported.

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Not applicable — no OpenClaw code is in HERETIC's repo |
| THIRD_PARTY_NOTICES.md entry | Yes — OpenClaw should be listed as a supported agent backend with its MIT license and GitHub URL, noted as an external runtime service, not distributed code |
| In-source headers | Not applicable |
| Trademark | Do not imply OpenClaw community endorsement of HERETIC. "OpenClaw is a supported agent backend for H.E.R.E.T.I.C." is appropriate attribution language. |

---

## Verification Status

- License re-verified: **2026-05-07** — MIT confirmed at https://github.com/openclaw/openclaw/blob/main/LICENSE
- OpenAI-compat API surface: **architectural reference confirmed** — OpenClaw speaks the required subset. Full verification against a live OpenClaw endpoint at time of v0.1 testing.
- Open question: OpenClaw's tool-call message format (confirm `tools` array and `role: tool` responses) — verify at v0.1 build phase with a test probe. Record result in this map's Verification Status section at that time.
- Open question: OpenClaw's handling of `max_tokens: 127000` (per RULES.AI.md mandate) — some agent runtimes cap lower. Test and document behavior at v0.1 verification.

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*OpenClaw is a second spirit the body may receive. Like Hermes, it enters through the Bifröst gate.*
*HERETIC does not know which spirit comes — only that any spirit who speaks the protocol is welcome.*
