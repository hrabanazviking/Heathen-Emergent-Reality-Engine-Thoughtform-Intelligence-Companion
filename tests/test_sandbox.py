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

import os
import sys

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

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="symlink creation requires elevated permissions on Windows",
    )
    def test_path_within_allowed_roots_symlink_inside_root_pointing_inside_is_ok(self, tmp_path):
        """A symlink that lives inside allowed_roots AND points to a target inside
        allowed_roots is accepted.

        Path.resolve() follows the symlink to its target. Since both the symlink
        and its target reside within allowed_roots the prefix check passes.
        """
        target_file = tmp_path / "real_file.txt"
        target_file.write_text("content", encoding="utf-8")
        link_path = tmp_path / "link_to_inside.txt"
        try:
            os.symlink(str(target_file), str(link_path))
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation failed on this platform/configuration")

        ok, result = path_within_allowed_roots(str(link_path), [str(tmp_path)])
        assert ok is True
        assert result is not None

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="symlink creation requires elevated permissions on Windows",
    )
    def test_path_within_allowed_roots_symlink_inside_root_pointing_outside_is_rejected(self, tmp_path):
        """A symlink that lives inside allowed_roots but points OUTSIDE is rejected.

        Path.resolve() follows the symlink to its physical target. The target
        is outside allowed_roots, so the prefix check fails and the path is
        rejected. This is the primary defence against sandbox escape via symlinks.
        """
        outside_dir = tmp_path.parent / "outside_sandbox"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret", encoding="utf-8")

        link_path = tmp_path / "evil_link.txt"
        try:
            os.symlink(str(outside_file), str(link_path))
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation failed on this platform/configuration")

        ok, reason = path_within_allowed_roots(str(link_path), [str(tmp_path)])
        assert ok is False
        assert "denied" in reason.lower() or "not within" in reason.lower()

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="symlink creation requires elevated permissions on Windows",
    )
    def test_path_within_allowed_roots_symlink_chain_resolves_to_outside_is_rejected(self, tmp_path):
        """A chain of symlinks where the final target is outside allowed_roots is rejected.

        Path.resolve() fully dereferences symlink chains. Even a two-hop chain
        that escapes the sandbox is caught.
        """
        outside_dir = tmp_path.parent / "outside_sandbox_chain"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "deep_secret.txt"
        outside_file.write_text("deep secret", encoding="utf-8")

        # Two-hop chain: link2 -> link1 -> outside_file
        link1 = tmp_path / "hop1.txt"
        link2 = tmp_path / "hop2.txt"
        try:
            os.symlink(str(outside_file), str(link1))
            os.symlink(str(link1), str(link2))
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation failed on this platform/configuration")

        ok, reason = path_within_allowed_roots(str(link2), [str(tmp_path)])
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
