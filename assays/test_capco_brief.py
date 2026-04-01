from __future__ import annotations

"""Tests for effectors/capco-brief — quick-reference briefings for Capco onboarding.

Capco-brief is a script — loaded via exec(), never imported.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pytest

CAPCO_BRIEF_PATH = Path(__file__).resolve().parents[1] / "effectors" / "capco-brief"


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest.fixture()
def cb(tmp_path):
    """Load capco-brief via exec, redirecting CHROMATIN/PULSE/FASTI to tmp_path."""
    chromatin = tmp_path / "chromatin"
    chromatin.mkdir()
    pulse = tmp_path / "pulse"
    pulse.mkdir()
    fasti = tmp_path / "fasti_mock"
    fasti.write_text("#!/bin/sh\nexit 0\n")

    ns: dict = {
        "__name__": "test_capco_brief",
        "__file__": str(CAPCO_BRIEF_PATH),
    }
    source = CAPCO_BRIEF_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    ns["CHROMATIN"] = chromatin
    ns["PULSE"] = pulse
    ns["FASTI"] = fasti
    return ns


def _chromatin_file(cb: dict, name: str, content: str) -> Path:
    """Write a file under CHROMATIN."""
    p = cb["CHROMATIN"] / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _pulse_file(cb: dict, name: str, content: str) -> Path:
    """Write a file under PULSE."""
    p = cb["PULSE"] / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ── File basics ────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert CAPCO_BRIEF_PATH.exists()

    def test_shebang(self):
        first = CAPCO_BRIEF_PATH.read_text().split("\n")[0]
        assert first.startswith("#!")

    def test_has_docstring(self):
        content = CAPCO_BRIEF_PATH.read_text()
        assert "capco-brief" in content


# ── _read ──────────────────────────────────────────────────────────────────


class TestRead:
    def test_read_existing_file(self, cb, tmp_path):
        f = tmp_path / "hello.md"
        f.write_text("hello world", encoding="utf-8")
        assert cb["_read"](f) == "hello world"

    def test_read_missing_file_returns_empty(self, cb, tmp_path):
        assert cb["_read"](tmp_path / "nope.md") == ""


# ── _is_person_name ───────────────────────────────────────────────────────


class TestIsPersonName:
    def test_valid_two_word_name(self, cb):
        assert cb["_is_person_name"]("Terry Li") is True

    def test_valid_three_word_name(self, cb):
        assert cb["_is_person_name"]("Mary Jane Watson") is True

    def test_single_word_rejected(self, cb):
        assert cb["_is_person_name"]("Terry") is False

    def test_five_words_rejected(self, cb):
        assert cb["_is_person_name"]("A B C D E") is False

    def test_lowercase_rejected(self, cb):
        assert cb["_is_person_name"]("terry li") is False

    def test_never_name_words_rejected(self, cb):
        assert cb["_is_person_name"]("Hong Kong") is False

    def test_never_name_word_capco(self, cb):
        assert cb["_is_person_name"]("Capco Institute") is False

    def test_never_name_word_bank(self, cb):
        assert cb["_is_person_name"]("Big Bank") is False

    def test_comma_suffix_handled(self, cb):
        """Names with commas like 'Dara Sosulski, PhD' should be handled."""
        assert cb["_is_person_name"]("Dara Sosulski, PhD") is True

    def test_numeric_characters_rejected(self, cb):
        assert cb["_is_person_name"]("John Smith3") is False

    def test_honorifics_accepted(self, cb):
        assert cb["_is_person_name"]("Dr Jane Smith") is True

    def test_surrounding_stars_stripped(self, cb):
        assert cb["_is_person_name"]("**Terry Li**") is True


# ── _capco_files ──────────────────────────────────────────────────────────


class TestCapcoFiles:
    def test_empty_chromatin(self, cb):
        assert cb["_capco_files"]() == []

    def test_finds_transition_file(self, cb):
        _chromatin_file(cb, "Capco Transition.md", "# Transition")
        files = cb["_capco_files"]()
        assert len(files) == 1
        assert files[0].name == "Capco Transition.md"

    def test_finds_capco_glob_files(self, cb):
        _chromatin_file(cb, "Capco Notes.md", "notes")
        files = cb["_capco_files"]()
        assert any(f.name == "Capco Notes.md" for f in files)

    def test_finds_capco_subdir(self, cb):
        _chromatin_file(cb, "Capco/People.md", "# People")
        files = cb["_capco_files"]()
        assert any(f.name == "People.md" for f in files)

    def test_transition_first(self, cb):
        _chromatin_file(cb, "Capco Notes.md", "notes")
        _chromatin_file(cb, "Capco Transition.md", "# Transition")
        files = cb["_capco_files"]()
        assert files[0].name == "Capco Transition.md"

    def test_no_duplicates(self, cb):
        _chromatin_file(cb, "Capco Transition.md", "# T")
        files = cb["_capco_files"]()
        names = [f.name for f in files]
        assert names.count("Capco Transition.md") == 1


# ── cmd_stakeholders ──────────────────────────────────────────────────────


class TestStakeholders:
    def test_no_files_outputs_nothing(self, cb, capsys):
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_pattern1_heading_dash(self, cb, capsys):
        _chromatin_file(cb, "Capco/Key People.md",
            "### Terry Li — Managing Director\nSome bio text")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Terry Li" in out
        assert "Managing Director" in out

    def test_pattern2_table_bold(self, cb, capsys):
        _chromatin_file(cb, "Capco/Team.md",
            "| **Alice Johnson** | Senior Consultant |\n| **Bob Chen** | Tech Lead |")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Johnson" in out
        assert "Bob Chen" in out

    def test_pattern2_short_role_filtered(self, cb, capsys):
        """Roles <=5 chars should be filtered out."""
        _chromatin_file(cb, "Capco/Team.md",
            "| **Alice Johnson** | Lead |")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_pattern3_label_parens(self, cb, capsys):
        _chromatin_file(cb, "Capco Transition.md",
            "- **Manager:** Terry Li (Delivery Lead)")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Terry Li" in out

    def test_pattern4_capco_role(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Alice Johnson (Capco / Senior Consultant)")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Johnson" in out

    def test_deduplication(self, cb, capsys):
        """Same person in multiple files should appear only once."""
        _chromatin_file(cb, "Capco/A.md", "### Terry Li — Director\n")
        _chromatin_file(cb, "Capco/B.md", "### Terry Li — Director Extra\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert out.count("Terry Li") == 1

    def test_table_format(self, cb, capsys):
        _chromatin_file(cb, "Capco/People.md",
            "### Terry Li — Managing Director\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "# Capco Stakeholders" in out
        assert "|" in out

    def test_summary_line(self, cb, capsys):
        _chromatin_file(cb, "Capco/People.md",
            "### Alice Johnson — Partner\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "1 people extracted" in out


# ── cmd_calendar ──────────────────────────────────────────────────────────


class TestCalendar:
    def test_no_events(self, cb, capsys):
        # fasti mock exits 0 with no output
        cb["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Calendar" in out
        assert "No events found" in out

    def test_client_events_categorised(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_mock2"
        mock.write_text("#!/bin/sh\necho 'HSBC catchup 10:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        ns2 = dict(cb)
        ns2["FASTI"] = mock
        ns2["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Client" in out

    def test_internal_events_categorised(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_mock3"
        mock.write_text("#!/bin/sh\necho 'Team standup 09:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        ns2 = dict(cb)
        ns2["FASTI"] = mock
        ns2["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Internal" in out

    def test_fasti_unavailable(self, cb, capsys):
        cb["FASTI"] = Path("/nonexistent/fasti")
        cb["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No events found" in out

    def test_summary_line(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_mock4"
        mock.write_text("#!/bin/sh\necho 'HSBC sync 10:00'\necho 'Lunch with team 12:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        ns2 = dict(cb)
        ns2["FASTI"] = mock
        ns2["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "total" in out


# ── cmd_checklist ─────────────────────────────────────────────────────────


class TestChecklist:
    def test_no_files(self, cb, capsys):
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No capco-day1-*.md files found" in out

    def test_unchecked_items(self, cb, capsys):
        _pulse_file(cb, "capco-day1-onboarding-2026-03-15.md",
            "# Day 1\n\n- [x] Done item\n- [ ] Bring laptop\n- [ ] Get badge\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Bring laptop" in out
        assert "Get badge" in out
        assert "Done item" not in out

    def test_all_checked(self, cb, capsys):
        _pulse_file(cb, "capco-day1-dress-2026-03-15.md",
            "- [x] Item one\n- [x] Item two\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "All items checked off" in out

    def test_multiple_files(self, cb, capsys):
        _pulse_file(cb, "capco-day1-transport-2026-03-15.md",
            "- [ ] Check MTR route\n")
        _pulse_file(cb, "capco-day1-benefits-2026-03-15.md",
            "- [ ] Sign up insurance\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Check MTR route" in out
        assert "Sign up insurance" in out
        assert "2 unchecked items" in out

    def test_bold_stripped_from_items(self, cb, capsys):
        _pulse_file(cb, "capco-day1-tasks-2026-03-15.md",
            "- [ ] **Review** the onboarding docs\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Review the onboarding docs" in out
        # bold markers should be stripped
        assert "****" not in out

    def test_header_format(self, cb, capsys):
        _pulse_file(cb, "capco-day1-tasks-2026-03-15.md",
            "- [ ] Do something\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "# Capco Day 1 — Unchecked Items" in out


# ── main ──────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_command_exits_1(self, cb):
        cb["sys"].argv = ["capco-brief"]
        with pytest.raises(SystemExit) as exc_info:
            cb["main"]()
        assert exc_info.value.code == 1

    def test_help_exits_0(self, cb):
        cb["sys"].argv = ["capco-brief", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            cb["main"]()
        assert exc_info.value.code == 0

    def test_stakeholders_command(self, cb, capsys):
        cb["sys"].argv = ["capco-brief", "stakeholders"]
        cb["main"]()
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_calendar_command(self, cb, capsys):
        cb["sys"].argv = ["capco-brief", "calendar"]
        cb["main"]()
        out = capsys.readouterr().out
        assert "Calendar" in out

    def test_checklist_command(self, cb, capsys):
        cb["sys"].argv = ["capco-brief", "checklist"]
        cb["main"]()
        out = capsys.readouterr().out
        assert "capco-day1" in out.lower() or "Capco" in out


# ── CLI subprocess ────────────────────────────────────────────────────────


class TestCLI:
    def test_runs_without_error(self):
        result = subprocess.run(
            [sys.executable, str(CAPCO_BRIEF_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "capco-brief" in result.stdout

    def test_no_command_exits_1(self):
        result = subprocess.run(
            [sys.executable, str(CAPCO_BRIEF_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1
