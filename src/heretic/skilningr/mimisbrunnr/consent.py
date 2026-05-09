"""
Mímisbrunnr download consent — operator approval gate for library downloads.

The consent module enforces that no network download of a LibrarySource
occurs without explicit operator approval. This is the human-in-the-loop
gate that separates the decision to download from the act of downloading.

The gate has two modes:
    auto_yes=True  — Skips the interactive prompt. Returns True
                     immediately. Used in non-interactive deployments
                     where the operator has pre-approved downloads via
                     LibraryConfig (e.g. enabled: true + sources list).
    auto_yes=False — Prints a consent prompt to stdout and reads a
                     single line from stdin. Any response starting with
                     'y' or 'Y' returns True; anything else (including
                     empty input) raises ConsentRefused.

DESIGN CONTRACT:
    - prompt_for_download is the single function in this module. It is
      synchronous; callers do not need async.
    - The function never raises anything other than ConsentRefused or
      (indirectly) KeyboardInterrupt on Ctrl-C. It does not suppress
      KeyboardInterrupt — Ctrl-C propagates normally so the operator
      can abort at the prompt.
    - No download is attempted inside this module. The caller that
      receives True proceeds to call Downloader.download().

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Consent
     src/heretic/skilningr/mimisbrunnr/errors.py (ConsentRefused)
"""

from __future__ import annotations

from heretic.skilningr.mimisbrunnr.errors import ConsentRefused
from heretic.skilningr.mimisbrunnr.manifest import LibrarySource


def prompt_for_download(
    source: LibrarySource,
    auto_yes: bool = False,
) -> bool:
    """Ask the operator for consent to download a LibrarySource.

    In auto_yes mode (non-interactive deployments), returns True
    immediately without any I/O.

    In interactive mode (auto_yes=False), prints a prompt to stdout
    describing the source — title, URL, approximate size — and reads
    one line from stdin. A response beginning with 'y' or 'Y' returns
    True. Any other response raises ConsentRefused.

    Args:
        source:   The LibrarySource entry the operator is being asked
                  to approve.
        auto_yes: If True, skip the prompt and return True immediately.
                  Default False (interactive, require explicit consent).

    Returns:
        True if the operator consents to the download.

    Raises:
        ConsentRefused: if the operator declines (or enters anything
            other than a 'y'/'yes' response in interactive mode).
    """
    if auto_yes:
        return True

    # Format the size for human-readable display
    size_bytes = source.expected_size_bytes
    if size_bytes >= 1_000_000:
        size_str = f"{size_bytes / 1_000_000:.1f} MB"
    elif size_bytes >= 1_000:
        size_str = f"{size_bytes / 1_000:.1f} KB"
    else:
        size_str = f"{size_bytes} bytes"

    print()
    print("Mímisbrunnr — Download consent required")
    print("-" * 45)
    print(f"  Title   : {source.title}")
    print(f"  URL     : {source.url}")
    print(f"  Size    : ~{size_str}")
    print(f"  License : {source.license}")
    print()

    try:
        response = input("Download this source? [y/N] ").strip()
    except EOFError:
        # Non-interactive stdin (piped empty, CI without input) — treat as refusal
        raise ConsentRefused(
            f"Operator declined download of {source.id!r} "
            "(stdin closed — non-interactive mode; use --yes flag to bypass)"
        )

    if response.lower().startswith("y"):
        return True

    raise ConsentRefused(
        f"Operator declined download of {source.id!r}. "
        f"Response: {response!r}. "
        "Pass --yes to skip the consent prompt."
    )
