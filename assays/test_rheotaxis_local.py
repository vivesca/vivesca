"""Tests for rheotaxis-local effector.

Effectors are scripts — loaded via exec(open(path).read(), ns), never imported.
"""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTORS_DIR = Path(__file__).resolve().parent.parent / "effectors"
RHEOTAXIS_PATH = EFFECTORS_DIR / "rheotaxis-local"


def _load() -> dict:
    """Load rheotaxis-local into an isolated namespace."""
    assert RHEOTAXIS_PATH.exists(), f"Effector not found: {RHEOTAXIS_PATH}"
    ns: dict = {"__name__": "test_rheotaxis_local_module", "__file__": str(RHEOTAXIS_PATH)}
    exec(RHEOTAXIS_PATH.read_text(), ns)
    return ns


# ---------------------------------------------------------------------------
# _extract_query
# ---------------------------------------------------------------------------

class TestExtractQuery:
    def _get_func(self):
        return _load()["_extract_query"]

    def test_strips_markdown_and_urls(self):
        fn = self._get_func()
        text = "# Heading **bold** `code` https://example.com/thing [link](url)"
        result = fn(text)
        assert "https://" not in result
        assert "#" not in result
        assert "**" not in result
        assert "Heading" in result
        assert "bold" in result

    def test_returns_at_most_15_words(self):
        fn = self._get_func()
        words = " ".join(f"word{i}" for i in range(50))
        result = fn(words)
        assert len(result.split()) <= 15

    def test_filters_short_words(self):
        fn = self._get_func()
        text = "a bb cat doge elephant"
        result = fn(text)
        assert "a" not in result.split()
        assert "bb" not in result.split()
        assert "cat" in result.split()
        assert "doge" in result.split()

    def test_empty_string_returns_empty(self):
        fn = self._get_func()
        assert fn("") == ""

    def test_only_short_words_returns_empty(self):
        fn = self._get_func()
        assert fn("a b c d e f") == ""


# ---------------------------------------------------------------------------
# query_qmd
# ---------------------------------------------------------------------------

class TestQueryQmd:
    def _get_func(self):
        return _load()["query_qmd"]

    def test_returns_stdout_on_success(self):
        fn = self._get_func()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "qmd://notes/foo.md:1\nScore: 0.9\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            out = fn("some text", limit=3)

        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == "qmd"
        assert cmd_args[1] == "vsearch"
        assert out == "qmd://notes/foo.md:1\nScore: 0.9"

    def test_exits_on_nonzero_returncode(self):
        fn = self._get_func()
        ns = _load()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "something failed"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit):
                fn("some text")


# ---------------------------------------------------------------------------
# format_callout
# ---------------------------------------------------------------------------

class TestFormatCallout:
    def _get_func(self):
        return _load()["format_callout"]

    def test_formats_qmd_paths_as_callout(self):
        fn = self._get_func()
        qmd_out = textwrap.dedent("""\
        qmd://notes/projects/alpha.md:12
        Score: 0.95
        qmd://notes/projects/beta.md:34
        Score: 0.88
        """)
        result = fn(qmd_out, Path("notes/my-note.md"))
        assert "> [!related] Related notes" in result
        assert "[[alpha]]" in result
        assert "[[beta]]" in result
        assert "0.95" in result
        assert "0.88" in result

    def test_excludes_self_references(self):
        fn = self._get_func()
        qmd_out = textwrap.dedent("""\
        qmd://notes/my-note.md:1
        Score: 0.99
        qmd://notes/other.md:5
        Score: 0.70
        """)
        result = fn(qmd_out, Path("notes/my-note.md"))
        assert "[[my-note]]" not in result
        assert "[[other]]" in result

    def test_title_lines(self):
        fn = self._get_func()
        qmd_out = textwrap.dedent("""\
        Title: My Great Note
        Score: 0.91
        """)
        result = fn(qmd_out, Path("notes/current.md"))
        assert "[[My Great Note]]" in result

    def test_returns_empty_on_no_entries(self):
        fn = self._get_func()
        qmd_out = "some irrelevant text\nno entries here"
        result = fn(qmd_out, Path("notes/current.md"))
        assert result == ""

    def test_limits_to_six_entries(self):
        fn = self._get_func()
        lines = []
        for i in range(10):
            lines.append(f"qmd://notes/note{i}.md:1")
            lines.append(f"Score: 0.{90 - i}")
        qmd_out = "\n".join(lines) + "\n"
        result = fn(qmd_out, Path("notes/current.md"))
        # Count bullet lines (lines starting with "> - ")
        bullet_lines = [l for l in result.splitlines() if l.startswith("> - ")]
        assert len(bullet_lines) == 6


# ---------------------------------------------------------------------------
# main — integration via subprocess.run mock + tmp file
# ---------------------------------------------------------------------------

class TestMain:
    def test_dry_run_prints_callout(self, tmp_path):
        note = tmp_path / "test-note.md"
        note.write_text("This is a sufficiently long note content for testing purposes " * 5)

        ns = _load()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "qmd://notes/related.md:1\nScore: 0.85\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["rheotaxis-local", str(note), "--dry-run"]):
                with patch("builtins.print") as mock_print:
                    ns["main"]()

        printed = "\n".join(str(c) for c, _ in [c.args for c in mock_print.call_args_list])
        assert "[!related]" in printed or any("[!related]" in str(a) for a in mock_print.call_args)

    def test_appends_to_note(self, tmp_path):
        note = tmp_path / "test-note.md"
        note.write_text("Sufficiently long note content for testing rheotaxis functionality " * 5)

        ns = _load()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "qmd://notes/alpha.md:1\nScore: 0.9\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["rheotaxis-local", str(note)]):
                ns["main"]()

        updated = note.read_text()
        assert "[!related]" in updated
        assert "[[alpha]]" in updated

    def test_nonexistent_note_exits(self, tmp_path):
        ns = _load()
        with patch("sys.argv", ["rheotaxis-local", str(tmp_path / "nope.md")]):
            with pytest.raises(SystemExit):
                ns["main"]()

    def test_short_note_exits_cleanly(self, tmp_path):
        note = tmp_path / "short.md"
        note.write_text("hi")

        ns = _load()
        with patch("sys.argv", ["rheotaxis-local", str(note)]):
            with pytest.raises(SystemExit) as exc_info:
                ns["main"]()
            assert exc_info.value.code == 0

    def test_no_qmd_results_exits_cleanly(self, tmp_path):
        note = tmp_path / "test-note.md"
        note.write_text("Sufficiently long note content for testing rheotaxis functionality " * 5)

        ns = _load()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["rheotaxis-local", str(note)]):
                with pytest.raises(SystemExit) as exc_info:
                    ns["main"]()
                assert exc_info.value.code == 0
