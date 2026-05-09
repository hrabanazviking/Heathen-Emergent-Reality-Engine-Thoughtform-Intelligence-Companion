# Minni Sense — Interface Contract

**Last updated:** 2026-05-08 (v0.6.2 scaffold — Rúnhild Svartdóttir)
**Scope:** L5.1 Minni — sandboxed local filesystem sense
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. Identity

| Field       | Value                                          |
|-------------|------------------------------------------------|
| True Name   | Minni ("memory")                               |
| sense_id    | `minni`                                        |
| Layer       | L5.1 Skilningr sense hub                       |
| Prefix      | `minni.*`                                      |
| Config key  | `skilningr.minni.*` in `heretic.yaml`          |
| Module      | `heretic.skilningr.senses.minni`               |
| Client      | `MinniClient` (sandboxed pathlib/io)           |

---

## 2. Purpose

Minni gives the agent controlled access to the local filesystem — reading files,
writing output, and listing directory contents — within a strict sandbox defined
by the operator. Outside the sandbox, the agent is blind to the filesystem.

Minni does NOT touch execute permissions. It does NOT follow symlinks by default.
It does NOT perform streaming reads. File content is loaded fully into memory
up to the configured size cap.

---

## 3. Sandbox Invariants (NON-NEGOTIABLE)

These invariants must hold for every tool invocation, under every input.
Any implementation that weakens them introduces a security regression.

| # | Invariant |
|---|-----------|
| M-1 | Every path is validated against `MinniConfig.allowed_roots` via `sandbox.path_within_allowed_roots()` BEFORE any I/O occurs. No I/O precedes this check. |
| M-2 | Path traversal (`../`) is neutralised by `Path.resolve()` before comparison. The raw string is never used for access control. |
| M-3 | Absolute paths to system locations (e.g. `/etc/passwd`, `C:\Windows\System32`) outside `allowed_roots` are rejected as sandbox violations regardless of how they are expressed. |
| M-4 | Symlinks are NOT followed during sandbox validation (`follow_symlinks: false` default). A symlink inside `allowed_roots` that points outside is a violation. |
| M-5 | Files exceeding `max_read_bytes` are rejected BEFORE any bytes are read. No partial read. |
| M-6 | Content exceeding `max_write_bytes` is rejected BEFORE any bytes are written. No partial write. |
| M-7 | No execute permission is ever set on written files. |
| M-8 | `enabled: false` by default. The sense does not register tools until explicitly enabled. |
| M-9 | An empty `allowed_roots` list grants no access even when `enabled: true`. |

---

## 4. Tools (LOCKED at v0.6.2)

| Tool name             | Action         | Required params      | Optional params             |
|-----------------------|----------------|----------------------|-----------------------------|
| `minni.read_file`     | Read file      | `path` (string)      | —                           |
| `minni.write_file`    | Write file     | `path`, `content`    | —                           |
| `minni.list_directory`| List directory | `path` (string)      | `recurse` (boolean, default false) |

Tool names are stable identifiers. Renaming is a breaking change per
SENSE_CONTRACTS.md §2 rule 4.

---

## 5. Success Response Shapes

### minni.read_file
```json
{
  "path": "/home/user/heretic_workspace/notes.md",
  "content": "<file content as UTF-8 string>",
  "size_bytes": 1234,
  "encoding": "utf-8"
}
```

### minni.write_file
```json
{
  "path": "/home/user/heretic_workspace/output.txt",
  "bytes_written": 512,
  "created": true
}
```

### minni.list_directory
```json
{
  "path": "/home/user/heretic_workspace",
  "entries": [
    {"name": "notes.md", "type": "file", "size_bytes": 1234, "path": "..."},
    {"name": "subdir",   "type": "directory", "size_bytes": null, "path": "..."}
  ],
  "recurse": false,
  "total_entries": 2
}
```

---

## 6. Failure Modes

| Condition                              | Error class              | SENSE_CONTRACTS code  |
|----------------------------------------|--------------------------|-----------------------|
| Path outside `allowed_roots`           | `MinniSandboxViolation`  | `PERMISSION_DENIED`   |
| Symlink escaping sandbox               | `MinniSandboxViolation`  | `PERMISSION_DENIED`   |
| File or directory does not exist       | `MinniFileNotFoundError` | `INVALID_ARGUMENTS`   |
| File exceeds `max_read_bytes`          | `MinniFileTooLargeError` | `INVALID_ARGUMENTS`   |
| Content exceeds `max_write_bytes`      | `MinniFileTooLargeError` | `INVALID_ARGUMENTS`   |
| OS permission denied                   | `MinniPermissionError`   | `PERMISSION_DENIED`   |
| Unknown tool name in `minni.*`         | `ToolDispatchError`      | `SENSE_INTERNAL_ERROR`|
| Sense disabled or not open             | `SenseUnavailableError`  | `SENSE_UNAVAILABLE`   |

All failures are translated into structured tool_result error JSON at the
MinniSense dispatch boundary. None propagate to L1 Bifröst.

---

## 7. Lifecycle

1. **Kynding (open):** `MinniSense.open()` verifies `enabled=True` and logs
   the number of configured roots. Forge Wave 2 adds root-existence verification.
2. **Tengsl (tool calls):** `dispatch_tool_call()` routes to `MinniClient`.
   Sandbox validation precedes every I/O call.
3. **Slokna (close):** `MinniSense.close()` marks `_is_open=False`.
   No persistent connection exists in v0.6.2.

---

## 8. Configuration Reference

```yaml
skilningr:
  minni:
    enabled: false                   # opt-in; must be true to expose tools
    allowed_roots:
      - ~/heretic_workspace          # default; add paths as needed
    max_read_bytes: 1048576          # 1 MB default
    max_write_bytes: 1048576         # 1 MB default
    follow_symlinks: false           # privacy-first default
```

---

## 9. What Callers Must Not Assume

- Callers must NOT assume the agent can access arbitrary filesystem paths.
  Every path is subject to the sandbox gate.
- Callers must NOT rely on partial reads or writes — the size cap is enforced
  before I/O begins; nothing partial is returned.
- Callers must NOT use Minni as a code execution vector — write_file sets no
  execute permission; Skepja is the execution sense.

---

## 10. Forge Wave 2 — Implementation Contract

Forge implements `MinniClient` bodies in Wave 2 of v0.6.2. The following
invariants must be honoured in the implementation:

- `read_file`: call `_validate_path()` first; check size; open with `Path.read_text(encoding="utf-8")`; catch `FileNotFoundError` → `MinniFileNotFoundError`; catch `PermissionError` → `MinniPermissionError`.
- `write_file`: call `_validate_path()` first; check content length in bytes; create parent dirs with `mkdir(parents=True, exist_ok=True)` (only within sandbox); write atomically via temp file + rename where possible; catch `PermissionError` → `MinniPermissionError`.
- `list_directory`: call `_validate_path()` first; use `Path.iterdir()` or `Path.rglob()` for recurse; each entry validated to still be within allowed_roots; catch `PermissionError` → `MinniPermissionError`.
