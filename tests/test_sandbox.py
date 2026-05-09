"""
Tests for heretic.skilningr.sandbox — shared sandbox primitives.

These tests cover the three pure validation functions:
    path_within_allowed_roots()  — filesystem path sandbox gate
    command_in_allowlist()       — command allowlist gate
    url_matches_allowlist()      — URL allowlist gate

All tests are stdlib-only. No external dependencies required.

Ref: src/heretic/skilningr/sandbox.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (sandbox invariants)
"""

from __future__ import annotations

import pytest

from heretic.skilningr.sandbox import (
    command_in_allowlist,
    path_within_allowed_roots,
    url_matches_allowlist,
)


# ---------------------------------------------------------------------------
# path_within_allowed_roots
# ---------------------------------------------------------------------------

class TestPathWithinAllowedRoots:

    def test_path_within_root_accepted(self, tmp_path):
        """A path that resolves inside the allowed root is accepted."""
        root = str(tmp_path)
        target = str(tmp_path / "notes.md")
        ok, result = path_within_allowed_roots(target, [root])
        assert ok is True
        assert result is not None

    def test_path_outside_root_rejected(self, tmp_path):
        """A path outside all allowed roots is rejected."""
        root = str(tmp_path / "workspace")
        target = str(tmp_path / "outside" / "secret.txt")
        ok, reason = path_within_allowed_roots(target, [root])
        assert ok is False
        assert "denied" in reason.lower() or "not within" in reason.lower()

    def test_path_traversal_blocked(self, tmp_path):
        """A path that uses ../ to escape the sandbox is rejected after resolve()."""
        root = str(tmp_path / "workspace")
        # Attempt to escape via traversal — resolve() collapses this
        target = str(tmp_path / "workspace" / ".." / "outside" / "secret.txt")
        ok, reason = path_within_allowed_roots(target, [root])
        assert ok is False

    def test_empty_allowed_roots_always_rejects(self, tmp_path):
        """An empty allowed_roots list rejects any path."""
        ok, reason = path_within_allowed_roots(str(tmp_path), [])
        assert ok is False
        assert "empty" in reason.lower() or "no allowed" in reason.lower()

    def test_path_is_the_root_itself(self, tmp_path):
        """The root directory itself is within allowed_roots."""
        root = str(tmp_path)
        ok, result = path_within_allowed_roots(root, [root])
        assert ok is True

    def test_empty_path_rejected(self, tmp_path):
        """An empty path string is rejected."""
        ok, reason = path_within_allowed_roots("", [str(tmp_path)])
        assert ok is False


# ---------------------------------------------------------------------------
# command_in_allowlist
# ---------------------------------------------------------------------------

class TestCommandInAllowlist:

    def test_allowed_executable_accepted(self):
        """An executable present in the allowlist is accepted."""
        ok, result = command_in_allowlist("git status", ["git", "python"])
        assert ok is True

    def test_forbidden_executable_rejected(self):
        """An executable not in the allowlist is rejected."""
        ok, reason = command_in_allowlist("rm -rf /", ["git", "python"])
        assert ok is False
        assert "rm" in reason or "not in the allowlist" in reason

    def test_empty_allowlist_rejects_all(self):
        """An empty allowlist rejects all commands."""
        ok, reason = command_in_allowlist("git status", [])
        assert ok is False
        assert "empty" in reason.lower() or "no commands" in reason.lower()

    def test_empty_command_rejected(self):
        """An empty command string is rejected."""
        ok, reason = command_in_allowlist("", ["git"])
        assert ok is False

    def test_full_command_pattern_match(self):
        """A full command string matching an allowlist entry is accepted."""
        ok, result = command_in_allowlist("git status", ["git status"])
        assert ok is True


# ---------------------------------------------------------------------------
# url_matches_allowlist
# ---------------------------------------------------------------------------

class TestUrlMatchesAllowlist:

    def test_prefix_wildcard_accepted(self):
        """A URL matching a prefix wildcard pattern is accepted."""
        ok, result = url_matches_allowlist(
            "https://docs.python.org/3/library/os.html",
            ["https://docs.python.org/*"],
        )
        assert ok is True

    def test_url_outside_patterns_rejected(self):
        """A URL not matching any pattern is rejected."""
        ok, reason = url_matches_allowlist(
            "https://evil.com/steal",
            ["https://docs.python.org/*"],
        )
        assert ok is False
        assert "does not match" in reason or "not match" in reason

    def test_empty_patterns_rejects_all(self):
        """An empty patterns list rejects all URLs."""
        ok, reason = url_matches_allowlist("https://docs.python.org/", [])
        assert ok is False
        assert "empty" in reason.lower() or "no urls" in reason.lower()

    def test_exact_url_match(self):
        """An exact URL match (no wildcard) is accepted."""
        ok, result = url_matches_allowlist(
            "https://example.com/page",
            ["https://example.com/page"],
        )
        assert ok is True

    def test_wildcard_star_matches_any(self):
        """The bare '*' wildcard pattern matches any URL."""
        ok, result = url_matches_allowlist(
            "https://anything.example.com/anything",
            ["*"],
        )
        assert ok is True

    def test_empty_url_rejected(self):
        """An empty URL string is rejected."""
        ok, reason = url_matches_allowlist("", ["*"])
        assert ok is False

    def test_scheme_normalisation(self):
        """Uppercase scheme is normalised before matching."""
        ok, result = url_matches_allowlist(
            "HTTPS://docs.python.org/3/",
            ["https://docs.python.org/*"],
        )
        assert ok is True
