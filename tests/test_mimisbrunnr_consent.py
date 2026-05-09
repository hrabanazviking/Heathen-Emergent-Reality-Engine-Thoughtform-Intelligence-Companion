"""
Tests for Mímisbrunnr consent module — download approval gate.

Covers:
    - auto_yes=True returns True immediately without any I/O
    - auto_yes=False with 'y' response returns True
    - auto_yes=False with 'yes' response returns True
    - auto_yes=False with 'YES' response returns True
    - auto_yes=False with 'Y' response returns True
    - auto_yes=False with 'n' response raises ConsentRefused
    - auto_yes=False with '' (empty) response raises ConsentRefused
    - auto_yes=False with 'no' response raises ConsentRefused
    - auto_yes=False with EOF (non-interactive stdin) raises ConsentRefused
    - ConsentRefused message includes source_id

Ref: src/heretic/skilningr/mimisbrunnr/consent.py
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from heretic.skilningr.mimisbrunnr.consent import prompt_for_download
from heretic.skilningr.mimisbrunnr.errors import ConsentRefused
from heretic.skilningr.mimisbrunnr.manifest import LibrarySource


# ---------------------------------------------------------------------------
# Test fixture — a representative LibrarySource
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_source() -> LibrarySource:
    return LibrarySource(
        id="prose_edda_brodeur",
        title="The Younger Edda (Prose Edda) — Snorri Sturluson, trans. Brodeur (1916)",
        url="https://www.gutenberg.org/files/18947/18947-0.txt",
        license="Project Gutenberg License — public domain in the USA",
        expected_size_bytes=387_653,
        sha256=None,
    )


# ---------------------------------------------------------------------------
# auto_yes=True mode
# ---------------------------------------------------------------------------

class TestAutoYesMode:
    """With auto_yes=True, prompt must return True with no stdin interaction."""

    def test_returns_true_immediately(self, sample_source: LibrarySource) -> None:
        result = prompt_for_download(sample_source, auto_yes=True)
        assert result is True

    def test_does_not_read_stdin(self, sample_source: LibrarySource) -> None:
        """Verify no stdin reads happen (patch input to raise if called)."""
        with patch("builtins.input", side_effect=AssertionError("input() called unexpectedly")):
            result = prompt_for_download(sample_source, auto_yes=True)
        assert result is True

    def test_does_not_print_to_stdout(
        self, sample_source: LibrarySource, capsys: pytest.CaptureFixture
    ) -> None:
        """auto_yes mode should produce no output at all."""
        prompt_for_download(sample_source, auto_yes=True)
        captured = capsys.readouterr()
        assert captured.out == ""


# ---------------------------------------------------------------------------
# Interactive mode — affirmative responses
# ---------------------------------------------------------------------------

class TestInteractiveModeYes:
    """Interactive prompt must return True for affirmative user responses."""

    @pytest.mark.parametrize("response", ["y", "Y", "yes", "YES", "Yes", "yep", "yup"])
    def test_y_variants_return_true(
        self, sample_source: LibrarySource, response: str
    ) -> None:
        with patch("builtins.input", return_value=response):
            result = prompt_for_download(sample_source, auto_yes=False)
        assert result is True

    def test_y_with_whitespace_returns_true(self, sample_source: LibrarySource) -> None:
        """Leading/trailing whitespace around 'y' should be stripped."""
        with patch("builtins.input", return_value="  y  "):
            result = prompt_for_download(sample_source, auto_yes=False)
        assert result is True


# ---------------------------------------------------------------------------
# Interactive mode — declined responses
# ---------------------------------------------------------------------------

class TestInteractiveModeNo:
    """Interactive prompt must raise ConsentRefused for any non-affirmative response."""

    @pytest.mark.parametrize("response", ["n", "N", "no", "NO", "No", "nope", "", "maybe", "x"])
    def test_non_y_raises_consent_refused(
        self, sample_source: LibrarySource, response: str
    ) -> None:
        with patch("builtins.input", return_value=response):
            with pytest.raises(ConsentRefused):
                prompt_for_download(sample_source, auto_yes=False)

    def test_consent_refused_message_includes_source_id(
        self, sample_source: LibrarySource
    ) -> None:
        with patch("builtins.input", return_value="n"):
            with pytest.raises(ConsentRefused, match="prose_edda_brodeur"):
                prompt_for_download(sample_source, auto_yes=False)


# ---------------------------------------------------------------------------
# EOF / non-interactive stdin
# ---------------------------------------------------------------------------

class TestNonInteractiveStdin:
    """EOFError from stdin (piped empty) must raise ConsentRefused."""

    def test_eof_raises_consent_refused(self, sample_source: LibrarySource) -> None:
        with patch("builtins.input", side_effect=EOFError()):
            with pytest.raises(ConsentRefused, match="non-interactive"):
                prompt_for_download(sample_source, auto_yes=False)

    def test_eof_consent_refused_includes_source_id(
        self, sample_source: LibrarySource
    ) -> None:
        with patch("builtins.input", side_effect=EOFError()):
            with pytest.raises(ConsentRefused, match="prose_edda_brodeur"):
                prompt_for_download(sample_source, auto_yes=False)


# ---------------------------------------------------------------------------
# Output verification
# ---------------------------------------------------------------------------

class TestInteractiveModeOutput:
    """Interactive prompt must print source title, URL, and size."""

    def test_prints_title_and_url(
        self, sample_source: LibrarySource, capsys: pytest.CaptureFixture
    ) -> None:
        with patch("builtins.input", return_value="n"):
            with pytest.raises(ConsentRefused):
                prompt_for_download(sample_source, auto_yes=False)
        captured = capsys.readouterr()
        assert "Prose Edda" in captured.out or "Edda" in captured.out
        assert "gutenberg.org" in captured.out

    def test_prints_size_in_human_readable_form(
        self, sample_source: LibrarySource, capsys: pytest.CaptureFixture
    ) -> None:
        with patch("builtins.input", return_value="n"):
            with pytest.raises(ConsentRefused):
                prompt_for_download(sample_source, auto_yes=False)
        captured = capsys.readouterr()
        # 387_653 bytes should be shown as something with K or M
        assert any(unit in captured.out for unit in ("KB", "MB", "K", "M", "bytes"))
