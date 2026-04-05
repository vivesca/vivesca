from __future__ import annotations

"""Tests for oura-weekly-digest effector.

Effectors are scripts — loaded via exec(open(path).read(), ns), never imported.
All function calls use dict-style access: ns["func"]().
"""

import subprocess
import sys
import types
from datetime import date
from pathlib import Path
from unittest.mock import patch

EFFECTORS_DIR = Path(__file__).resolve().parent.parent / "effectors"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_script(name: str) -> dict:
    """Load a Python effector into a namespace dict."""
    path = EFFECTORS_DIR / name
    if not path.exists() and not path.name.endswith(".py"):
        path = path.with_suffix(".py")
    assert path.exists(), f"Effector not found: {path}"
    mod_name = f"_test_oura_weekly_{name.replace('-', '_')}"
    mod = types.ModuleType(mod_name)
    mod.__file__ = str(path)
    old_mod = sys.modules.get(mod_name)
    sys.modules[mod_name] = mod
    try:
        exec(path.read_text(), mod.__dict__)
    except Exception:
        sys.modules.pop(mod_name, None)
        if old_mod is not None:
            sys.modules[mod_name] = old_mod
        raise
    return mod.__dict__


class ns_proxy:
    """Proxy that wraps a dict so ns.func() works via dict access."""

    def __init__(self, d: dict):
        self.__dict__["_d"] = d

    def __getattr__(self, name):
        try:
            return self._d[name]
        except KeyError as exc:
            raise AttributeError(f"namespace has no {name!r}") from exc

    def __setattr__(self, name, value):
        self._d[name] = value

    def __delattr__(self, name):
        self._d.pop(name, None)


def _load(name: str) -> ns_proxy:
    return ns_proxy(_load_script(name))


# ===================================================================
# strip_ansi
# ===================================================================


class TestStripAnsi:
    def test_removes_color_codes(self):
        ns = _load("oura-weekly-digest")
        text = "\x1b[32mOK\x1b[0m \x1b[1;33mwarning\x1b[0m"
        assert ns.strip_ansi(text) == "OK warning"

    def test_no_ansi_passthrough(self):
        ns = _load("oura-weekly-digest")
        assert ns.strip_ansi("hello world") == "hello world"

    def test_empty_string(self):
        ns = _load("oura-weekly-digest")
        assert ns.strip_ansi("") == ""

    def test_complex_ansi(self):
        ns = _load("oura-weekly-digest")
        text = "\x1b[38;5;196mred\x1b[0m"
        assert ns.strip_ansi(text) == "red"


# ===================================================================
# parse_trend_table
# ===================================================================


class TestParseTrendTable:
    def test_basic_rows(self):
        ns = _load("oura-weekly-digest")
        raw = (
            "Date              Sleep  Readiness  Activity\n"
            "Mon Mar 24  85  90  78\n"
            "Tue Mar 25  88  92  80\n"
            "Wed Mar 26  90  88  82\n"
        )
        rows = ns.parse_trend_table(raw)
        assert len(rows) == 3
        assert rows[0] == {
            "date": "Mon Mar 24",
            "sleep": "85",
            "readiness": "90",
            "activity": "78",
        }
        assert rows[2]["sleep"] == "90"

    def test_skips_header_and_average(self):
        ns = _load("oura-weekly-digest")
        raw = (
            "Date              Sleep  Readiness  Activity\n"
            "Average  87  90  80\n"
            "Mon Mar 24  85  90  78\n"
        )
        rows = ns.parse_trend_table(raw)
        assert len(rows) == 1
        assert rows[0]["date"] == "Mon Mar 24"

    def test_dashes_for_missing(self):
        ns = _load("oura-weekly-digest")
        raw = "Mon Mar 24  --  90  --\n"
        rows = ns.parse_trend_table(raw)
        assert len(rows) == 1
        assert rows[0]["sleep"] == "--"
        assert rows[0]["readiness"] == "90"
        assert rows[0]["activity"] == "--"

    def test_empty_input(self):
        ns = _load("oura-weekly-digest")
        assert ns.parse_trend_table("") == []

    def test_skips_short_lines(self):
        ns = _load("oura-weekly-digest")
        raw = "Mon\n\nTue Mar 25  88  92  80\n"
        rows = ns.parse_trend_table(raw)
        assert len(rows) == 1


# ===================================================================
# compute_avg
# ===================================================================


class TestComputeAvg:
    def test_normal_values(self):
        ns = _load("oura-weekly-digest")
        assert ns.compute_avg(["80", "85", "90"]) == "85"

    def test_rounds_correctly(self):
        ns = _load("oura-weekly-digest")
        # (80 + 90) / 2 = 85.0
        assert ns.compute_avg(["80", "90"]) == "85"

    def test_rounds_half(self):
        ns = _load("oura-weekly-digest")
        # (80 + 91) / 2 = 85.5 -> 86
        assert ns.compute_avg(["80", "91"]) == "86"

    def test_all_dashes(self):
        ns = _load("oura-weekly-digest")
        assert ns.compute_avg(["--", "--"]) == "--"

    def test_mixed_dashes(self):
        ns = _load("oura-weekly-digest")
        # only "80" and "90" count -> avg 85
        assert ns.compute_avg(["--", "80", "--", "90"]) == "85"

    def test_empty_list(self):
        ns = _load("oura-weekly-digest")
        assert ns.compute_avg([]) == "--"

    def test_single_value(self):
        ns = _load("oura-weekly-digest")
        assert ns.compute_avg(["75"]) == "75"


# ===================================================================
# trend_arrow
# ===================================================================


class TestTrendArrow:
    def test_trending_up(self):
        ns = _load("oura-weekly-digest")
        # recent [90,91,92] avg=91, older [80,81,82,83] avg=81.5, diff=9.5 >= 3
        vals = ["80", "81", "82", "83", "90", "91", "92"]
        assert ns.trend_arrow(vals) == " (trending up)"

    def test_trending_down(self):
        ns = _load("oura-weekly-digest")
        # recent [70,71,72] avg=71, older [85,86,87,88] avg=86.5, diff=-15.5 <= -3
        vals = ["85", "86", "87", "88", "70", "71", "72"]
        assert ns.trend_arrow(vals) == " (trending down)"

    def test_stable(self):
        ns = _load("oura-weekly-digest")
        # recent [83,84,85] avg=84, older [82,83,84,85] avg=83.5, diff=0.5
        vals = ["82", "83", "84", "85", "83", "84", "85"]
        assert ns.trend_arrow(vals) == " (stable)"

    def test_too_few_values(self):
        ns = _load("oura-weekly-digest")
        assert ns.trend_arrow(["80", "85"]) == ""

    def test_exactly_three_no_older(self):
        ns = _load("oura-weekly-digest")
        assert ns.trend_arrow(["80", "85", "90"]) == ""

    def test_all_dashes_returns_empty(self):
        ns = _load("oura-weekly-digest")
        assert ns.trend_arrow(["--", "--", "--", "--", "--"]) == ""


# ===================================================================
# format_section
# ===================================================================


class TestFormatSection:
    def test_normal_text(self):
        ns = _load("oura-weekly-digest")
        raw = "Total sleep: 7h 30m\nDeep sleep: 1h 20m"
        result = ns.format_section("Sleep", raw)
        assert result == "- Total sleep: 7h 30m\n- Deep sleep: 1h 20m"

    def test_empty_returns_no_data(self):
        ns = _load("oura-weekly-digest")
        assert ns.format_section("Sleep", "") == "*No data*"

    def test_whitespace_only_returns_empty(self):
        ns = _load("oura-weekly-digest")
        # whitespace-only lines are stripped and filtered out -> empty join
        assert ns.format_section("Sleep", "  \n  \n") == ""

    def test_single_line(self):
        ns = _load("oura-weekly-digest")
        assert ns.format_section("HRV", "Average HRV: 45ms") == "- Average HRV: 45ms"


# ===================================================================
# run (subprocess mock)
# ===================================================================


class TestRun:
    def test_replaces_oura_binary(self):
        ns = _load("oura-weekly-digest")
        oura_path = str(Path.home() / "code" / "oura-cli" / "target" / "release" / "oura")

        def fake_run(cmd, **kwargs):
            assert cmd[0] == oura_path
            assert cmd[1:] == ["trend", "--days", "7"]
            return subprocess.CompletedProcess(cmd, 0, stdout="output", stderr="")

        with patch("subprocess.run", fake_run):
            result = ns.run(["oura", "trend", "--days", "7"])
        assert result == "output"

    def test_strips_ansi_from_output(self):
        ns = _load("oura-weekly-digest")

        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], 0, stdout="\x1b[32mhello\x1b[0m", stderr=""
            ),
        ):
            result = ns.run(["some_cmd"])
        assert result == "hello"

    def test_full_path_passthrough(self):
        ns = _load("oura-weekly-digest")

        def fake_run(cmd, **kwargs):
            assert cmd[0] == "/usr/bin/echo"
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with patch("subprocess.run", fake_run):
            result = ns.run(["/usr/bin/echo", "hi"])
        assert result == "ok"


# ===================================================================
# main (integration with mocks)
# ===================================================================


class TestMain:
    @staticmethod
    def _mock_run_outputs(trend_data=None):
        """Return a mock subprocess.run that returns predetermined oura outputs."""
        if trend_data is None:
            trend_data = (
                "Date              Sleep  Readiness  Activity\n"
                "Mon Mar 24  85  90  78\n"
                "Tue Mar 25  88  92  80\n"
                "Wed Mar 26  90  88  82\n"
                "Thu Mar 27  87  85  79\n"
                "Fri Mar 28  82  88  81\n"
                "Sat Mar 29  89  91  83\n"
                "Sun Mar 30  86  87  77\n"
            )

        def fake_run(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "trend" in cmd_str:
                stdout = trend_data
            elif "sleep" in cmd_str:
                stdout = "Sleep score: 85\nDeep: 1h"
            elif "readiness" in cmd_str:
                stdout = "Readiness: 88"
            elif "hrv" in cmd_str:
                stdout = "HRV avg: 42ms"
            elif "activity" in cmd_str:
                stdout = "Steps: 8000"
            else:
                stdout = ""
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

        return fake_run

    def test_main_creates_note_file(self, tmp_path, monkeypatch):
        ns = _load("oura-weekly-digest")
        notes_dir = tmp_path / "notes" / "Daily"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(sys, "argv", ["oura-weekly-digest"])
        today = date.today()
        expected_path = notes_dir / f"Oura Weekly - {today.strftime('%Y-%m-%d')}.md"

        with patch("subprocess.run", self._mock_run_outputs()):
            ns.main()

        assert expected_path.exists()
        content = expected_path.read_text()
        # Check markdown structure
        assert "# Oura Weekly Digest" in content
        assert "## 7-Day Scores" in content
        assert "| Date | Sleep | Readiness | Activity |" in content
        assert "**Average**" in content
        assert "## Yesterday's Detail" in content
        assert "### Sleep" in content
        assert "### Readiness" in content
        assert "### HRV & Recovery" in content
        assert "### Activity" in content
        assert "tags: [oura, health, weekly]" in content

    def test_main_prints_summary(self, tmp_path, monkeypatch, capsys):
        ns = _load("oura-weekly-digest")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(sys, "argv", ["oura-weekly-digest"])

        with patch("subprocess.run", self._mock_run_outputs()):
            ns.main()

        captured = capsys.readouterr()
        assert "Oura 7d:" in captured.out
        assert "sleep avg" in captured.out
        assert "readiness avg" in captured.out
        assert "activity avg" in captured.out

    def test_main_table_rows(self, tmp_path, monkeypatch):
        ns = _load("oura-weekly-digest")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(sys, "argv", ["oura-weekly-digest"])

        with patch("subprocess.run", self._mock_run_outputs()):
            ns.main()

        today = date.today()
        note_path = tmp_path / "notes" / "Daily" / f"Oura Weekly - {today.strftime('%Y-%m-%d')}.md"
        content = note_path.read_text()
        # Should have 7 data rows
        for d in [
            "Mon Mar 24",
            "Tue Mar 25",
            "Wed Mar 26",
            "Thu Mar 27",
            "Fri Mar 28",
            "Sat Mar 29",
            "Sun Mar 30",
        ]:
            assert d in content

    def test_main_averages(self, tmp_path, monkeypatch):
        ns = _load("oura-weekly-digest")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(sys, "argv", ["oura-weekly-digest"])

        with patch("subprocess.run", self._mock_run_outputs()):
            ns.main()

        today = date.today()
        note_path = tmp_path / "notes" / "Daily" / f"Oura Weekly - {today.strftime('%Y-%m-%d')}.md"
        content = note_path.read_text()
        # Averages: sleep=(85+88+90+87+82+89+86)/7=86.71->87
        # readiness=(90+92+88+85+88+91+87)/7=88.71->89
        # activity=(78+80+82+79+81+83+77)/7=80
        assert "**87**" in content
        assert "**89**" in content
        assert "**80**" in content

    def test_main_empty_trend(self, tmp_path, monkeypatch, capsys):
        ns = _load("oura-weekly-digest")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(sys, "argv", ["oura-weekly-digest"])

        with patch("subprocess.run", self._mock_run_outputs(trend_data="")):
            ns.main()

        captured = capsys.readouterr()
        assert "sleep avg --" in captured.out
