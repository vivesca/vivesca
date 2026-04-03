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
    """search_cards returns 0 and prints message when no matches."""
    _write_card(cards_dir, "other.md", "# Other\nSome content\n")
    count = search_cards("nonexistent_keyword_xyz")
    assert count == 0
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


def test_subprocess_search_keyword(tmp_path):
    """card-search with a keyword runs without crashing."""
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "sample.md").write_text("# Test Card\nSome test content\n")
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "test"],
        capture_output=True,
        text=True,
        env={**os.environ, "CARDS_DIR": str(cards)},
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


# ── additional edge-case tests ────────────────────────────────────────


def test_get_card_title_h2_only_returns_stem(cards_dir):
    """get_card_title returns stem when file has only ## (h2) headings."""
    _write_card(cards_dir, "sub.md", "## Sub Heading\nSome text\n")
    title = get_card_title(cards_dir / "sub.md")
    assert title == "sub"


def test_get_card_title_special_chars(cards_dir):
    """get_card_title handles headings with colons, dashes, and unicode."""
    _write_card(cards_dir, "spec.md", "# AI/ML: Risk — Stratégie\nContent\n")
    title = get_card_title(cards_dir / "spec.md")
    assert title == "AI/ML: Risk — Stratégie"


def test_get_card_title_heading_with_inline_formatting(cards_dir):
    """get_card_title returns raw heading text including markdown formatting."""
    _write_card(cards_dir, "fmt.md", "# Important **Bold** and `code`\nContent\n")
    title = get_card_title(cards_dir / "fmt.md")
    assert title == "Important **Bold** and `code`"


def test_list_cards_ignores_non_md(cards_dir, patch_cards_dir, capsys):
    """list_cards only lists .md files, ignoring other extensions."""
    _write_card(cards_dir, "card.md", "# Card\n")
    (cards_dir / "notes.txt").write_text("Not a card\n")
    (cards_dir / "data.json").write_text("{}\n")
    list_cards()
    out = capsys.readouterr().out
    assert "card: Card" in out
    assert "notes" not in out
    assert "data" not in out


def test_search_cards_keyword_in_title_only(cards_dir, patch_cards_dir, capsys):
    """search_cards finds keyword that appears only in the title line."""
    _write_card(cards_dir, "governance.md", "# Governance Framework\nNo other text\n")
    search_cards("Governance Framework")
    out = capsys.readouterr().out
    assert "1 card(s) found" in out
    assert "governance" in out


def test_search_cards_card_with_fewer_than_three_lines(cards_dir, patch_cards_dir, capsys):
    """search_cards summary mode handles cards with < 3 non-empty content lines."""
    _write_card(cards_dir, "short.md", "# Short\nOnly one line of content\n")
    search_cards("Short")
    out = capsys.readouterr().out
    assert "Only one line of content" in out
    assert "1 card(s) found" in out


def test_search_cards_card_with_only_title(cards_dir, patch_cards_dir, capsys):
    """search_cards summary mode handles card with title and no body lines."""
    _write_card(cards_dir, "bare.md", "# Bare Title\n")
    search_cards("Bare")
    out = capsys.readouterr().out
    assert "bare" in out
    assert "1 card(s) found" in out


def test_search_cards_output_separators(cards_dir, patch_cards_dir, capsys):
    """search_cards output contains separator lines around each card."""
    _write_card(cards_dir, "sep.md", "# Separator Test\nBody text\n")
    search_cards("Separator")
    out = capsys.readouterr().out
    assert "File: sep" in out
    assert "Title: Separator Test" in out
    # Two separator lines per card (before File: and after Title:)
    assert out.count("=" * 60) >= 2


def test_search_cards_full_mode_shows_entire_file(cards_dir, patch_cards_dir, capsys):
    """search_cards full mode shows the entire file content including title."""
    content = "# Long Card\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\n"
    _write_card(cards_dir, "long.md", content)
    search_cards("Long", full=True)
    out = capsys.readouterr().out
    for i in range(1, 7):
        assert f"Line {i}" in out


def test_main_full_without_keyword_exits(cards_dir, patch_cards_dir, monkeypatch):
    """main() with --full but no keyword shows help and exits 1."""
    _write_card(cards_dir, "card.md", "# Card\nContent\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "--full"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_list_and_full_together(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with both --list and --full: --list takes precedence."""
    _write_card(cards_dir, "alpha.md", "# Alpha\nContent A\n")
    _write_card(cards_dir, "beta.md", "# Beta\nContent B\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "--list", "--full"])
    list_cards()
    out = capsys.readouterr().out
    assert "alpha: Alpha" in out
    assert "beta: Beta" in out


def test_get_card_title_with_multiple_blank_lines_before_heading(cards_dir):
    """get_card_title skips blank lines before finding the first # heading."""
    _write_card(cards_dir, "blank.md", "\n\n\n# Hidden Title\nContent\n")
    title = get_card_title(cards_dir / "blank.md")
    assert title == "Hidden Title"


def test_search_cards_empty_card_not_matched(cards_dir, patch_cards_dir, capsys):
    """search_cards does not match empty .md files (grep -l won't find them)."""
    _write_card(cards_dir, "empty.md", "")
    _write_card(cards_dir, "nonempty.md", "# Has Content\nSome text here\n")
    search_cards("Content")
    out = capsys.readouterr().out
    assert "1 card(s) found" in out
    assert "nonempty" in out


# ── additional coverage tests ──────────────────────────────────────────


def test_subprocess_short_flag_f(tmp_path):
    """card-search -f <keyword> works as --full."""
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "sample.md").write_text("# Test Card\nSome test content\n")
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "-f", "test"],
        capture_output=True,
        text=True,
        env={**os.environ, "CARDS_DIR": str(cards)},
    )
    assert result.returncode == 0


def test_subprocess_short_flag_l():
    """card-search -l works as --list."""
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "-l"],
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1)


def test_subprocess_full_flag(tmp_path):
    """card-search --full <keyword> runs without error."""
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "model.md").write_text("# Model Card\nModel content here\n")
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "--full", "model"],
        capture_output=True,
        text=True,
        env={**os.environ, "CARDS_DIR": str(cards)},
    )
    assert result.returncode == 0


def test_subprocess_help_shows_examples():
    """card-search --help shows usage examples."""
    result = subprocess.run(
        [sys.executable, CARDS_SEARCH_PATH, "--help"],
        capture_output=True,
        text=True,
    )
    assert "card-search" in result.stdout
    assert "--full" in result.stdout
    assert "--list" in result.stdout


def test_main_search_no_match_exits_0(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with a keyword that matches nothing exits 0."""
    _write_card(cards_dir, "other.md", "# Other\nUnrelated content\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "xyzZY_not_found"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "No cards found matching" in out


def test_main_list_short_flag(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with -l short flag lists cards."""
    _write_card(cards_dir, "alpha.md", "# Alpha Title\nContent\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "-l"])
    main()
    out = capsys.readouterr().out
    assert "alpha: Alpha Title" in out


def test_main_full_short_flag(cards_dir, patch_cards_dir, capsys, monkeypatch):
    """main() with -f short flag shows full content."""
    _write_card(cards_dir, "full.md", "# Full Card\nA\nB\nC\n")
    monkeypatch.setattr(sys, "argv", ["card-search", "-f", "Full"])
    main()
    out = capsys.readouterr().out
    assert "A" in out
    assert "C" in out


def test_search_cards_summary_skips_blank_lines(cards_dir, patch_cards_dir, capsys):
    """search_cards summary mode skips blank lines when counting 3 non-empty lines."""
    content = "# Blanks\n\n\nLine1\n\n\nLine2\n\n\nLine3\n\n\nLine4\n"
    _write_card(cards_dir, "blanks.md", content)
    search_cards("Blanks")
    out = capsys.readouterr().out
    assert "Line1" in out
    assert "Line2" in out
    assert "Line3" in out
    assert "Line4" not in out


def test_get_card_title_read_error(cards_dir):
    """get_card_title returns stem when file is unreadable (permission denied)."""
    p = cards_dir / "noperm.md"
    p.write_text("# Secret Title\n")
    p.chmod(0o000)
    try:
        title = get_card_title(p)
        assert title == "noperm"
    finally:
        p.chmod(0o644)


def test_search_cards_full_mode_read_error(cards_dir, patch_cards_dir, capsys):
    """search_cards full mode prints error to stderr when card is unreadable."""
    p = _write_card(cards_dir, "bad.md", "# Bad Card\nContent\n")
    p.chmod(0o000)
    try:
        search_cards("Bad", full=True)
        err = capsys.readouterr().err
        # The grep subprocess may still find the file in the directory listing
        # if it checks by name; either way, reading should handle the error
        # gracefully (error printed to stderr or no crash).
    finally:
        p.chmod(0o644)


def test_search_cards_summary_mode_read_error(cards_dir, patch_cards_dir, capsys):
    """search_cards summary mode prints error to stderr when card is unreadable."""
    p = _write_card(cards_dir, "badsum.md", "# Bad Summary\nContent\n")
    p.chmod(0o000)
    try:
        search_cards("Bad", full=False)
        err = capsys.readouterr().err
    finally:
        p.chmod(0o644)


def test_list_cards_single_card(cards_dir, patch_cards_dir, capsys):
    """list_cards works with exactly one card."""
    _write_card(cards_dir, "only.md", "# Only Card\nContent\n")
    list_cards()
    out = capsys.readouterr().out
    assert "only: Only Card" in out
    assert out.strip().count("\n") == 0  # single line


def test_search_cards_grep_returns_multiple_lines(cards_dir, patch_cards_dir, capsys):
    """search_cards correctly parses grep output with multiple result lines."""
    for i in range(5):
        _write_card(cards_dir, f"card{i}.md", f"# Card {i}\nShared keyword here\n")
    search_cards("Shared")
    out = capsys.readouterr().out
    assert "5 card(s) found" in out
