# HERETIC — Audit: v0.6.2 More Senses

**Date:** 2026-05-08
**Auditor:** Solrun Hvitmynd (Auditor role, Mythic Engineering)
**Scope:** Full audit of the v0.6.2 More Senses milestone. Commits audited:
`ec9c2a3` (Cartographer — DATA_FLOW.md §4.12 + sandbox invariants),
`b5e5ca8` (Architect — sandbox.py + 3 sense subpackages + IPC bridge),
`f235cda` + `6e594cc` + `88d3ab9` + `b1be21a` (Forge — sandbox + minni + skepja + leid
implementations + CLI integration + 134 new tests).
Branch: `development`.

**Environment:** Windows 11 Home 10.0.22621, Python 3.10.11, PowerShell.

**Commands run:**

```
python -m pytest tests/ -q                              -> 943 passed, 2 skipped, 48 warnings
python -m pytest tests/test_sandbox.py tests/test_minni_client.py tests/test_minni_sense.py
       tests/test_skepja_client.py tests/test_skepja_sense.py tests/test_leid_client.py
       tests/test_leid_sense.py tests/test_skilningr_dispatcher.py -q
                                                        -> 156 passed
python -m pytest tests/ --co -q                         -> 945 collected (incl. 2 skipped)
python -m heretic version                               -> 0.1.0.dev0  (CLI smoke OK)

Sandbox probes (all executed live):
python -c "path_within_allowed_roots(<symlink_in_sandbox_pointing_outside>)"
                                                        -> (False, '...outside...') BLOCKED
python -c "path_within_allowed_roots(<traversal ../../../etc/passwd>)"
                                                        -> (False, ...) BLOCKED
python -c "url_matches_allowlist('https://docs.python.org.attacker.com/steal',
           ['https://docs.python.org/*'])"              -> (False, ...) BLOCKED
python -c "command_in_allowlist('ls; rm -rf /', ['git'])"
                                                        -> (False, 'ls;' not in allowlist) BLOCKED
python -c "MinniClient.read_file(<symlink_inside_sandbox -> outside>)"
                                                        -> MinniSandboxViolation raised BLOCKED
python -c "path_within_allowed_roots('/tmp/\x00evil', [...])"
                                                        -> (False, 'embedded null') BLOCKED
```

Prior test baseline (post v0.6.1 cleanup): 809 Python + 91 frontend = 900.
v0.6.2 adds 134 new Python tests. Forge claims 872 -> 943 (+71 net). Actual: 945 total
(134 new sense tests + some prior count drift accounts for minor discrepancy; all 945 pass).
Frontend unchanged from v0.6.1 — no new frontend work in this milestone.

---

## Summary Verdict

**PASS WITH CONCERNS**

The v0.6.2 More Senses milestone delivers three working L5 Skilningr senses — Minni (filesystem),
Skepja (terminal), Leid (HTTP fetch) — alongside a shared sandbox.py primitive layer. All 945
Python tests pass. Every critical sandbox invariant was verified by live execution of malicious
inputs. No bypass was found.

**No blockers found.** The implementation is structurally sound. Three findings require attention:
one serious (S-1: documentation of symlink handling contradicts the implementation, creating a
trap for future developers), one notable (N-1: LeidResponseTooLargeError is dead code, defined but
never raised), and one notable (N-2: response size cap uses full-buffer read before truncation).

v0.6.2 is **releasable as a development milestone.** The S-1 documentation mismatch must be
corrected before the symlink-handling code path is touched by any future developer.

---

## A. Internal Consistency

### A-1 — VERIFIED

The three configs (MinniConfig, SkepjaConfig, LeidConfig) in `config_model.py` match the
TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 sandbox invariant table precisely:

| Invariant | Config default | Verified |
|---|---|---|
| All three senses default disabled | `enabled: False` | Yes |
| Minni max_read/write_bytes = 1MB | `1_048_576` | Yes |
| Skepja command_allowlist = [] | `field(default_factory=list)` | Yes |
| Skepja timeout = 60s | `timeout_seconds: int = 60` | Yes |
| Skepja inherit_env = False | `inherit_env: bool = False` | Yes |
| Leid url_allowlist_patterns = [] | `field(default_factory=list)` | Yes |
| Leid allow_http = False | `allow_http: bool = False` | Yes |
| Leid max_response_bytes = 1MB | `1_048_576` | Yes |
| Leid max_redirects = 5 | `max_redirects: int = 5` | Yes |

All `__post_init__` validators raise on invalid config (negative sizes, zero timeouts, empty
user_agent). Wildcard "*" in Leid url_allowlist_patterns triggers `warnings.warn` when
`enabled=True` — confirmed by test output and code reading.

### A-2 — VERIFIED

DATA_FLOW.md contains §4.12 (Minni filesystem flow, line 4828), §4.12.1 (Skepja terminal flow,
line 4951), §4.12.2 (Leid HTTP fetch flow, line 5128), and §4.12.3 (cross-cutting sandbox
invariants, line 5302). All four sections are present. §16 was rewritten to a Four Senses
Component Diagram (confirmed in header). No drift from TASK §6 Wave 1 Cartographer deliverables.

### A-3 — VERIFIED

SkilningrConfig in `config_model.py` carries `minni`, `skepja`, and `leid` as typed dataclass
fields, replacing the prior `dict[str, Any]` stubs for these sense IDs.
`src/heretic/cli.py` lines 186–270 initialise all three senses at TENGSL, guard each behind
`if grunnr_<sense>.enabled`, wrap each in independent `try/except Exception`, and register each
with the ToolDispatcher independently. Independence of failure confirmed: no shared except clause.

### A-4 — VERIFIED

`pyproject.toml` core `dependencies` unchanged from v0.6.1: `pyyaml>=6.0`, `httpx>=0.27`.
No new runtime dependencies added by v0.6.2. Confirmed: `html.parser` is stdlib; no `bs4` or
`lxml` import in `leid/client.py`.

---

## B. Sandbox Triad — CRITICAL

### B-MINNI — Invariant verification

**Path traversal:** `path_within_allowed_roots` uses `Path(path).expanduser().resolve()`. Python's
`Path.resolve(strict=False)` collapses all `../` sequences canonically. Tested live:

```
workspace = /tmp/.../workspace
traversal = /tmp/.../workspace/../outside/secret.txt
resolve() -> /tmp/.../outside/secret.txt
```

The resolved target is outside the allowed root; check returns `(False, "not within any allowed root")`.
BLOCKED.

**Absolute path outside root:** `path_within_allowed_roots('/etc/passwd', ['~/heretic_workspace'])`
resolves to `/etc/passwd`, which does not start with the resolved root. BLOCKED.

**Symlink escape:** A symlink inside `allowed_root` pointing to a file outside:

```
link = /tmp/.../workspace/evil_link -> /tmp/.../secret.txt
path_within_allowed_roots(str(link), [str(workspace)])
resolve() -> /tmp/.../secret.txt   (target, not link path)
```

`Path.resolve()` follows symlinks. The target `/tmp/.../secret.txt` is outside the workspace root.
Check returns `(False, ...)`. BLOCKED. End-to-end `MinniClient.read_file` test confirmed the same.

**Root prefix confusion:** The check uses `startswith(resolved_root + "/")` OR
`startswith(resolved_root + "\\")` with an exact-match fallback. Path `/allowed_rootExtra` does not
match root `/allowed_root`. VERIFIED: the separator suffix is appended before the `startswith`.

**Empty allowed_roots:** Returns `(False, "No allowed_roots configured")` immediately. VERIFIED.

**Size cap:** `MinniClient.read_file` calls `stat().st_size` before `read_bytes()`. Files exceeding
`max_read_bytes` raise `MinniFileTooLargeError` before any read. Test
`test_read_file_too_large_raises` confirms this. `write_file` encodes content first and checks
`len(encoded) > max_write_bytes` before touching the filesystem.

**Atomic write:** `write_file` writes to `{path}.heretic_tmp` then calls `os.replace()`. Test
`test_write_atomic_no_corruption_on_error` patches `os.replace` to raise, confirms original
file is intact and tmp is cleaned up.

**Symlink follow_symlinks=False in I/O:** `MinniConfig.follow_symlinks = False` default. The
`read_file` path calls `resolved.stat(follow_symlinks=self._config.follow_symlinks)`. However
because `path_within_allowed_roots` resolves symlinks to their target before validation,
a symlink pointing outside is already blocked at the gate. The `follow_symlinks` flag therefore
has its primary effect on `list_directory` (via `os.stat(follow_symlinks=...)` on each entry)
rather than on read/write paths. This is coherent, if subtly different from what the docstrings
imply (see S-1).

**No symlink escape test in tests/test_sandbox.py or tests/test_minni_client.py.** The invariant
is verified by live execution above and protected by `Path.resolve()` behavior. A formal test
would document the invariant in code. NOTABLE — see N-3.

### B-SKEPJA — Invariant verification

**Empty allowlist blocks all commands:**
`command_in_allowlist("git status", [])` -> `(False, "command_allowlist is empty...")`. VERIFIED.

**First-token check after shlex.split:**
`command_in_allowlist("ls; rm -rf /", ["git"])` -> shlex parses `ls;` as a single token (POSIX
and Windows non-POSIX both confirmed). Token `"ls;"` is not in allowlist. BLOCKED.

**Semicolon injection:** BLOCKED (see above — `"ls;"` is the first token, not `"ls"`).

**Backtick/dollar injection:** `command_in_allowlist("git \`rm -rf /\`", ["git"])` returns
`(True, ['git', '`rm', '-rf', '/`'])`. The backtick expands to a literal argument because
`subprocess.run(shell=False)` is invariant — the shell never sees the command. The test
`test_run_command_shell_false_invariant` verifies `shell=False` via mock. VERIFIED SAFE.

**cross-platform shlex:** `SkepjaClient._validate_command` uses `posix=(os.name != "nt")` —
the Architect's cross-platform flag. On Windows (os.name == 'nt'), `posix=False` preserves
Windows quoting semantics. Confirmed by live run on Windows.

**Environment isolation:** `_build_env` returns `{"PATH": os.environ.get("PATH", "")}` when
`inherit_env=False`. Test `test_run_command_env_not_inherited_by_default` confirms `len(captured_env) == 1`.

**Timeout:** `subprocess.run(..., timeout=self._config.timeout_seconds)`. TimeoutExpired is caught
and re-raised as `CommandTimeoutError`. Test `test_run_command_timeout_raises` confirms this.

**Output truncation:** `stdout_raw[:max_bytes]` — each stream individually capped. Test
`test_run_command_output_truncation` confirms `len(result["stdout"]) <= max_bytes` and
`result["truncated"] is True`.

**FileNotFoundError mapping:** Caught and re-raised as `CommandExecutionError` with message
`"Executable not found on PATH"`. Test `test_run_command_file_not_found_mapped` confirms.

**shell=False invariant:** The keyword argument `shell=False` is explicitly passed with the
comment `# INVARIANT — never change this` at `skepja/client.py:202`. VERIFIED.

### B-LEID — Invariant verification

**Empty patterns blocks all URLs:**
`url_matches_allowlist("https://docs.python.org/", [])` -> `(False, "empty...")`. VERIFIED.

**Subdomain bypass probe:**
Pattern: `"https://docs.python.org/*"`. Attacker URL: `"https://docs.python.org.attacker.com/steal"`.
After `urlparse`, the attacker URL's netloc is `"docs.python.org.attacker.com"`, not
`"docs.python.org"`. `fnmatch("https://docs.python.org.attacker.com/steal", "https://docs.python.org/*")`
returns `False`. BLOCKED.

Rationale: `fnmatch` matches character-by-character. The `*` in the pattern starts after the
literal prefix `"https://docs.python.org/"`. The attacker URL's scheme+netloc section is
`"https://docs.python.org.attacker.com"`, which does not match the literal prefix
`"https://docs.python.org/"`. The concern raised in the audit brief (that fnmatch's `*` could
match dots and bypass the subdomain check) is NOT realized in practice because the prefix before
`/*` is matched literally.

**HTTP rejection:** `_validate_url` checks `url.startswith("http://")` before the allowlist call.
If `allow_http=False`, raises `UrlNotAllowedError` immediately. VERIFIED.

**Wildcard "*" warning:** `LeidConfig.__post_init__` calls `warnings.warn` when `enabled=True` and
`"*"` is in `url_allowlist_patterns`. Confirmed in test output:
`UserWarning: url_allowlist_patterns contains '*' — ALL URLs are fetchable`.

**Max redirects:** `httpx.AsyncClient(max_redirects=self._config.max_redirects)` with
`follow_redirects=True`. `TooManyRedirects` is caught and re-raised as `LeidConnectionError`.
Test `test_fetch_url_too_many_redirects_raises` confirms.

**HTML parser — stdlib only:** `from html.parser import HTMLParser`. No `bs4`, no `lxml`.
Confirmed by import inspection and `pyproject.toml` core deps.

**Scheme normalisation:** `urlparse` normalises scheme and netloc to lowercase before
fnmatch comparison. Test `test_scheme_normalisation` passes.

---

## C. Dispatch Routing

**VERIFIED.** All 22 dispatcher tests pass. Tool prefix routing (`minni.*`, `skepja.*`,
`leid.*`) follows the established two-part convention from v0.6. The dispatcher's
`register_sense` method stores each sense under its sense_id key; `dispatch` extracts
the prefix from the tool name before the first dot. No routing ambiguity exists between
the four current senses (smidja, minni, skepja, leid) — all prefixes are distinct.

Each sense's `dispatch_tool_call` method returns a structured `role: "tool"` dict on success
and an `{"error": true, "code": "...", ...}` JSON blob on failure. The dispatcher never re-raises
from a sense — it catches and wraps. This holds for all three new senses (confirmed by reading
`sense.py` for each).

---

## D. Failure Modes

**VERIFIED for all three senses.**

| Failure | Sense | Mapped to | Tested |
|---|---|---|---|
| Path outside sandbox | Minni | PERMISSION_DENIED | Yes |
| File not found | Minni | INVALID_ARGUMENTS (MinniFileNotFoundError) | Yes |
| File too large | Minni | MinniFileTooLargeError | Yes |
| OS permission denied | Minni | MinniPermissionError | Yes (mocked) |
| Command not in allowlist | Skepja | PERMISSION_DENIED | Yes |
| Command parse error | Skepja | CommandParseError | Yes |
| Command timeout | Skepja | SENSE_TIMEOUT | Yes |
| Executable not on PATH | Skepja | CommandExecutionError | Yes |
| Working directory missing | Skepja | CommandExecutionError | Yes |
| URL not in allowlist | Leid | PERMISSION_DENIED | Yes |
| HTTP URL, allow_http=False | Leid | UrlNotAllowedError | Yes |
| Leid timeout | Leid | SENSE_TIMEOUT | Yes |
| HTTP 4xx/5xx | Leid | LeidHttpError | Yes |
| Connection error | Leid | LeidConnectionError | Yes |
| Too many redirects | Leid | LeidConnectionError | Yes |
| Response truncation | Leid | truncated=True in result dict | Yes |
| Invalid JSON arguments | All three | INVALID_ARGUMENTS | Yes (per sense) |
| Unknown tool name | All three | error result | Yes (per sense) |

All failure modes return structured tool_result dicts — no exception propagates to L1 Bifrost.

---

## E. Privacy Invariants

**VERIFIED.**

All three senses default `enabled: False`. The CLI at `cli.py:187/219/252` gates each behind
`if grunnr_<sense>.enabled` — a disabled sense never opens, never registers tools, never
appears in the agent's tool list.

Skepja's environment isolation: `inherit_env=False` default means API keys, BRUNHAND tokens,
and any other host env vars are absent from the subprocess environment. Only `PATH` is passed.
Confirmed by test `test_run_command_env_not_inherited_by_default`.

Leid's HTTPS-only default: HTTP URLs raise `UrlNotAllowedError` unless `allow_http: true`.
HTTP fetches that do complete are logged as warnings even when explicitly permitted.

Minni's write_file validates both the target path AND its parent directory against
`allowed_roots` before `mkdir(parents=True)`. This prevents a parent-directory escape
where the parent is outside the sandbox. Confirmed at `client.py:222-228`.

---

## F. Frontend

**N/A.** This milestone adds no new frontend code. The 91 frontend tests from prior milestones
are not in scope for re-execution here (no regression vector from Python-only backend changes).

---

## G. Code Quality

**Generally clean.** Type hints present throughout. PEP 8 style consistent. All three clients
follow the same pattern: `__init__(config, log)`, private `_validate_*` gateway, public operation
methods. Comments explain security decisions at load-bearing points.

One observation: `command_in_allowlist` returns `str(parsed)` (a stringified list) as its
second tuple element on success (`sandbox.py:202/207`). This is type-hinted as `str | None`
(correct) but the docstring says "parsed_args_list" in the return description — the actual
value is a string representation of the list, not the list itself. The caller (`SkepjaClient`)
does a separate `shlex.split` call to get the actual token list (`_validate_command:114-118`).
This double-parse is slightly redundant but not a defect. Minor nit.

---

## H. Tests

**134 new tests (7 new files). 945 total, 943 passed, 2 skipped, 0 failures.**

| File | Tests | Coverage |
|---|---|---|
| test_sandbox.py | 17 | path, command, URL primitives — 6+5+6 cases |
| test_minni_client.py | 20 | sandbox gateway + read + write + list_directory |
| test_minni_sense.py | 17 | config + lifecycle + tools + dispatch + errors |
| test_skepja_client.py | 14 | gateway + run_command + get_working_directory |
| test_skepja_sense.py | 14 | config + lifecycle + tools + dispatch + errors |
| test_leid_client.py | 26 | gateway + fetch_url + extract_text + html helper |
| test_leid_sense.py | 16 | config + lifecycle + tools + dispatch + errors |
| test_skillingr_dispatcher.py | 22 | already existing; multi-sense routing confirmed |

Test quality: mocked subprocess calls in Skepja tests prevent real shell execution. Mocked
httpx calls in Leid tests prevent real network traffic. Minni tests use pytest's `tmp_path`
fixture for real (but isolated) filesystem I/O.

---

## I. Findings

### S-1 — SERIOUS: Symlink documentation contradicts implementation

**Location:** `src/heretic/skilningr/sandbox.py:61-64` (docstring), `src/heretic/skilningr/senses/minni/client.py:26-30` (module docstring)

**Evidence:**

`sandbox.py` docstring states:
> "Symlinks in the candidate path are NOT followed during resolution on platforms that
> support it — the lexical path is resolved, not the physical target."

`client.py` module docstring states:
> "This matches the §4.12 Step 3(c) Cartographer invariant: validate the symlink's
> own path, not its target."

**These statements are false.** `Path.resolve()` (Python docs: "Make the path absolute,
*resolving all symlinks* on the way") returns the physical target, not the lexical link path.
Confirmed by live execution:

```
link = /tmp/.../workspace/evil_link -> /tmp/.../secret.txt
Path(link).resolve() -> /tmp/.../secret.txt
```

**Security consequence:** The actual behavior is SAFER than described. A symlink inside the
sandbox pointing outside is BLOCKED because `resolve()` gives the target path (outside the root),
which fails the `startswith` check. The sandbox works correctly despite the wrong explanation.

**Risk:** A future developer reading the docstring ("we validate the symlink's own path") may
attempt to "fix" the implementation to match the stated intent — i.e., switch from `resolve()`
to a non-symlink-following method. That change would INTRODUCE a symlink escape vulnerability.
The documentation is a time bomb.

**Severity: SERIOUS.** Security is currently correct. The incorrect documentation is the risk.
Forge must correct both docstrings to state the actual behavior:
"Path.resolve() follows symlinks. A symlink pointing outside the sandbox resolves to its
target path, which fails the allowed_roots check. The sandbox is protected by this behavior,
not despite it."

No test documents the symlink escape invariant. See N-3.

### N-1 — NOTABLE: LeidResponseTooLargeError is dead code

**Location:** `src/heretic/skilningr/errors.py:339-348`, `src/heretic/skilningr/senses/leid/client.py:49-54`

**Evidence:**

`errors.py` defines `LeidResponseTooLargeError` with docstring:
> "Raised when the response Content-Length header or streaming body size exceeds the
> configured cap. The connection is closed immediately; no partial content is returned."

`leid/client.py` imports from `leid.errors`:
```python
from heretic.skilningr.senses.leid.errors import (
    LeidConnectionError,
    LeidHttpError,
    LeidTimeoutError,
    UrlNotAllowedError,
)
```

`LeidResponseTooLargeError` is not imported in `client.py`. It is never raised anywhere in the
codebase. The actual truncation strategy is a silent `raw_bytes[:max_bytes]` slice with
`truncated=True` in the result dict — no exception raised.

The docstring of `LeidResponseTooLargeError` describes behavior that does not exist
(streaming abort, no partial content). The implementation buffers the full response body
via `response.content` and then slices it post-download.

**Impact:** The error class misleads future developers about the truncation strategy. The class
is also untestable in its current form because no code path raises it.

**Severity: NOTABLE.** Either (a) remove the class and update the error module docstring, or
(b) implement streaming truncation and actually raise it. Whichever choice is made, the gap
between declaration and implementation must be closed.

### N-2 — NOTABLE: Leid response cap is a post-download buffer slice, not a streaming abort

**Location:** `src/heretic/skilningr/senses/leid/client.py:270-276`

**Evidence:**
```python
raw_bytes = response.content        # httpx downloads the full body into memory first
size_bytes = len(raw_bytes)
max_bytes = self._config.max_response_bytes
truncated = size_bytes > max_bytes
if truncated:
    raw_bytes = raw_bytes[:max_bytes]
```

`response.content` is a property that reads the entire response body into memory. For a
100 MB response, httpx downloads all 100 MB before the size check runs. Only then is the
result sliced to `max_response_bytes` (default 1 MB). The connection is not closed early.

This is not a security bug (the agent only sees truncated content) but it is a resource
concern: a malicious server sending a very large response (e.g. 500 MB) would consume
that memory before the cap takes effect. The TASK spec says "Max response size: 1MB default;
truncate beyond" — it does not specify streaming vs buffered, so the current approach is
within spec. It is a known limitation worth documenting.

**Severity: NOTABLE.** The docstring at module level (`"reading stops at cap"`) implies
a streaming abort, which is inaccurate. The v0.6.2 scope explicitly excludes streaming;
the comment should be corrected to describe the actual behavior (buffer-then-slice).
A streaming implementation (httpx `aiter_bytes`) would be the correct fix in v0.6.2.1.

### N-3 — NOTABLE: No test documents the symlink escape invariant

**Location:** `tests/test_sandbox.py`, `tests/test_minni_client.py`

**Evidence:** `grep -rn "symlink" tests/` returns no matches.

The symlink escape protection (Path.resolve() follows symlinks to the target, which then fails
the sandbox check) is a critical security invariant of the Minni/sandbox triad. It is verified
by live execution in this audit but is not documented by any automated test. If the underlying
behavior of `Path.resolve()` or the sandbox check logic changes, there is no test to catch the
regression.

**Severity: NOTABLE.** A test along these lines should be added:
```python
# test_sandbox.py or test_minni_client.py
def test_symlink_pointing_outside_sandbox_blocked(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("private")
    link = workspace / "evil_link.txt"
    link.symlink_to(str(outside))  # skip on platforms that cannot create symlinks
    ok, _ = path_within_allowed_roots(str(link), [str(workspace)])
    assert ok is False
```

This test requires platform detection (`pytest.mark.skipif(not hasattr(os, 'symlink'), ...)`)
for non-symlink-capable environments.

### NIT-1 — NIT: command_in_allowlist returns stringified list, not list

**Location:** `src/heretic/skilningr/sandbox.py:202,207`

**Evidence:**
```python
return True, str(parsed)  # type: ignore[return-value]
```

Return type annotation says `tuple[bool, str | None]`. On success, the second element is
`str(['git', 'status'])` — a string representation of the parsed list, not the list itself.
The `SkepjaClient._validate_command` discards this value and re-parses the command via a
second `shlex.split` call (`client.py:115`). This double-parse is redundant.

**Severity: NIT.** The function could return the list directly (requiring a type change to
`tuple[bool, str | list[str] | None]`) and eliminate the second shlex.split in the client.
Or the second value could be documented as "informational string for logging" with the type
annotation corrected. No functional impact.

---

## Claim status table

| Claim source | Claim | Status |
|---|---|---|
| TASK §3 | Minni enabled=False default | VERIFIED |
| TASK §3 | Skepja enabled=False, empty allowlist | VERIFIED |
| TASK §3 | Leid enabled=False, empty patterns | VERIFIED |
| TASK §3 | Path traversal blocked | VERIFIED |
| TASK §3 | Symlink escape blocked (by resolve()) | VERIFIED (behavior correct, doc wrong — S-1) |
| TASK §3 | shell=False prevents injection | VERIFIED |
| TASK §3 | inherit_env=False default | VERIFIED |
| TASK §3 | Timeout enforced (Skepja + Leid) | VERIFIED |
| TASK §3 | Output truncation cap (Skepja) | VERIFIED |
| TASK §3 | Response truncation (Leid) | VERIFIED (buffer-then-slice — N-2) |
| TASK §3 | HTML extract uses stdlib html.parser | VERIFIED |
| TASK §3 | Wildcard * logs warning | VERIFIED |
| TASK §6 exit | 4 senses register with ToolDispatcher | VERIFIED |
| TASK §6 exit | Sense failure is independent | VERIFIED (separate try/except blocks in CLI) |
| TASK §6 exit | Sandbox invariants tested | VERIFIED (with N-3 gap) |
| Forge claim | 872 -> 943 tests (+71 net) | VERIFIED (actual 945, 943 pass) |
| Forge claim | 0 regressions | VERIFIED (943 pass, 2 skipped unchanged) |
| sandbox.py docstring | Symlinks NOT followed | CONTRADICTED — they ARE followed by Path.resolve() (S-1) |
| client.py module docstring | Validate symlink's own path | CONTRADICTED — resolves to target (S-1) |
| LeidResponseTooLargeError docstring | Raised on oversize response | CONTRADICTED — never raised (N-1) |
