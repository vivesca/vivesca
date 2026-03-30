from __future__ import annotations

import re
from unittest.mock import patch

from metabolon.organelles import engram


def test_make_line_context_returns_neighboring_lines():
    match_line, before_lines, after_lines = engram._make_line_context(
        "alpha\nbeta match\ngamma\ndelta",
        match_start=7,
        context_lines=1,
    )

    assert match_line == "beta match"
    assert before_lines == ["alpha"]
    assert after_lines == ["gamma"]


def test_highlight_matches_wraps_ansi_sequences():
    regex = re.compile("match", re.IGNORECASE)

    highlighted = engram._highlight_matches("beta match gamma", regex, color=True)

    assert "\033[1;31mmatch\033[0m" in highlighted


def test_print_search_renders_context_block(capsys):
    regex = re.compile("match", re.IGNORECASE)
    matches = [
        engram.TraceFragment(
            date="2026-03-31",
            time_str="09:30",
            timestamp_ms=1,
            session="abc12345",
            role="claude",
            snippet="beta match gamma",
            tool="Claude",
            match_line="beta match gamma",
            context_before=["alpha"],
            context_after=["delta"],
        )
    ]

    with patch.object(engram, "_color_enabled", return_value=False):
        engram._print_search(
            matches,
            regex,
            "match",
            days=7,
            deep=True,
            role_filter=None,
            session_filter=None,
            context_lines=1,
        )

    output = capsys.readouterr().out
    assert "context=1" in output
    assert "alpha" in output
    assert "> beta match gamma" in output
    assert "delta" in output


def test_cli_help_includes_context_flag(capsys):
    with patch("sys.argv", ["engram", "search", "--help"]):
        try:
            engram._cli()
        except SystemExit as exc:
            assert exc.code == 0

    output = capsys.readouterr().out
    assert "--context N" in output
    assert "Show N lines of context before and after each match" in output
