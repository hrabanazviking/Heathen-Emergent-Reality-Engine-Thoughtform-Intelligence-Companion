"""
Skilningr shared sandbox primitives — path, command, and URL validation.

These three pure functions are the cross-cutting security seam shared by all
senses that operate on local resources or outbound networks. They are called
by MinniSense, SkepjaSense, and LeidSense BEFORE any I/O is performed.

Design invariants:
    - All functions are pure (no side effects, no I/O).
    - All functions are stdlib-only: pathlib, shlex, fnmatch, urllib.parse.
    - No new dependencies are introduced by this module.
    - Each returns a (bool, reason_or_value) tuple so callers never have to
      catch an exception to know why validation failed.
    - Sandbox violations are NEVER propagated as exceptions to L1 Bifröst.
      The caller catches False and constructs a structured tool_result error.

Path traversal protection (Minni):
    Path.resolve() canonicalises the path fully — any ../ sequences are
    collapsed into their real absolute form before comparison. There is no
    need to inspect the path string for ".." literally; the OS does the work.

Command injection protection (Skepja):
    shlex.split() raises ValueError on malformed shell quoting but does NOT
    execute the command. The first token (the executable) is compared against
    the operator-supplied allowlist. shell=False is enforced in the client;
    this function validates the pre-execution gate only.

URL allowlist (Leið):
    Patterns follow two forms:
        - Exact URL match:   "https://example.com/page"
        - Prefix wildcard:   "https://docs.python.org/*"   (trailing /*)
        - Full wildcard:     "*"  (unrestricted — warning emitted at config time)
    fnmatch is used for pattern matching so only "*" and "?" are special.
    Schemes are normalised to lowercase before comparison.

Ref: TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (sandbox invariants)
     src/heretic/skilningr/senses/minni/INTERFACE.md
     src/heretic/skilningr/senses/skepja/INTERFACE.md
     src/heretic/skilningr/senses/leid/INTERFACE.md
"""

from __future__ import annotations

import fnmatch
import shlex
from pathlib import Path
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Path validation (Minni — filesystem sense)
# ---------------------------------------------------------------------------

def path_within_allowed_roots(
    path: str | Path,
    allowed_roots: list[str],
) -> tuple[bool, str | None]:
    """Check whether *path* resolves to a location within one of *allowed_roots*.

    The check is performed on the fully-resolved, absolute form of both the
    candidate path and each allowed root. Path traversal sequences (../) are
    neutralised by Path.resolve(), which is called on both the candidate and
    each root.

    SYMLINK BEHAVIOUR — Path.resolve() FOLLOWS symlinks to their physical
    target. This is deliberate: a symlink inside allowed_roots that points
    outside (e.g. allowed_root/evil_link -> /etc/passwd) will resolve to the
    outside path, fail the prefix check, and be rejected. The earlier wording
    in this docstring ("lexical path is resolved, not the physical target")
    was incorrect — Path.resolve() is not strict=True/lexical; it calls the
    OS to dereference symlinks. Both the sandbox rejection of outside-pointing
    symlinks AND the stat-time follow_symlinks=False flag in MinniClient
    cooperate to enforce the full invariant; they operate at different layers.

    Raises nothing. Returns a two-element tuple:
        (True,  resolved_path_str)   — path is within an allowed root
        (False, reason_str)          — path is outside all allowed roots, or
                                       allowed_roots is empty, or path is empty

    Args:
        path:          The candidate file or directory path to validate.
                       May be relative (resolved relative to cwd) or absolute.
        allowed_roots: List of allowed root directory strings. Each is resolved
                       the same way as path. An empty list → always False.

    Examples:
        >>> path_within_allowed_roots(
        ...     "~/heretic_workspace/notes.md",
        ...     ["~/heretic_workspace"],
        ... )
        (True, '/home/user/heretic_workspace/notes.md')

        >>> path_within_allowed_roots(
        ...     "/etc/passwd",
        ...     ["~/heretic_workspace"],
        ... )
        (False, 'Path /etc/passwd is not within any allowed root ...')
    """
    if not path:
        return False, "Path must be a non-empty string."

    if not allowed_roots:
        return False, "No allowed_roots configured — all filesystem access is denied."

    # Resolve the candidate path. strict=False so the path need not exist yet
    # (write_file must be able to validate before the file exists).
    # expand ~ before resolving so ~/heretic_workspace works cross-platform.
    try:
        resolved_candidate = Path(path).expanduser().resolve()
    except (TypeError, ValueError, OSError) as exc:
        return False, f"Could not resolve path {path!r}: {exc}"

    resolved_candidate_str = str(resolved_candidate)

    # Check against each allowed root
    for root_str in allowed_roots:
        if not root_str:
            continue
        try:
            resolved_root = Path(root_str).expanduser().resolve()
        except (TypeError, ValueError, OSError):
            continue  # malformed root — skip, do not crash

        resolved_root_str = str(resolved_root)

        # A path is within a root if the candidate starts with the root path
        # followed by the OS separator (to prevent /allowed_rootExtra matching /allowed_root).
        # Handle the edge case where candidate IS the root directory itself.
        if (
            resolved_candidate_str == resolved_root_str
            or resolved_candidate_str.startswith(resolved_root_str + "/")
            or resolved_candidate_str.startswith(resolved_root_str + "\\")
        ):
            return True, resolved_candidate_str

    roots_display = ", ".join(repr(r) for r in allowed_roots)
    return (
        False,
        f"Path {resolved_candidate_str!r} is not within any allowed root "
        f"({roots_display}). Access denied.",
    )


# ---------------------------------------------------------------------------
# Command allowlist validation (Skepja — terminal sense)
# ---------------------------------------------------------------------------

def command_in_allowlist(
    command: str,
    allowlist: list[str],
) -> tuple[bool, str | None]:
    """Check whether *command*'s executable is in the operator-supplied *allowlist*.

    The command string is split via shlex.split() (POSIX mode); the first token
    (the executable name) is compared against every entry in allowlist. An entry
    may be either:
        - A bare executable name:  "git"
        - A full command pattern:  "git status"  (checked against full command)
    If allowlist is empty, no command is permitted.

    Returns a two-element tuple:
        (True,  parsed_args_list)   — first token is in allowlist (or full match)
        (False, reason_str)         — command rejected or unparseable

    Raises nothing.

    Args:
        command:   The raw command string the agent wants to run.
                   Must be non-empty.
        allowlist: Operator-supplied list of permitted executable names or
                   full command patterns. Empty list → always False.

    Note on shell injection:
        This function validates but does NOT execute. The Skepja client must
        always call subprocess.run(..., shell=False). shlex.split() here is
        purely for parsing, not for shell expansion.

    Examples:
        >>> command_in_allowlist("git status", ["git", "python"])
        (True, ['git', 'status'])

        >>> command_in_allowlist("rm -rf /", ["git", "python"])
        (False, "Command executable 'rm' is not in the allowlist.")

        >>> command_in_allowlist("git status", [])
        (False, "command_allowlist is empty — no commands are permitted.")
    """
    if not command or not command.strip():
        return False, "Command must be a non-empty string."

    if not allowlist:
        return (
            False,
            "command_allowlist is empty — no commands are permitted. "
            "Add allowed executables to skilningr.skepja.command_allowlist.",
        )

    # Parse the command string — may raise on malformed quoting
    try:
        parsed: list[str] = shlex.split(command)
    except ValueError as exc:
        return False, f"Could not parse command {command!r} with shlex: {exc}"

    if not parsed:
        return False, f"Command {command!r} parsed to an empty token list."

    executable = parsed[0]

    # Check: executable in allowlist (bare name match)
    if executable in allowlist:
        return True, str(parsed)  # type: ignore[return-value]

    # Check: full command matches an allowlist pattern (e.g. "git status")
    full_command_stripped = command.strip()
    if full_command_stripped in allowlist:
        return True, str(parsed)  # type: ignore[return-value]

    return (
        False,
        f"Command executable {executable!r} is not in the allowlist "
        f"({allowlist!r}). Add it to skilningr.skepja.command_allowlist to permit.",
    )


# ---------------------------------------------------------------------------
# URL allowlist validation (Leið — HTTP fetch sense)
# ---------------------------------------------------------------------------

def url_matches_allowlist(
    url: str,
    patterns: list[str],
) -> tuple[bool, str | None]:
    """Check whether *url* matches at least one pattern in *patterns*.

    Pattern forms supported:
        "*"                        — unrestricted wildcard (match any URL)
        "https://example.com/*"    — prefix wildcard via fnmatch
        "https://example.com/page" — exact match (after normalisation)

    URL normalisation applied before matching:
        - Scheme is lowercased ("HTTPS" → "https")
        - Netloc is lowercased ("Example.COM" → "example.com")
        - Trailing slash is preserved as given in both url and pattern

    No DNS resolution is performed. No redirects are followed here.
    HTTPS vs HTTP distinction is pattern-level — the operator must explicitly
    include "http://*" to allow HTTP fetches (not recommended).

    Returns a two-element tuple:
        (True,  normalised_url_str) — url matches at least one pattern
        (False, reason_str)         — no pattern matched or url is invalid

    Raises nothing.

    Args:
        url:      The URL the agent wants to fetch. Must be non-empty.
        patterns: Operator-supplied list of URL patterns. Empty list → always False.

    Examples:
        >>> url_matches_allowlist(
        ...     "https://docs.python.org/3/library/os.html",
        ...     ["https://docs.python.org/*"],
        ... )
        (True, 'https://docs.python.org/3/library/os.html')

        >>> url_matches_allowlist(
        ...     "https://evil.com/steal",
        ...     ["https://docs.python.org/*"],
        ... )
        (False, "URL 'https://evil.com/steal' does not match any allowed pattern.")
    """
    if not url or not url.strip():
        return False, "URL must be a non-empty string."

    if not patterns:
        return (
            False,
            "url_allowlist_patterns is empty — no URLs are permitted. "
            "Add allowed URL patterns to skilningr.leid.url_allowlist_patterns.",
        )

    # Normalise the candidate URL
    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme:
            return False, f"URL {url!r} has no scheme (expected https:// or http://)."
        normalised_url = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
        ).geturl()
    except Exception as exc:
        return False, f"Could not parse URL {url!r}: {exc}"

    # Check against each pattern
    for pattern in patterns:
        if not pattern:
            continue

        # Normalise the pattern the same way
        try:
            p_parsed = urlparse(pattern)
            if p_parsed.scheme:
                normalised_pattern = p_parsed._replace(
                    scheme=p_parsed.scheme.lower(),
                    netloc=p_parsed.netloc.lower(),
                ).geturl()
            else:
                # Bare "*" wildcard — no scheme to normalise
                normalised_pattern = pattern
        except Exception:
            normalised_pattern = pattern

        if fnmatch.fnmatch(normalised_url, normalised_pattern):
            return True, normalised_url

    patterns_display = ", ".join(repr(p) for p in patterns)
    return (
        False,
        f"URL {normalised_url!r} does not match any allowed pattern "
        f"({patterns_display}). Add a matching pattern to "
        f"skilningr.leid.url_allowlist_patterns.",
    )
