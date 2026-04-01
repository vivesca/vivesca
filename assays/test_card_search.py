from __future__ import annotations

"""Tests for card-search effector — search consulting cards by keyword."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_card_search():
    """Load card-search by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/card-search")).read()
    ns: dict = {"__name__": "card_search"}
    exec(source, ns)
    return ns


_mod = _load_card_search()
get_card_title = _mod["get_card_title"]
list_cards = _mod["list_cards"]
search_cards = _mod["search_cards"]
main = _mod["main"]
CARDS_DIR_original = _mod["CARDS_DIR"]


@pytest.fixture
def cards_dir(tmp_path):
    """Create a temporary cards directory with sample cards."""
    d = tmp_path / "cards"
    d.mkdir()
    return d


@pytest.fixture
def patch_cards_dir(cards_dir):
    """Patch CARDS_DIR to point at the temp cards directory."""
    original = _mod["CARDS_DIR"]
    _mod["CARDS_DIR"] = cards_dir
    yield cards_dir
    _mod["CARDS_DIR"] = original


def _write_card(cards_dir, filename, content):
    """Write a card .md file in the cards directory."""
    p = cards_dir / filename
    p.write_text(content)
    return p


# ── get_card_title tests ─────────────────────────────────────────────


def test_get_card_title_extracts_heading(cards_dir):
    """get_card_title returns the first # heading."""
    _write_card(cards_dir, "model-risk.md", "# Model Risk Framework\nSome content\n")
    title = get_card_title(cards_dir / "model-risk.md")
    assert title == "Model Risk Framework"


def test_get_card_title_no_heading_returns_stem(cards_dir):
    """get_card_title falls back to filename stem when no # heading."""
    _write_card(cards_dir, "notes.md", "Just some notes\nNo heading here\n")
    title = get_card_title(cards_dir / "notes.md")
    assert title == "notes"


def test_get_card_title_empty_file(cards_dir):
    """get_card_title returns stem for an empty file."""
    _write_card(cards_dir, "empty.md", "")
    title = get_card_title(cards_dir / "empty.md")
    assert title == "empty"


def test_get_card_title_nonexistent_file(cards_dir):
    """get_card_title returns stem when file does not exist."""
    title = get_card_title(cards_dir / "nonexistent.md")
    assert title == "nonexistent"


def test_get_card_title_heading_with_extra_whitespace(cards_dir):
    """get_card_title handles heading with trailing whitespace."""
    _write_card(cards_dir, "bias.md", "#  Bias in AI Systems  \nContent\n")
    title = get_card_title(cards_dir / "bias.md")
    assert title == "Bias in AI Systems"


def test_get_card_title_only_reads_first_heading(cards_dir):
    """get_card_title returns the first # heading, ignoring later ones."""
    _write_card(
        cards_dir,
        "multi.md",
        "# First Title\n## Subtitle\n# Second Title\n",
    )
    title = get_card_title(cards_dir / "multi.md")
    assert title == "First Title"


# ── list_cards tests ─────────────────────────────────────────────────


def test_list_cards_shows_all(cards_dir, patch_cards_dir, capsys):
    """list_cards prints all cards with their titles."""
    _write_card(cards_dir, "alpha.md", "# Alpha Card\nContent A\n")
    _write_card(cards_dir, "beta.md", "# Beta Card\nContent B\n")
    list_cards()
    out = capsys.readouterr().out
    assert "alpha: Alpha Card" in out
    assert "beta: Beta Card" in out


def test_list_cards_no_cards_exits(patch_cards_dir, capsys):
    """list_cards prints to stderr and exits with 1 when no cards."""
    with pytest.raises(SystemExit) as exc_info:
        list_cards()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "No cards found" in err


def test_list_cards_sorted_alphabetically(cards_dir, patch_cards_dir, capsys):
    """list_cards outputs cards in sorted order by filename."""
    _write_card(cards_dir, "zebra.md", "# Zebra\n")
    _write_card(cards_dir, "apple.md", "# Apple\n")
    _write_card(cards_dir, "mango.md", "# Mango\n")
    list_cards()
    out = capsys.readouterr().out
    lines = [l for l in out.strip().splitlines() if l.strip()]
    assert lines[0].startswith("apple")
    assert lines[1].startswith("mango")
    assert lines[2].startswith("zebra")


# ── search_cards tests ───────────────────────────────────────────────


def test_search_cards_finds_keyword(cards_dir, patch_cards_dir, capsys):
    """search_cards finds cards containing the keyword."""
    _write_card(cards_dir, "risk.md", "# Risk\nModel risk assessment framework\n")
    _write_card(cards_dir, "bias.md", "# Bias\nAlgorithmic bias detection\n")
    search_cards("risk")
    out = capsys.readouterr().out
    assert "risk" in out.lower()
    assert "1 card(s) found" in out


def test_search_cards_case_insensitive(cards_dir, patch_cards_dir, capsys):
    """search_cards performs case-insensitive search."""
    _write_card(cards_dir, "model.md", "# Model Risk\nModel Risk Framework\n")
    search_cards("MODEL")
    out = capsys.readouterr().out
    assert "model" in out.lower()
    assert "1 card(s) found" in out


def test_search_cards_no_match_exits_0(cards_dir, patch_cards_dir, capsys):
    """search_cards exits with 0 when no matches (not an error)."""
    _write_card(cards_dir, "other.md", "# Other\nSome content\n")
    with pytest.raises(SystemExit) as exc_info:
        search_cards("nonexistent_keyword_xyz")
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "No cards found matching" in out


def test_search_cards_missing_dir_exits(tmp_path, capsys):
    """search_cards exits with 1 when CARDS_DIR does not exist."""
    original = _mod["CARDS_DIR"]
    _mod["CARDS_DIR"] = tmp_path / "nonexistent_dir"
    try:
        with pytest.raises(SystemExit) as exc_info:
            search_cards("anything")
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "not found" in err.lower()
    finally:
        _mod["CARDS_DIR"] = original


def test_search_cards_full_mode(cards_dir, patch_cards_dir, capsys):
    """search_cards with full=True shows entire card content."""
    content = "# Full Card\nLine 1\nLine 2\nLine 3\nLine 4\n"
    _write_card(cards_dir, "full.md", content)
    search_cards("Full", full=True)
    out = capsys.readouterr().out
    assert "Line 1" in out
    assert "Line 2" in out
    assert "Line 3" in out
    assert "Line 4" in out


def test_search_cards_summary_mode_shows_three_lines(cards_dir, patch_cards_dir, capsys):
    """search_cards with full=False shows title + 3 non-empty lines."""
    content = "# Summary Card\n\nLine A\n\nLine B\n\nLine C\n\nLine D\n"
    _write_card(cards_dir, "summary.md", content)
    search_cards("Summary")
    out = capsys.readouterr().out
    assert "Line A" in out
    assert "Line B" in out
    assert "Line C" in out
    assert "Line D" not in out


def test_search_cards_multiple_matches(cards_dir, patch_cards_dir, capsys):
    """search_cards finds multiple matching cards."""
    _write_card(cards_dir, "a.md", "# A\nCommon topic discussed here\n")
    _write_card(cards_dir, "b.md", "# B\nAlso about common topic elsewhere\n")
    _write_card(cards_dir, "c.md", "# C\nCompletely unrelated content\n")
    search_cards("common")
    out = capsys.readouterr().out
    assert "2 card(s) found" in out


def test_search_cards_shows_file_stem_and_title(cards_dir, patch_cards_dir, capsys):
    """search_cards output includes both file stem and extracted title."""
    _write_card(cards_dir, "governance.md", "# Data Governance Policy\nDetails\n")
    search_cards("governance")
    out = capsys.readouterr().out
    assert "File: governance" in out
    assert "Title: Data Governance Policy" in out


# ── main (argparse) tests via subprocess ──────────────────────────────


CARDS_SEARCH_PATH = str(Path.home() / "germline/effectors/card-search")


def test_subprocess_no_args_exits_1():
    """card-search with no arguments exits with 1 (shows help)."""
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_subprocess_help():
    """card-search --help shows usage text and exits 0."""
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Search consulting cards" in result.stdout


def test_subprocess_list_flag():
    """card-search --list runs without error."""
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "--list"],
        capture_output=True,
        text=True,
    )
    # Either lists cards or exits 1 with "No cards found"
    assert result.returncode in (0, 1)


def test_subprocess_search_keyword():
    """card-search with a keyword runs without crashing."""
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "test"],
        capture_output=True,
        text=True,
    )
    # Returns 0 whether matches found or not
    assert result.returncode == 0


# ── main() via exec with mocked CARDS_DIR ─────────────────────────────


def test_main_list_with_cards(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with --list prints card titles."""
    _write_card(cards_dir, "alpha.md", "# Alpha Title\nContent\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "--list"])
    main()
    out = capsys.readouterr().out
    assert "alpha: Alpha Title" in out


def test_main_search_keyword(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with a keyword invokes search."""
    _write_card(cards_dir, "risk.md", "# Risk\nRisk assessment content\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "risk"])
    main()
    out = capsys.readouterr().out
    assert "1 card(s) found" in out


def test_main_search_full_flag(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with --full keyword shows full card content."""
    content = "# Full\nA\nB\nC\nD\nE\n"
    _write_card(cards_dir, "full.md", content)
    monkeypatch.setattr(sys, "argv", ["card-search", "--full", "full"])
    main()
    out = capsys.readouterr().out
    assert "A" in out
    assert "E" in out


def test_main_no_args_exits(cards_dir, patch_cards_dir, monkeypatch):
    """main() with no args exits with 1."""
    monkeypatch.setattr(sys, "argv", ["card-search"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
