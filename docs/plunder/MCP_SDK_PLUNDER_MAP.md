# MCP SDK (Anthropic Python) — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** studying — no code adapted yet; foundational for v0.1 Skilningr build

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | MCP Python SDK (Model Context Protocol) |
| Repository | https://github.com/modelcontextprotocol/python-sdk |
| PyPI package | `mcp` |
| Version as of write | 1.x (verify current at time of implementation — `pip index versions mcp`) |
| Primary maintainer | Anthropic, Inc. |
| License | MIT |
| License URL | https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE |
| License verification status | **Verified MIT 2026-05-07** (GitHub LICENSE file confirms MIT, copyright Anthropic, Inc.) |

---

## Upstream License

**MIT License** — permissive, allows vendoring and sublicensing. Compatible with HERETIC's MIT license with no restrictions beyond preserving the copyright notice.

Exact license type: MIT
License link: https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE

---

## Compatibility Verdict

**CLEAN — no caveats.** MIT upstream into MIT receiving project. No copyleft. No patent grants to navigate. No NOTICE file obligations beyond the copyright line. Code may be vendored into `vendor/mcp_sdk/` or installed as a runtime dependency via pip. Either path is legally sound.

**Recommended approach:** runtime dependency via pip (`pip install mcp`), not vendored source. The SDK is actively maintained by Anthropic and will receive protocol updates; staying on pip ensures HERETIC inherits upstream protocol improvements without manual backporting. If vendored, a one-time copy with upstream headers preserved is legally sufficient but imposes maintenance burden.

---

## What We Plunder

This is primarily an **architectural reference and runtime dependency** — not a source-level plunder. Specifically:

### Runtime dependency (pip install)
- The `mcp` Python package itself — used by every L5.x sense subprocess to implement the MCP server lifecycle (`initialize`, `tools/list`, `tools/call`, `shutdown` over stdio transport).
- The `mcp.server.fastmcp` or `mcp.server.Server` class (verify current API at implementation time) — each sense subprocess (`heretic-sense-minni`, `heretic-sense-skepja`, etc.) inherits from or wraps this.
- The stdio transport layer — how each sense subprocess communicates with L5 Skilningr hub over `stdin`/`stdout`.

### Architectural patterns (study and reimplement locally)
- The `initialize` / `serverInfo` / `senseVersion` handshake pattern — adapted into HERETIC's sense version negotiation schema (see `SENSE_CONTRACTS.md` §4).
- The `tools/list` → `tools/call` → structured result pattern — the two-call interface HERETIC's Skilningr hub exposes to L1 Bifröst.
- The health-check-via-tools-list pattern — Skilningr sends `tools/list` as a keepalive probe every `health_interval_seconds` (see `LAYER_INTERFACES.md` §L5.1).
- Error response structure — HERETIC's error taxonomy (`SENSE_CONTRACTS.md` §3) was designed to be compatible with MCP error semantics.

### What we study but do not copy
- The full MCP protocol specification — we implement against it, not by copying its reference implementation.
- The MCP client half — HERETIC uses L1 Bifröst's own HTTP client for agent calls; the MCP SDK's client is not used.
- The MCP documentation patterns — architectural reference only.

---

## What We DO NOT Plunder

- The MCP client implementation — HERETIC's Bifröst (L1) is an OpenAI-compat HTTP client, not an MCP client. These are different protocols.
- Any Anthropic-branded UI or tooling patterns.
- The MCP inspector or development tools — these are developer utilities, not runtime components.
- The TypeScript / other-language SDK variants — HERETIC's senses are Python; only the Python SDK is relevant.

---

## Local Domain Ownership

| HERETIC layer | True Name | Owns this integration |
|---|---|---|
| L5 Skilningr | Skilningr (skilningr) | MCP Sense Hub — spawns sense subprocesses via stdio MCP transport; aggregates tool schemas; routes calls |
| L5.1–L5.9 (all senses) | Minni, Skepja, Leið, Hönd, Smiðja, Líkami, Boð, Nýr Limr, Mímisbrunnr | Each sense subprocess uses `mcp` as its server implementation library |

The `mcp` package is a **shared runtime dependency** of all sense subprocesses. It is not owned by any single sense — it is the substrate all senses are built on.

---

## Public Interface

Inside HERETIC, the MCP SDK is surfaced as follows:

- Each sense subprocess imports `mcp` at startup and registers its tools via the SDK's `@server.call_tool` / `@server.list_tools` decorators (or equivalent API).
- The Skilningr hub communicates with sense subprocesses exclusively via **stdio MCP protocol** — the SDK handles serialization/deserialization.
- No HERETIC module outside `heretic/sense_hub/` ever imports `mcp` directly.
- The public interface HERETIC code calls: `sense_hub::get_tools() -> Vec<ToolSchema>` and `sense_hub::call_tool(name, args) -> ToolResult` — these are HERETIC-internal Rust types; the MCP SDK is hidden behind the subprocess boundary.

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Yes — if vendored: copy `LICENSE` into `vendor/mcp_sdk/`; if pip dep: note in `THIRD_PARTY_NOTICES.md` |
| NOTICE file required | No — MIT does not require a NOTICE file |
| In-source headers required | Only if code is directly copied/adapted (Strategy C); if pattern-only or runtime dep, no header needed |
| THIRD_PARTY_NOTICES.md entry | Yes — required regardless of vendored vs runtime dep |
| Trademark / branding | Do not imply Anthropic endorsement; do not use Anthropic or MCP logos |

---

## Verification Status

- License re-verified: **2026-05-07** — MIT confirmed at https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE
- PyPI package name confirmed: `mcp`
- Current version: **verify at implementation time** (`pip index versions mcp` or check PyPI)
- Open question: confirm whether `mcp.server.fastmcp` or `mcp.server.Server` is the stable API surface at time of L5 build — the SDK was in rapid development in 2024-2025. Pin to a specific version in `requirements.txt` at build time.

---

## Vendor Path

**External runtime dependency — user installs via pip.**

Not vendored. Declared in `requirements.txt` as `mcp>=1.0.0` (pin major version; exact version TBD at build time).

If the decision to vendor is ever made (e.g., for offline distribution): `vendor/mcp_sdk/` — with `LICENSE` file preserved and a `VENDOR_NOTES.md` recording the version pinned and the reason for vendoring.

---

## Plunder Intent (§6 Phase 0)

**Why this upstream matters:** The MCP Python SDK is the reference implementation of the Model Context Protocol — the standard tool-call protocol HERETIC uses to give the inhabiting spirit access to all its senses. Without this SDK (or an equivalent), building the L5 Skilningr sense hub from scratch would require implementing the stdio MCP transport protocol manually. Using the reference SDK ensures protocol compliance, future-proofs against spec evolution, and reduces implementation risk for v0.1 scope.

**What is not blindly copied:** The full SDK is not vendored — only the runtime package is consumed. HERETIC's tool schema format, error taxonomy, and version negotiation are HERETIC-native designs inspired by MCP semantics but not copied from the SDK source.

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*The MCP SDK is the tongue that lets the senses speak. We drink from it without copying the cup.*
