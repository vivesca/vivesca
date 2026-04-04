from __future__ import annotations

"""Tests for effectors/rheotaxis-local — ambient related-notes surfacer."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "rheotaxis-local"


def _load_effector():
    """Load the rheotaxis-local effector by exec-ing its source."""
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "rheotaxis_local_test"}
    exec(source, ns)
    return ns


_mod = _load_effector()
_extract_query = _mod["_extract_query"]
query_qmd = _mod["query_qmd"]
format_callout = _mod["format_callout"]
main = _mod["main"]


# ── _extract_query tests ──────────────────────────────────────────────


def test_extract_query_basic():
    """Extract meaningful words (>3 chars) from plain text."""
    text = "This is a simple note about python programming"
    result = _extract_query(text)
    assert "simple" in result
    assert "note" in result
    assert "about" in result
    assert "python" in result
    assert "programming" in result
    assert "is" not in result.split()
    assert "a" not in result.split()


def test_extract_query_strips_markdown():
    """Markdown syntax characters are removed before word extraction."""
    text = "# Heading **bold** `code` [link](url)"
    result = _extract_query(text)
    assert "#" not in result
    assert "**" not in result
    assert "`" not in result
    assert "[" not in result


def test_extract_query_strips_urls():
    """URLs are removed before word extraction."""
    text = "Check https://example.com/page for details about testing"
    result = _extract_query(text)
    assert "https://example.com/page" not in result
    assert "details" in result
    assert "testing" in result


def test_extract_query_limit_15_words():
    """At most 15 meaningful words are returned."""
    words = " ".join(f"word{i:02d}" for i in range(30))
    result = _extract_query(words)
    assert len(result.split()) == 15


def test_extract_query_empty_string():
    """Empty input produces empty query."""
    assert _extract_query("") == ""


def test_extract_query_only_short_words():
    """Text with only short words (<4 chars) produces empty query."""
    assert _extract_query("a b c d e f g hi") == ""


# ── format_callout tests ──────────────────────────────────────────────


def test_format_callout_qmd_urls():
    """qmd:// entries are parsed into wikilinks with scores."""
    qmd_output = (
        "qmd://notes/projects/alpha.md:10 #design\n"
        "Score: 0.95\n"
        "qmd://notes/projects/beta.md:5 #testing\n"
        "Score: 0.82\n"
    )
    result = format_callout(qmd_output, Path("gamma.md"))
    assert "> [!related] Related notes" in result
    assert "[[alpha]] (0.95)" in result
    assert "[[beta]] (0.82)" in result


def test_format_callout_title_lines():
    """Title: lines are used as the link name."""
    qmd_output = "Title: My Great Note\nScore: 0.91\n"
    result = format_callout(qmd_output, Path("other.md"))
    assert "[[My Great Note]] (0.91)" in result


def test_format_callout_excludes_self_references():
    """Entries matching the note's own stem are excluded."""
    qmd_output = (
        "qmd://notes/projects/self-note.md:10 #design\n"
        "Score: 0.99\n"
        "qmd://notes/projects/other-note.md:5 #testing\n"
        "Score: 0.80\n"
    )
    result = format_callout(qmd_output, Path("self-note.md"))
    assert "self-note" not in result
    assert "[[other-note]] (0.80)" in result


def test_format_callout_empty_input():
    """Empty qmd output returns empty string."""
    assert format_callout("", Path("note.md")) == ""


def test_format_callout_all_self_refs():
    """If all entries are self-references, return empty string."""
    qmd_output = "qmd://notes/my-note.md:1 #tag\nScore: 0.99\n"
    result = format_callout(qmd_output, Path("my-note.md"))
    assert result == ""


def test_format_callout_max_six_entries():
    """At most 6 entries are included in the callout."""
    lines = []
    for i in range(10):
        lines.append(f"Title: Note {i:02d}")
        lines.append(f"Score: 0.{9 - i}")
    qmd_output = "\n".join(lines) + "\n"
    result = format_callout(qmd_output, Path("test.md"))
    bullet_count = result.count("> -")
    assert bullet_count == 6


def test_format_callout_md_extension_stripped():
    """The .md extension is stripped from qmd:// paths."""
    qmd_output = "qmd://notes/vault/my-page.md:1 #tag\nScore: 0.90\n"
    result = format_callout(qmd_output, Path("other.md"))
    assert "[[my-page]] (0.90)" in result
    assert ".md" not in result.split("(0.90)")[0]


def test_format_callout_notes_prefix_stripped():
    """The qmd://notes/ prefix is stripped from paths."""
    qmd_output = "qmd://notes/deep/nested/page.md:1\nScore: 0.75\n"
    result = format_callout(qmd_output, Path("root.md"))
    assert "[[page]] (0.75)" in result
    assert "notes/" not in result


# ── query_qmd tests (mocked subprocess) ───────────────────────────────


def test_query_qmd_success():
    """query_qmd returns stdout on success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Title: Result\nScore: 0.9\n"
    mock_result.stderr = ""

    with patch.object(_mod["subprocess"], "run", return_value=mock_result) as mock_run:
        result = query_qmd("test query", limit=5)
    assert "Title: Result" in result
    mock_run.assert_called_once_with(
        ["qmd", "vsearch", "test query"],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_query_qmd_nonzero_exit():
    """query_qmd exits with code 1 when qmd fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "index not found"

    with patch.object(_mod["subprocess"], "run", return_value=mock_result):
        with pytest.raises(SystemExit) as exc_info:
            query_qmd("test query")
        assert exc_info.value.code == 1


def test_query_qmd_passes_extracted_query():
    """query_qmd uses _extract_query to process input text."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch.object(_mod["subprocess"], "run", return_value=mock_result) as mock_run:
        query_qmd("some meaningful text about programming", limit=3)
    called_query = mock_run.call_args[0][0][2]
    assert "meaningful" in called_query
    assert "programming" in called_query


# ── main CLI tests (mocked subprocess + sys.argv) ─────────────────────


def _make_qmd_mock(stdout="", returncode=0, stderr=""):
    """Build a mock subprocess.run result."""
    mock_result = MagicMock()
    mock_result.returncode = returncode
    mock_result.stdout = stdout
    mock_result.stderr = stderr
    return mock_result


def _run_main(args: list[str]):
    """Run main() with patched sys.argv."""
    with patch.object(sys, "argv", ["rheotaxis-local", *args]):
        main()


class TestMain:
    """Tests for the main() CLI entry point."""

    def test_note_not_found_exits(self):
        """Nonexistent note path prints error and exits 1."""
        with pytest.raises(SystemExit) as exc_info:
            _run_main(["/nonexistent/path/to/note.md"])
        assert exc_info.value.code == 1

    def test_short_note_exits_cleanly(self, tmp_path, capsys):
        """Notes shorter than 50 chars exit 0 with a message."""
        note = tmp_path / "short.md"
        note.write_text("Hi", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            _run_main([str(note)])
        assert exc_info.value.code == 0
        assert "too short" in capsys.readouterr().err

    def test_dry_run_prints_callout(self, tmp_path, capsys):
        """--dry-run prints the callout to stdout without modifying the file."""
        note = tmp_path / "test-note.md"
        original = (
            "This is a test note about python programming "
            "and software development practices in the wild"
        )
        note.write_text(original, encoding="utf-8")
        qmd_output = "Title: Related Article\nScore: 0.88\n"
        with patch.object(_mod["subprocess"], "run", return_value=_make_qmd_mock(qmd_output)):
            _run_main([str(note), "--dry-run"])
        captured = capsys.readouterr()
        assert "[[Related Article]] (0.88)" in captured.out
        assert note.read_text(encoding="utf-8") == original

    def test_append_mode_modifies_file(self, tmp_path, capsys):
        """Without --dry-run, the callout is appended to the note."""
        note = tmp_path / "test-note.md"
        original = (
            "This is a test note about python programming "
            "and software development practices in the wild"
        )
        note.write_text(original, encoding="utf-8")
        qmd_output = "Title: Related Article\nScore: 0.88\n"
        with patch.object(_mod["subprocess"], "run", return_value=_make_qmd_mock(qmd_output)):
            _run_main([str(note)])
        captured = capsys.readouterr()
        assert "Appended" in captured.out
        new_content = note.read_text(encoding="utf-8")
        assert original in new_content
        assert "[[Related Article]] (0.88)" in new_content

    def test_no_results_exits_cleanly(self, tmp_path, capsys):
        """When qmd returns empty output, exit 0 with a message."""
        note = tmp_path / "test-note.md"
        note.write_text(
            "This is a test note about python programming "
            "and software development practices in the wild",
            encoding="utf-8",
        )
        with patch.object(_mod["subprocess"], "run", return_value=_make_qmd_mock("")):
            with pytest.raises(SystemExit) as exc_info:
                _run_main([str(note)])
            assert exc_info.value.code == 0
        assert "No related notes found" in capsys.readouterr().out

    def test_all_self_refs_exits_cleanly(self, tmp_path, capsys):
        """When all results are self-references, exit 0."""
        note = tmp_path / "my-note.md"
        note.write_text(
            "This is a test note about python programming "
            "and software development practices in the wild",
            encoding="utf-8",
        )
        qmd_output = "qmd://notes/my-note.md:1 #tag\nScore: 0.99\n"
        with patch.object(_mod["subprocess"], "run", return_value=_make_qmd_mock(qmd_output)):
            with pytest.raises(SystemExit) as exc_info:
                _run_main([str(note)])
            assert exc_info.value.code == 0
        assert "No related notes (excluding self)" in capsys.readouterr().out

    def test_uses_filename_as_query(self, tmp_path):
        """When filename has enough words, it's used as the query."""
        note = tmp_path / "python-testing-guide.md"
        note.write_text(
            "A comprehensive guide to testing Python applications with pytest fixtures",
            encoding="utf-8",
        )
        qmd_output = "Title: Something\nScore: 0.5\n"
        with patch.object(
            _mod["subprocess"], "run", return_value=_make_qmd_mock(qmd_output)
        ) as mock_run:
            _run_main([str(note), "--dry-run"])
        called_query = mock_run.call_args[0][0][2]
        assert "python" in called_query.lower()
        assert "testing" in called_query.lower()
        assert "guide" in called_query.lower()
