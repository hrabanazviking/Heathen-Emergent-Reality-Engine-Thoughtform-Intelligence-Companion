# Skepja Sense — Interface Contract

**Last updated:** 2026-05-08 (v0.6.2 scaffold — Rúnhild Svartdóttir)
**Scope:** L5.2 Skepja — sandboxed terminal sense
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. Identity

| Field       | Value                                          |
|-------------|------------------------------------------------|
| True Name   | Skepja ("shaping")                             |
| sense_id    | `skepja`                                       |
| Layer       | L5.2 Skilningr sense hub                       |
| Prefix      | `skepja.*`                                     |
| Config key  | `skilningr.skepja.*` in `heretic.yaml`         |
| Module      | `heretic.skilningr.senses.skepja`              |
| Client      | `SkepjaClient` (subprocess.run, shell=False)   |

---

## 2. Purpose

Skepja gives the agent the ability to run shell commands — build tools, test
runners, scripts — in a sandboxed environment. The gate is a strict allowlist:
if the executable is not listed, the command does not run. Period.

Skepja does NOT maintain a persistent shell session. Each `run_command` call is
a fresh subprocess. Shell metacharacters (pipes, redirects, `&&`) are NOT
interpreted — they become literal arguments.

---

## 3. Sandbox Invariants (NON-NEGOTIABLE)

| # | Invariant |
|---|-----------|
| S-1 | `sandbox.command_in_allowlist()` is called BEFORE `subprocess.run()`. No subprocess is ever spawned for a command not on the allowlist. |
| S-2 | `subprocess.run(shell=False)` is INVARIANT. Shell injection is structurally impossible because no shell is invoked. |
| S-3 | `command_allowlist` defaults `[]` (empty). With an empty list, no command can run regardless of `enabled=True`. |
| S-4 | `enabled: false` by default. No terminal capability until explicitly enabled. |
| S-5 | The subprocess does NOT inherit HERETIC's environment unless `inherit_env: true` (default false). Credentials in HERETIC's environment are not exposed to subprocesses. |
| S-6 | Subprocess output is truncated at `max_output_bytes` to prevent token-blowup. |
| S-7 | Subprocesses are killed after `timeout_seconds` (default 60). No runaway processes. |
| S-8 | The `working_directory` is fixed for all commands — the agent cannot change it. |

---

## 4. Tools (LOCKED at v0.6.2)

| Tool name                     | Action              | Required params    | Optional params |
|-------------------------------|---------------------|--------------------|-----------------|
| `skepja.run_command`          | Execute command     | `command` (string) | —               |
| `skepja.get_working_directory`| Report working dir  | (none)             | —               |

---

## 5. Success Response Shapes

### skepja.run_command
```json
{
  "command": "git status",
  "exit_code": 0,
  "stdout": "On branch main...",
  "stderr": "",
  "timed_out": false,
  "working_directory": "/home/user/heretic_workspace"
}
```

### skepja.get_working_directory
```json
{
  "working_directory": "/home/user/heretic_workspace"
}
```

---

## 6. Failure Modes

| Condition                             | Error class             | SENSE_CONTRACTS code  |
|---------------------------------------|-------------------------|-----------------------|
| Executable not in allowlist           | `CommandNotAllowedError`| `PERMISSION_DENIED`   |
| Command string malformed (shlex)      | `CommandParseError`     | `INVALID_ARGUMENTS`   |
| Subprocess timed out                  | `CommandTimeoutError`   | `SENSE_TIMEOUT`       |
| Non-zero exit code                    | `CommandExecutionError` | `SENSE_INTERNAL_ERROR`|
| Unknown tool name in `skepja.*`       | `ToolDispatchError`     | `SENSE_INTERNAL_ERROR`|
| Sense disabled or not open            | `SenseUnavailableError` | `SENSE_UNAVAILABLE`   |

---

## 7. Configuration Reference

```yaml
skilningr:
  skepja:
    enabled: false                   # opt-in
    command_allowlist: []            # empty = nothing runs; add executables to permit
    working_directory: ~/heretic_workspace
    timeout_seconds: 60
    inherit_env: false               # do not expose HERETIC's env to subprocesses
    max_output_bytes: 65536          # 64 KB stdout+stderr cap
```

---

## 8. Cross-Platform Notes

Windows cmd.exe uses different conventions from POSIX sh. `shlex.split()` runs
in POSIX mode by default. Forge Wave 2 must handle platform-specific command
parsing. Allowlist entries are case-sensitive — on Windows, use the exact
executable name (e.g. `python` or `python.exe` as appropriate for the install).

---

## 9. Forge Wave 2 — Implementation Contract

- `run_command`: call `_validate_command()` first; resolve `working_directory`
  with `Path.expanduser().resolve()`; call `subprocess.run(tokens, shell=False,
  capture_output=True, timeout=timeout_seconds, cwd=cwd, env=env_or_none)`;
  handle `subprocess.TimeoutExpired` → `CommandTimeoutError`; truncate output
  to `max_output_bytes`; if `exit_code != 0` and caller wants a rich error,
  raise `CommandExecutionError` with exit_code + output in detail.
- `get_working_directory`: return `{"working_directory": str(Path(working_directory).expanduser().resolve())}`.
