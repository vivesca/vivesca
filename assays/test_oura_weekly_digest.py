from __future__ import annotations
"""Tests for oura-weekly-digest — weekly health data markdown generator."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "oura-weekly-digest.py"


def _load_module() -> dict:
    """Load the effector via exec (effectors are scripts, not importable modules)."""
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "oura_weekly_digest_test"}
    exec(source, ns)
    return ns


_mod = _load_module()
strip_ansi = _mod["strip_ansi"]
parse_trend_table = _mod["parse_trend_table"]
compute_avg = _mod["compute_avg"]
trend_arrow = _mod["trend_arrow"]
format_section = _mod["format_section"]
run = _mod["run"]
main = _mod["main"]


# ── strip_ansi tests ────────────────────────────────────────────────────


def test_strip_ansi_removes_color_codes():
    """strip_ansi strips common ANSI escape sequences."""
    text = "\x1b[32mOK\x1b[0m \x1b[1;31mFAIL\x1b[0m"
    assert strip_ansi(text) == "OK FAIL"


def test_strip_ansi_no_codes():
    """strip_ansi returns plain text unchanged."""
    assert strip_ansi("hello world") == "hello world"


def test_strip_ansi_empty():
    """strip_ansi handles empty string."""
    assert strip_ansi("") == ""


# ── parse_trend_table tests ─────────────────────────────────────────────


def test_parse_trend_table_basic():
    """parse_trend_table parses a well-formed trend output."""
    raw = """Date  Sleep  Readiness  Activity
Mon Mar 24  78  85  62
Tue Mar 25  82  90  70
Wed Mar 26  --  88  65"""
    rows = parse_trend_table(raw)
    assert len(rows) == 3
    assert rows[0]["date"] == "Mon Mar 24"
    assert rows[0]["sleep"] == "78"
    assert rows[0]["readiness"] == "85"
    assert rows[0]["activity"] == "62"
    assert rows[1]["sleep"] == "82"
    assert rows[2]["sleep"] == "--"
    assert rows[2]["readiness"] == "88"


def test_parse_trend_table_skips_header_and_average():
    """parse_trend_table skips 'Date' header and 'Average' summary lines."""
    raw = """Date  Sleep  Readiness  Activity
Average  80  87  66
Mon Mar 24  78  85  62"""
    rows = parse_trend_table(raw)
    assert len(rows) == 1
    assert rows[0]["date"] == "Mon Mar 24"


def test_parse_trend_table_empty():
    """parse_trend_table returns empty list for empty string."""
    assert parse_trend_table("") == []


def test_parse_trend_table_short_lines():
    """parse_trend_table skips lines with fewer than 2 parts."""
    raw = "Mon\n\nTue Mar 25  82  90  70"
    rows = parse_trend_table(raw)
    assert len(rows) == 1
    assert rows[0]["date"] == "Tue Mar 25"


def test_parse_trend_table_missing_scores():
    """parse_trend_table handles rows with fewer than 3 scores."""
    raw = "Mon Mar 24  78  85"
    rows = parse_trend_table(raw)
    assert len(rows) == 1
    assert rows[0]["sleep"] == "78"
    assert rows[0]["readiness"] == "85"
    assert rows[0]["activity"] == "--"


# ── compute_avg tests ───────────────────────────────────────────────────


def test_compute_avg_basic():
    """compute_avg computes integer average of numeric strings."""
    assert compute_avg(["80", "82", "78"]) == "80"


def test_compute_avg_rounds():
    """compute_avg rounds to nearest integer."""
    assert compute_avg(["80", "81"]) == "80"  # 80.5 -> 80 (banker's rounding, but round(80.5)=80)


def test_compute_avg_skips_dashes():
    """compute_avg ignores '--' and '' entries."""
    assert compute_avg(["80", "--", "82", ""]) == "81"


def test_compute_avg_all_missing():
    """compute_avg returns '--' when no valid numbers."""
    assert compute_avg(["--", "", "--"]) == "--"


def test_compute_avg_empty_list():
    """compute_avg returns '--' for empty list."""
    assert compute_avg([]) == "--"


def test_compute_avg_single_value():
    """compute_avg works with a single value."""
    assert compute_avg(["95"]) == "95"


# ── trend_arrow tests ───────────────────────────────────────────────────


def test_trend_arrow_up():
    """trend_arrow detects upward trend (recent 3 much higher than older)."""
    values = ["70", "71", "72", "85", "86", "87"]
    assert trend_arrow(values) == " (trending up)"


def test_trend_arrow_down():
    """trend_arrow detects downward trend."""
    values = ["90", "89", "88", "75", "74", "73"]
    assert trend_arrow(values) == " (trending down)"


def test_trend_arrow_stable():
    """trend_arrow reports stable when difference < 3."""
    values = ["80", "81", "79", "80", "82", "81"]
    assert trend_arrow(values) == " (stable)"


def test_trend_arrow_too_few():
    """trend_arrow returns empty string with fewer than 3 numeric values."""
    assert trend_arrow(["80", "82"]) == ""
    assert trend_arrow(["80"]) == ""


def test_trend_arrow_just_three():
    """trend_arrow returns empty string with exactly 3 values (no older baseline)."""
    assert trend_arrow(["80", "82", "78"]) == ""


def test_trend_arrow_skips_dashes():
    """trend_arrow ignores '--' values."""
    values = ["--", "70", "71", "72", "85", "86"]
    # recent 3: [72, 85, 86] avg=81, older: [70, 71] avg=70.5, diff=10.5 -> up
    assert trend_arrow(values) == " (trending up)"


def test_trend_arrow_empty():
    """trend_arrow returns empty string for empty list."""
    assert trend_arrow([]) == ""


# ── format_section tests ────────────────────────────────────────────────


def test_format_section_basic():
    """format_section formats each non-empty line as a bullet."""
    raw = "Total sleep: 7h 30m\nEfficiency: 92%\nDeep sleep: 1h 20m"
    result = format_section("Sleep", raw)
    assert result == "- Total sleep: 7h 30m\n- Efficiency: 92%\n- Deep sleep: 1h 20m"


def test_format_section_empty():
    """format_section returns '*No data*' for empty input."""
    assert format_section("Sleep", "") == "*No data*"


def test_format_section_whitespace_only():
    """format_section returns empty string for whitespace-only input (lines stripped to nothing)."""
    assert format_section("Sleep", "   \n\n  ") == ""


def test_format_section_strips_lines():
    """format_section strips leading/trailing whitespace from lines."""
    raw = "  hello  \n  world  "
    result = format_section("Test", raw)
    assert result == "- hello\n- world"


# ── run() tests ─────────────────────────────────────────────────────────


def test_run_substitutes_oura_path():
    """run() replaces 'oura' with the full binary path."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="output\n", stderr="")
        result = run(["oura", "trend", "--days", "7"])
        called_cmd = mock_run.call_args[0][0]
        # First arg should be the full path, not "oura"
        assert called_cmd[0] != "oura"
        assert called_cmd[0].endswith("oura")
        assert called_cmd[1:] == ["trend", "--days", "7"]
        assert result == "output"


def test_run_passes_through_other_commands():
    """run() leaves non-oura commands unchanged."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="ok", stderr="")
        run(["echo", "hello"])
        assert mock_run.call_args[0][0] == ["echo", "hello"]


def test_run_strips_ansi():
    """run() strips ANSI codes from stdout."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="\x1b[32mgreen\x1b[0m\n", stderr="")
        assert run(["test"]) == "green"


# ── main() integration test ─────────────────────────────────────────────


def _make_subprocess_mock(trend_output="Mon Mar 24  78  85  62\nTue Mar 25  82  90  70\nWed Mar 26  80  88  65\nThu Mar 27  77  82  60\nFri Mar 28  83  91  72\nSat Mar 29  79  87  68\nSun Mar 30  81  89  71"):
    """Create a mock subprocess.run that returns oura CLI outputs."""
    call_count = {"n": 0}

    def _mock_run(cmd, **kwargs):
        call_count["n"] += 1
        n = call_count["n"]
        if "trend" in cmd:
            out = trend_output
        elif "sleep" in cmd[0] if isinstance(cmd[0], str) else False:
            out = "Total sleep: 7h 30m\nEfficiency: 92%"
        else:
            # 2=sleep, 3=readiness, 4=activity, 5=hrv
            outputs = {
                2: "Total sleep: 7h 30m\nEfficiency: 92%",
                3: "Score: 85\nTemperature: 36.5",
                4: "Steps: 8500\nCalories: 2200",
                5: "Average HRV: 45ms\nMax HRV: 65ms",
            }
            out = outputs.get(n, "data")
        return MagicMock(stdout=out + "\n", stderr="")

    return _mock_run


def test_main_writes_note_file(tmp_path, monkeypatch):
    """main() writes a markdown note to ~/notes/Daily/."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["oura-weekly-digest.py"])

    # We need to re-exec with the patched home since OURA_BIN uses Path.home()
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "test_oura_main"}
    exec(source, ns)

    mock_run = _make_subprocess_mock()

    with patch("subprocess.run", side_effect=mock_run):
        ns["main"]()

    # Check file was written
    notes_dir = tmp_path / "notes" / "Daily"
    files = list(notes_dir.glob("Oura Weekly - *.md"))
    assert len(files) == 1

    content = files[0].read_text()
    # Verify structure
    assert "# Oura Weekly Digest" in content
    assert "## 7-Day Scores" in content
    assert "| Date | Sleep | Readiness | Activity |" in content
    assert "**Average**" in content
    assert "## Yesterday's Detail" in content
    assert "### Sleep" in content
    assert "### Readiness" in content
    assert "### HRV & Recovery" in content
    assert "### Activity" in content


def test_main_outputs_summary(tmp_path, monkeypatch, capsys):
    """main() prints a one-line summary to stdout."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["oura-weekly-digest.py"])

    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "test_oura_main"}
    exec(source, ns)

    mock_run = _make_subprocess_mock()

    with patch("subprocess.run", side_effect=mock_run):
        ns["main"]()

    captured = capsys.readouterr()
    assert "Oura 7d:" in captured.out
    assert "sleep avg" in captured.out
    assert "readiness avg" in captured.out
    assert "activity avg" in captured.out
    assert "saved" in captured.out


def test_main_atomic_write(tmp_path, monkeypatch):
    """main() writes via temp file then renames (atomic write)."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sys.argv", ["oura-weekly-digest.py"])

    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "test_oura_main"}
    exec(source, ns)

    mock_run = _make_subprocess_mock()
    replaces = []

    original_replace = Path.replace

    def tracking_replace(self, target):
        replaces.append((str(self), str(target)))
        return original_replace(self, target)

    with patch("subprocess.run", side_effect=mock_run), \
         patch.object(Path, "replace", tracking_replace):
        ns["main"]()

    # Should have renamed .md.tmp -> .md
    assert any(".md.tmp" in src and ".md" in dst and ".tmp" not in dst
               for src, dst in replaces)
