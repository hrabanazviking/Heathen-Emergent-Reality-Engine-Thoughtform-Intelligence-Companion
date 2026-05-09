# TASK — HERETIC v0.6.x MCP SERVER HOSTING

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.6.2 More Senses shipped + audited + cleaned at `63fdf38`)

> **Mode: alternative-transport milestone.** Adds MCP (Model Context Protocol) server hosting alongside existing OpenAI tool_use path. v0.6 + v0.6.1 + v0.6.2 expose 16 tools to OpenAI-compat agents via the chat-completions tools array. v0.6.x adds a parallel path: HERETIC runs an MCP server, MCP-aware agents (Claude Desktop, Continue, OpenClaw with MCP client) connect directly. Both transports coexist.

---

## 1. Task scope

Until v0.6.x: agent → `/v1/chat/completions` with `tools` array → agent emits tool_call deltas → CLI dispatches via ToolDispatcher → tool_result → next chat iteration.

v0.6.x adds: MCP server (single, hosting all 4 senses' 16 tools) on configurable transport (stdio + HTTP/SSE). MCP-aware agent connects, calls `tools/list` → receives 16 tools, calls `tools/call` → ToolDispatcher routes → result. Same dispatcher; different transport.

The dispatch fabric (Skilningr.ToolDispatcher, the 4 sense subpackages, sandbox.py, the auth invariants) is **unchanged**. Only the transport layer is added. This is the architecture's biggest payoff: one tool-execution backend, multiple agent-connection paths.

What v0.6.x does NOT add:
- New senses (4 senses already shipped; v0.6.2 backlog for more)
- New tools (16 tools already locked)
- MCP client (HERETIC remains a server; we're not consuming someone else's MCP server)
- Native MCP transport for v0.6's existing OpenAI tool_use path (kept side-by-side)
- Auth via OAuth/JWT (bearer-token-via-env-var carries forward; localhost-only by default)

---

## 2. Current status — 2026-05-08

**Phase:** v0.6.2 SHIPPED + AUDITED + CLEANED at `63fdf38`. Test baseline: 943 Python + 7 skipped + 91 frontend = 1041.

### v0.6.x deliverables
- ⏳ `src/heretic/skilningr/mcp_server.py` — MCP server adapter using official `mcp` Python SDK
- ⏳ `src/heretic/cli.py` — new `mcp` subcommand: `heretic mcp [--transport stdio|http]` launches the MCP server
- ⏳ `SkilningrConfig` extension — `mcp_server: McpServerConfig` (enabled, transport, host, port, allow_remote_bind)
- ⏳ MCP transport backends: stdio (Claude Desktop convention) AND HTTP/SSE (parallel to vebond WS pattern)
- ⏳ `tools/list` — returns the 16 tool definitions from registered senses
- ⏳ `tools/call` — routes through existing ToolDispatcher (one execution backend; two transport paths)
- ⏳ `pyproject.toml` — add `mcp>=0.1` to a new `[mcp]` extra
- ⏳ `heretic.example.yaml` — new `skilningr.mcp_server:` block
- ⏳ `docs/cartography/DATA_FLOW.md §4.13` — MCP transport flow
- ⏳ `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md` — note MCP as alternative agent-connection path
- ⏳ Tests — 30+ new Python tests (transport, tools/list, tools/call, error mapping); total target 973+

### What v0.6.x carries forward
- Same 4 senses (Smiðja, Minni, Skepja, Leið)
- Same ToolDispatcher
- Same 16 tools
- Same sandbox primitives
- Same auth invariants (token from env, never logged)
- Same fault tolerance (tool dispatch failure → error tool_result, never crash)

The transport seam is the ONLY thing new.

---

## 3. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| MCP library | `mcp` (official Anthropic Python SDK, MIT) | Canonical implementation; in plunder maps already; minimal license risk |
| Server topology | **Single MCP server hosting all senses** | Cleaner connection model; one URI; simpler operator config |
| Transports | **stdio + HTTP/SSE** (both supported; operator chooses) | stdio = Claude Desktop convention; HTTP/SSE = browser-friendly + remote-via-Tailscale |
| Coexistence with OpenAI tool_use | **Both paths supported in parallel** | Operators with OpenAI-compat agents (Hermes, OpenClaw via OpenAI shim) keep working; MCP-aware agents get native protocol |
| Dispatch reuse | **ToolDispatcher unchanged; only transport adapter is new** | Single execution backend invariant |
| Auth model | Bearer-token-via-env-var carries forward; localhost default | Mirror Brúarhönd / Forge auth pattern from v0.6 + v0.6.1 |
| `allow_remote_bind` | False default; explicit opt-in for non-localhost | Privacy + Tailscale-routability without exposing publicly |
| CLI subcommand | New `heretic mcp` alongside `heretic light` and `heretic serve` | Three modes; operator launches what they need |
| Concurrent MCP + serve | Yes — both can run in same Python process if operator wants | mcp_server is async; serve uses FastAPI/uvicorn; both run on asyncio loop together |
| New Skald essay | NO — alternative transport; not a new faculty | Vision cycle remains 7 panels; v1.x polish may add a "MCP door" essay |

---

## 4. MCP protocol surface

Per the official MCP spec (modelcontextprotocol.io):

**Server-side methods HERETIC implements:**
- `initialize` — handshake; return server capabilities (tools, resources optional, prompts optional — v0.6.x ships tools only)
- `tools/list` — returns 16 tool definitions converted from `SMIDJA_TOOL_DEFINITIONS` + `MINNI_TOOL_DEFINITIONS` + `SKEPJA_TOOL_DEFINITIONS` + `LEID_TOOL_DEFINITIONS` to MCP tool schema (similar but not identical format)
- `tools/call` — receive `name` + `arguments`; route through ToolDispatcher; return `content` array per MCP spec

**Server-side methods HERETIC does NOT implement (v0.6.x scope):**
- `resources/*` — file-resource hosting (deferred)
- `prompts/*` — prompt template hosting (deferred)
- `sampling/*` — letting the agent run inference inside the server (out of scope)
- `logging/*` — server logs streamed to client (deferred)

### Tool schema conversion

OpenAI tool_use format:
```json
{
  "type": "function",
  "function": {
    "name": "smidja.screenshot",
    "description": "...",
    "parameters": {"type": "object", "properties": {...}, "required": [...]}
  }
}
```

MCP tool format:
```json
{
  "name": "smidja.screenshot",
  "description": "...",
  "inputSchema": {"type": "object", "properties": {...}, "required": [...]}
}
```

Architect's job: write a `convert_to_mcp_tool(openai_tool: dict) -> dict` helper.

---

## 5. Mythic Engineering wave plan (slim — alternative transport, no new senses)

### Wave 1 — parallel
- **Cartographer**: `docs/cartography/DATA_FLOW.md §4.13 "MCP transport flow (v0.6.x)"`: agent → MCP transport (stdio or HTTP/SSE) → server initialize → tools/list → server returns 16 tool defs → tools/call → ToolDispatcher → ToolResult mapped to MCP content array → return. Diagram showing both transports (stdio + HTTP/SSE) alongside the existing OpenAI tool_use path; emphasize ToolDispatcher as single shared backend.
- **Architect**: scaffold `src/heretic/skilningr/mcp_server.py` (skeleton with NotImplementedError stubs for transport startup, tools/list, tools/call); McpServerConfig dataclass; tool-schema converter helper signature; `[mcp]` pyproject extra; new CLI subcommand stub; INTERFACE.md; placeholder tests; verify mcp Python SDK API surface (read official docs to lock the import path + handler signatures)

### Wave 2
- **Forge**: implement MCP server (initialize handshake, tools/list returning converted tools, tools/call routing through ToolDispatcher); both transports (stdio + HTTP/SSE); CLI `heretic mcp` subcommand fully wired; tests with mocked MCP client; total 30+ new tests
- **Auditor**: AUDIT_v0.6.x_MCP_SERVER.md; verify dispatch reuse (ToolDispatcher unchanged; same execution path); transport correctness (stdio + HTTP/SSE both work; no shared-state bugs); tool schema conversion (round-trip OpenAI ↔ MCP); auth invariant (token from env carries forward); concurrent operation (mcp + serve in same process possible); failure modes (transport disconnect, malformed tools/call, unknown tool name)

### Wave 3 — cleanup if needed

### Close-out
- **Scribe**: DEVLOG entry 13 + TASK update + memory refresh

---

## 6. Files to be created/extended

```
src/heretic/skilningr/
  mcp_server.py         NEW — MCP server adapter; initialize/tools_list/tools_call
  config_model.py       extend — McpServerConfig + SkilningrConfig.mcp_server field
  errors.py             extend — McpServerError + child types (TransportError, ProtocolError)
src/heretic/cli.py      extend — `mcp` subcommand
tests/
  test_mcp_server.py    NEW — handler tests + mocked-client tests
  test_mcp_transport.py NEW — stdio + http transport tests
heretic.example.yaml    extend — skilningr.mcp_server: block
pyproject.toml          extend — [mcp] extra: mcp>=0.1
docs/cartography/DATA_FLOW.md §4.13 NEW
docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md MCP alternative-path note
```

---

## 7. v0.6.x exit criteria
- `heretic mcp --transport stdio` launches MCP server reading stdin/writing stdout
- `heretic mcp --transport http` launches MCP server on configured host:port
- MCP client (mocked in tests) successfully calls initialize + tools/list + tools/call
- Tools/list returns 16 tools (matching the count exposed via OpenAI tool_use path)
- Tools/call routes through ToolDispatcher (single execution backend)
- Both transports tested
- Test count ≥973 Python; total ≥1064
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 8. Operational rules (carried)

- Privacy: localhost default; allow_remote_bind explicit opt-in
- Auth: bearer token from env if configured (mirror Brúarhönd / Forge); never logged
- Cross-platform: stdio works on all OS; HTTP/SSE via uvicorn (already a dep from v0.4)
- Type hints, no emoji, no absolute paths
- After EVERY completed phase: update TASK file + memory immediately

---

## 9. Backlog forward
- v0.5.3 frontend Sjón webcam sub-badge (carry from v0.5.2)
- v0.5.x periodic webcam, multi-camera, privacy masks
- v0.6.2.1 Leið streaming via aiter_bytes (carry from v0.6.2)
- v0.6.2.2 Leið headless browser (playwright; carry from v0.6.2)
- v0.6.x.1 MCP resources/* hosting (carry from v0.6.x — deferred to scope tightness)
- v0.6.x.2 MCP prompts/* hosting (carry from v0.6.x)
- v0.7 Mímisbrunnr starter pack — NEXT after v0.6.x
- v0.4.1 first compile (awaits operator linker install)

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.6.x — when the workshop opens a second door.*
