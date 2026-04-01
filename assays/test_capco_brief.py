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

    def test_valid_four_word_name(self, cb):
        """Four words is the upper bound for acceptance."""
        assert cb["_is_person_name"]("Mary Jane Watson Smith") is True

    def test_single_word_rejected(self, cb):
        assert cb["_is_person_name"]("Terry") is False

    def test_five_words_rejected(self, cb):
        assert cb["_is_person_name"]("A B C D E") is False

    def test_empty_string_rejected(self, cb):
        assert cb["_is_person_name"]("") is False

    def test_single_char_words_rejected(self, cb):
        """Words <2 chars after stripping punctuation are rejected."""
        assert cb["_is_person_name"]("A B") is False

    def test_lowercase_rejected(self, cb):
        assert cb["_is_person_name"]("terry li") is False

    def test_mixed_case_rejected(self, cb):
        """Second word starting lowercase fails the title-case check."""
        assert cb["_is_person_name"]("John smith") is False

    def test_never_name_words_rejected(self, cb):
        assert cb["_is_person_name"]("Hong Kong") is False

    def test_never_name_word_capco(self, cb):
        assert cb["_is_person_name"]("Capco Institute") is False

    def test_never_name_word_bank(self, cb):
        assert cb["_is_person_name"]("Big Bank") is False

    def test_never_name_word_consulting(self, cb):
        assert cb["_is_person_name"]("Financial Consulting") is False

    def test_never_name_word_digital(self, cb):
        assert cb["_is_person_name"]("Smart Digital") is False

    def test_comma_suffix_handled(self, cb):
        """Names with commas like 'Dara Sosulski, PhD' should be handled."""
        assert cb["_is_person_name"]("Dara Sosulski, PhD") is True

    def test_numeric_characters_rejected(self, cb):
        assert cb["_is_person_name"]("John Smith3") is False

    def test_honorifics_accepted(self, cb):
        assert cb["_is_person_name"]("Dr Jane Smith") is True

    def test_honorific_mr(self, cb):
        assert cb["_is_person_name"]("Mr John Smith") is True

    def test_honorific_ms(self, cb):
        assert cb["_is_person_name"]("Ms Jane Doe") is True

    def test_surrounding_stars_stripped(self, cb):
        assert cb["_is_person_name"]("**Terry Li**") is True

    def test_trailing_punctuation_stripped(self, cb):
        """Trailing :.,; on words should be stripped before checking."""
        assert cb["_is_person_name"]("John Smith:") is True

    def test_non_alpha_word_rejected(self, cb):
        """Words containing digits should fail the isalpha check."""
        assert cb["_is_person_name"]("John S2") is False


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

    def test_pattern1_en_dash(self, cb, capsys):
        """En dash (–) should also work as separator."""
        _chromatin_file(cb, "Capco/People.md",
            "### Alice Johnson – Senior Partner\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Johnson" in out

    def test_pattern1_plain_hyphen(self, cb, capsys):
        """Plain ASCII hyphen should also work as separator."""
        _chromatin_file(cb, "Capco/People.md",
            "### Alice Johnson - Consultant\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Johnson" in out

    def test_pattern1_empty_role_filtered(self, cb, capsys):
        """Heading with dash but no role text should not produce entry."""
        _chromatin_file(cb, "Capco/People.md",
            "### Alice Johnson —\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_never_name_word_filtered(self, cb, capsys):
        """Names that are in _NEVER_NAME_WORDS should not appear."""
        _chromatin_file(cb, "Capco/People.md",
            "### Hong Kong — Director\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_pattern4_director_keyword(self, cb, capsys):
        """Pattern 4 with 'director' keyword in role."""
        _chromatin_file(cb, "Capco/Contacts.md",
            "Alice Johnson (Executive Director)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Johnson" in out

    def test_pattern4_head_keyword(self, cb, capsys):
        """Pattern 4 with 'head' keyword in role."""
        _chromatin_file(cb, "Capco/Contacts.md",
            "Bob Chen (Head of Data)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Bob Chen" in out

    def test_pattern4_no_matching_keyword(self, cb, capsys):
        """Pattern 4: name (role) but role lacks any keyword → filtered."""
        _chromatin_file(cb, "Capco/Contacts.md",
            "Alice Johnson (Software Engineer)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_long_name_truncated_in_table(self, cb, capsys):
        """Names >22 chars should be truncated with '..'."""
        _chromatin_file(cb, "Capco/People.md",
            "### Verylongfirstname Verylonglastname — Director\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert ".." in out

    def test_multiple_stakeholders_from_single_file(self, cb, capsys):
        """Multiple people in one file should all appear."""
        _chromatin_file(cb, "Capco/Team.md",
            "### Alice Johnson — Director\n### Bob Chen — Partner\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Johnson" in out
        assert "Bob Chen" in out
        assert "2 people extracted" in out


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
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out

    def test_internal_events_categorised(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_mock3"
        mock.write_text("#!/bin/sh\necho 'Team standup 09:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
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
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "total" in out

    def test_comment_lines_skipped(self, cb, capsys, tmp_path):
        """Lines starting with # should be ignored."""
        mock = tmp_path / "fasti_mock5"
        mock.write_text("#!/bin/sh\necho '# This is a comment'\necho 'HSBC meeting 10:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        # The comment line should not appear as an event
        assert "# This is a comment" not in out
        assert "HSBC meeting" in out

    def test_events_prefix_lines_skipped(self, cb, capsys, tmp_path):
        """Lines starting with 'Events' should be ignored."""
        mock = tmp_path / "fasti_mock6"
        mock.write_text("#!/bin/sh\necho 'Events for today'\necho 'Team standup 09:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Events for today" not in out

    def test_empty_lines_skipped(self, cb, capsys, tmp_path):
        """Empty lines should be ignored."""
        mock = tmp_path / "fasti_mock7"
        mock.write_text("#!/bin/sh\necho 'HSBC sync 10:00'\necho ''\necho '  '\necho 'Lunch 12:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "HSBC sync" in out
        assert "Lunch" in out

    def test_mixed_client_internal(self, cb, capsys, tmp_path):
        """Both client and internal sections should appear."""
        mock = tmp_path / "fasti_mock8"
        mock.write_text("#!/bin/sh\necho 'HSBC client meeting 10:00'\necho 'Team standup 09:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out
        assert "Internal" in out
        assert "total" in out

    def test_header_format(self, cb, capsys):
        cb["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "# Calendar — Next 5 Days" in out


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

    def test_empty_checklist_file(self, cb, capsys):
        """A file with no checklist items at all."""
        _pulse_file(cb, "capco-day1-notes-2026-03-15.md",
            "# Notes\n\nSome prose without any checkboxes.\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "All items checked off" in out

    def test_non_matching_files_ignored(self, cb, capsys):
        """Files not matching capco-day1-*.md should be ignored."""
        _pulse_file(cb, "other-checklist.md", "- [ ] Task\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No capco-day1-*.md files found" in out

    def test_summary_count(self, cb, capsys):
        """Footer should report correct count."""
        _pulse_file(cb, "capco-day1-stuff-2026-03-15.md",
            "- [ ] Item alpha\n- [ ] Item beta\n- [ ] Item gamma\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "3 unchecked items" in out


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

    def test_unknown_command_exits(self, cb):
        """An unknown subcommand should trigger argparse error and exit 2."""
        cb["sys"].argv = ["capco-brief", "nonexistent"]
        with pytest.raises(SystemExit) as exc_info:
            cb["main"]()
        assert exc_info.value.code == 2


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


# ── Additional edge cases ──────────────────────────────────────────────────


class TestIsPersonNameEdgeCases:
    def test_mrs_honorific(self, cb):
        assert cb["_is_person_name"]("Mrs Jane Smith") is True

    def test_hyphenated_word_rejected(self, cb):
        """Hyphenated words fail isalpha check."""
        assert cb["_is_person_name"]("John-Smith Director") is False

    def test_whitespace_only_rejected(self, cb):
        assert cb["_is_person_name"]("   ") is False

    def test_comma_name_too_short(self, cb):
        """'A, PhD' → name part 'A' is single word → rejected."""
        assert cb["_is_person_name"]("A, PhD") is False

    def test_surrounding_whitespace_stripped(self, cb):
        assert cb["_is_person_name"]("  Terry Li  ") is True

    def test_trailing_parenthesis_rejected(self, cb):
        """Parentheses make the word non-alpha."""
        assert cb["_is_person_name"]("John Smith)") is False

    def test_never_name_word_consultants(self, cb):
        assert cb["_is_person_name"]("Senior Consultants") is False

    def test_never_name_word_manager(self, cb):
        assert cb["_is_person_name"]("Hiring Manager") is False

    def test_never_name_word_sponsor(self, cb):
        assert cb["_is_person_name"]("Project Sponsor") is False

    def test_never_name_word_talent(self, cb):
        assert cb["_is_person_name"]("Global Talent") is False

    def test_honorific_with_single_name_rejected(self, cb):
        """'Dr' alone is only 1 word after split."""
        assert cb["_is_person_name"]("Dr") is False


class TestCapcoFilesEdgeCases:
    def test_non_md_ignored(self, cb):
        """Non-.md files in Capco/ should be ignored."""
        d = cb["CHROMATIN"] / "Capco"
        d.mkdir(parents=True, exist_ok=True)
        (d / "notes.txt").write_text("not markdown")
        assert cb["_capco_files"]() == []

    def test_hidden_file_ignored(self, cb):
        """Hidden files (starting with .) should not be globbed."""
        d = cb["CHROMATIN"] / "Capco"
        d.mkdir(parents=True, exist_ok=True)
        (d / ".hidden.md").write_text("hidden")
        # glob("*.md") does not match dotfiles by default
        assert cb["_capco_files"]() == []

    def test_nested_subdir_not_traversed(self, cb):
        """Only Capco/*.md is globbed, not Capco/sub/*.md."""
        sub = cb["CHROMATIN"] / "Capco" / "archive"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "old.md").write_text("old content")
        assert cb["_capco_files"]() == []


class TestStakeholdersEdgeCases:
    def test_pattern4_lead_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Jane Cooper (Delivery Lead)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Jane Cooper" in out

    def test_pattern4_officer_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Tom Baker (Chief Operating Officer)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Tom Baker" in out

    def test_pattern4_managing_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Sarah Connors (Managing Director)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Sarah Connors" in out

    def test_pattern4_executive_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Mike Hunt (Executive Partner)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Mike Hunt" in out

    def test_pattern4_practice_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Lisa Chen (Practice Lead)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Lisa Chen" in out

    def test_pattern4_governance_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "David Park (Governance Lead)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "David Park" in out

    def test_pattern4_data_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Anna Kim (Data Scientist)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Anna Kim" in out

    def test_pattern4_ai_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Robert Lin (AI Engineering Lead)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Robert Lin" in out

    def test_pattern4_hsbc_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Terry Li (HSBC Relationship Manager)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Terry Li" in out

    def test_pattern4_bank_keyword(self, cb, capsys):
        _chromatin_file(cb, "Capco/Contacts.md",
            "Alice Wang (Banking Analyst)\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Alice Wang" in out

    def test_role_truncation(self, cb, capsys):
        """Roles >60 chars should be truncated with '..'."""
        long_role = "A" * 70
        _chromatin_file(cb, "Capco/People.md",
            f"### Alice Johnson — {long_role}\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert ".." in out

    def test_source_column_shown(self, cb, capsys):
        _chromatin_file(cb, "Capco/Key People.md",
            "### Terry Li — Managing Director\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Key People" in out

    def test_pattern2_empty_role_column_filtered(self, cb, capsys):
        """Table row with empty role column should be filtered."""
        _chromatin_file(cb, "Capco/Team.md",
            "| **Alice Johnson** |  |\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No stakeholders found" in out

    def test_summary_file_count(self, cb, capsys):
        """Footer should report correct file count."""
        _chromatin_file(cb, "Capco/People.md",
            "### Alice Johnson — Partner\n")
        cb["cmd_stakeholders"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "1 files" in out


class TestCalendarEdgeCases:
    def test_bank_keyword_categorised_as_client(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_bank"
        mock.write_text("#!/bin/sh\necho 'Bank review meeting 14:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out
        assert "bank review" in out.lower()

    def test_hang_seng_keyword_categorised_as_client(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_hs"
        mock.write_text("#!/bin/sh\necho 'Hang Seng catchup 11:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out

    def test_secondment_keyword_categorised_as_client(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_sec"
        mock.write_text("#!/bin/sh\necho 'Secondment sync 16:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out

    def test_site_visit_keyword_categorised_as_client(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_sv"
        mock.write_text("#!/bin/sh\necho 'Site visit preparation 10:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out

    def test_aims_keyword_categorised_as_client(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_aims"
        mock.write_text("#!/bin/sh\necho 'AIMS quarterly review 09:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out

    def test_customer_keyword_categorised_as_client(self, cb, capsys, tmp_path):
        mock = tmp_path / "fasti_cust"
        mock.write_text("#!/bin/sh\necho 'Customer journey workshop 15:00'\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        assert "Client" in out

    def test_no_header_prefix_in_output(self, cb, capsys):
        """When no events, output should not have Client/Internal sections."""
        cb["cmd_calendar"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "## Client" not in out
        assert "## Internal" not in out

    def test_fasti_timeout_handled(self, cb, capsys, tmp_path):
        """A fasti that hangs should be caught by timeout."""
        mock = tmp_path / "fasti_slow"
        mock.write_text("#!/bin/sh\nsleep 30\n")
        import os
        os.chmod(str(mock), 0o755)
        saved = cb["FASTI"]
        cb["FASTI"] = mock
        try:
            cb["cmd_calendar"](argparse.Namespace())
            out = capsys.readouterr().out
        finally:
            cb["FASTI"] = saved
        # timeout → subprocess.SubprocessError caught → no events
        assert "No events found" in out


class TestChecklistEdgeCases:
    def test_bold_in_middle_of_item(self, cb, capsys):
        """Bold markers within the text should be stripped."""
        _pulse_file(cb, "capco-day1-notes-2026-03-15.md",
            "- [ ] Review **Section 2** and **Section 3** of the guide\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Review Section 2 and Section 3 of the guide" in out
        assert "**" not in out

    def test_file_with_only_checked_items(self, cb, capsys):
        """File with all items checked shows 'All items checked off'."""
        _pulse_file(cb, "capco-day1-onboard-2026-03-15.md",
            "- [x] Task A\n- [x] Task B\n- [x] Task C\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "All items checked off" in out
        assert "Task A" not in out

    def test_checklist_item_with_leading_spaces(self, cb, capsys):
        """Items with leading whitespace after '- [ ]' should still match."""
        _pulse_file(cb, "capco-day1-tasks-2026-03-15.md",
            "- [ ]   Indented task\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Indented task" in out

    def test_checked_item_with_x_uppercase(self, cb, capsys):
        """' - [X]' (uppercase X) should be treated as checked."""
        _pulse_file(cb, "capco-day1-tasks-2026-03-15.md",
            "- [X] Uppercase checked\n- [ ] Unchecked item\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "Unchecked item" in out
        # Uppercase X is not matched by regex r"^- \[ \]", so only 1 item
        assert "1 unchecked items" in out

    def test_no_md_extension_ignored(self, cb, capsys):
        """Files matching capco-day1-* but not .md should be ignored."""
        _pulse_file(cb, "capco-day1-notes.txt", "- [ ] Task\n")
        cb["cmd_checklist"](argparse.Namespace())
        out = capsys.readouterr().out
        assert "No capco-day1-*.md files found" in out
