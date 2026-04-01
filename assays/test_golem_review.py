from __future__ import annotations

"""Tests for golem-review — META-GOLEM review and requeue effector."""

import subprocess
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load():
    """Load golem-review by exec-ing its source."""
    source = open(str(Path.home() / "germline/effectors/golem-review")).read()
    ns: dict = {"__name__": "golem_review_test"}
    exec(source, ns)
    return ns


_mod = _load()

# Functions under test
parse_since = _mod["parse_since"]
parse_log_timestamp = _mod["parse_log_timestamp"]
scan_log = _mod["scan_log"]
get_recent_files = _mod["get_recent_files"]
run_pytest_on_files = _mod["run_pytest_on_files"]
check_consulting_content = _mod["check_consulting_content"]
_detect_section_keyword = _mod["_detect_section_keyword"]
_compute_quality_score = _mod["_compute_quality_score"]
_verdict_from_score = _mod["_verdict_from_score"]
diagnose_failure = _mod["diagnose_failure"]
read_log_tail = _mod["read_log_tail"]
count_pending_tasks = _mod["count_pending_tasks"]
find_untested_modules = _mod["find_untested_modules"]
generate_queue_tasks = _mod["generate_queue_tasks"]
append_tasks_to_queue = _mod["append_tasks_to_queue"]
write_fixed_tasks = _mod["write_fixed_tasks"]
generate_review = _mod["generate_review"]
run_review = _mod["run_review"]

# Save originals for restore
_ORIG = {
    "QUEUE_FILE": _mod["QUEUE_FILE"],
    "LOGFILE": _mod["LOGFILE"],
    "REVIEW_FILE": _mod["REVIEW_FILE"],
    "COPIA_DIR": _mod["COPIA_DIR"],
    "GERMLINE": _mod["GERMLINE"],
    "EFFECTORS_DIR": _mod["EFFECTORS_DIR"],
    "ASSAYS_DIR": _mod["ASSAYS_DIR"],
}


def _restore():
    for k, v in _ORIG.items():
        _mod[k] = v


def _recent_ts(minutes_ago: int = 0) -> str:
    """Return a timestamp string N minutes ago from now."""
    ts = datetime.now() - timedelta(minutes=minutes_ago)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


# ── parse_since ────────────────────────────────────────────────────────


class TestParseSince:
    def test_minutes(self):
        assert parse_since("30m") == timedelta(minutes=30)

    def test_hours(self):
        assert parse_since("2h") == timedelta(hours=2)

    def test_seconds(self):
        assert parse_since("60s") == timedelta(seconds=60)

    def test_days(self):
        assert parse_since("1d") == timedelta(days=1)

    def test_bare_number_is_minutes(self):
        assert parse_since("45") == timedelta(minutes=45)

    def test_invalid_returns_default(self):
        assert parse_since("abc") == timedelta(minutes=30)

    def test_whitespace_trimmed(self):
        assert parse_since("  15m  ") == timedelta(minutes=15)


# ── parse_log_timestamp ────────────────────────────────────────────────


class TestParseLogTimestamp:
    def test_valid(self):
        dt = parse_log_timestamp("2026-03-31 10:53:29")
        assert dt is not None
        assert dt.year == 2026 and dt.month == 3 and dt.day == 31

    def test_invalid(self):
        assert parse_log_timestamp("not-a-ts") is None

    def test_empty(self):
        assert parse_log_timestamp("") is None


# ── scan_log ───────────────────────────────────────────────────────────


class TestScanLog:
    def _make_log(self, tmp_path, lines):
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join(lines) + "\n")
        return log_path

    def test_completed_task_found(self, tmp_path):
        ts = _recent_ts(5)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] Starting: golem task1",
            f"[{ts}] Finished (60s, exit=0): golem task1...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["completed"]) == 1
        assert result["completed"][0][1] == "golem task1"
        assert len(result["failed"]) == 0

    def test_failed_task_found(self, tmp_path):
        ts = _recent_ts(2)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] FAILED (exit=1): golem task...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["failed"]) == 1
        assert len(result["completed"]) == 0

    def test_timeout_detected(self, tmp_path):
        ts = _recent_ts(1)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] TIMEOUT (1800s): golem slow-task...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["timeouts"]) == 1

    def test_old_entries_excluded(self, tmp_path):
        log_path = self._make_log(tmp_path, [
            "[2020-01-01 00:00:00] Finished (60s, exit=0): old task...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["completed"]) == 0

    def test_missing_log_file(self, tmp_path):
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = tmp_path / "nonexistent.log"
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert result["completed"] == []
        assert result["failed"] == []

    def test_mixed(self, tmp_path):
        log_path = self._make_log(tmp_path, [
            f"[{_recent_ts(10)}] Finished (10s, exit=0): task1",
            f"[{_recent_ts(9)}] FAILED (exit=1): task2",
            f"[{_recent_ts(8)}] Finished (5s, exit=0): task3",
            f"[{_recent_ts(7)}] TIMEOUT (1800s): task4",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["completed"]) == 2
        assert len(result["failed"]) == 1
        assert len(result["timeouts"]) == 1

    def test_empty_log(self, tmp_path):
        log_path = self._make_log(tmp_path, [])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert result["completed"] == []
        assert result["failed"] == []

    def test_finished_nonzero_exit_is_failed(self, tmp_path):
        ts = _recent_ts(3)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] Finished (30s, exit=2): golem bad-cmd...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["failed"]) == 1
        assert len(result["completed"]) == 0


# ── diagnose_failure ───────────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_import_error(self):
        r = diagnose_failure("golem task", "ModuleNotFoundError: foo")
        assert "import_error" in r

    def test_syntax_error(self):
        r = diagnose_failure("golem task", "SyntaxError: invalid")
        assert "syntax_error" in r

    def test_hardcoded_path(self):
        r = diagnose_failure("golem /Users/terry/ task", "")
        assert "path_issue" in r

    def test_timeout(self):
        r = diagnose_failure("golem task", "timeout after 1800s")
        assert "timeout" in r

    def test_permission_error(self):
        r = diagnose_failure("golem task", "PermissionError: denied")
        assert "permission_error" in r

    def test_exit_code_2(self):
        r = diagnose_failure("golem task exit=2", "")
        assert "command_error" in r

    def test_unknown(self):
        r = diagnose_failure("golem task", "something weird")
        assert "unknown" in r

    def test_assertion_error(self):
        r = diagnose_failure("golem task", "assert False")
        assert "assertion_error" in r


# ── get_recent_files ───────────────────────────────────────────────────


class TestGetRecentFiles:
    def test_returns_files(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 0 if "diff" in cmd else 1
            r.stdout = "assays/test_foo.py\neffectors/bar.py\n" if "diff" in cmd else ""
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = get_recent_files(5)
        assert "assays/test_foo.py" in result

    def test_git_failure(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 128
            r.stdout = ""
            r.stderr = "fatal"
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = get_recent_files()
        assert result == []


# ── run_pytest_on_files ────────────────────────────────────────────────


class TestRunPytestOnFiles:
    def test_passing(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 0
            r.stdout = "5 passed in 1.2s"
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = run_pytest_on_files(["assays/test_ex.py"])
        assert result["total_passed"] == 5

    def test_failing(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = "3 passed, 2 failed"
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = run_pytest_on_files(["assays/test_brk.py"])
        assert result["total_failed"] == 2

    def test_empty(self):
        result = run_pytest_on_files([])
        assert result["total_passed"] == 0

    def test_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("c", 1)):
            result = run_pytest_on_files(["assays/test_slow.py"])
        assert result["total_errors"] == 1


# ── check_consulting_content ───────────────────────────────────────────


class TestCheckConsultingContent:
    def test_enough_words(self, tmp_path):
        f = tmp_path / "deep.md"
        f.write_text(" ".join(["word"] * 250))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["deep.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is True

    def test_too_short(self, tmp_path):
        f = tmp_path / "thin.md"
        f.write_text("short")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["thin.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is False

    def test_missing(self, tmp_path):
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["nope.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["exists"] is False

    def test_well_structured(self, tmp_path):
        f = tmp_path / "good.md"
        body = ("This is the introduction paragraph with enough content "
                "to meet the word count requirement for a proper report. " * 15)
        f.write_text(textwrap.dedent(f"""\
            # Good Consulting Report

            {body}

            ## Analysis

            - Key finding one with detailed explanation
            - Key finding two with supporting evidence

            **Conclusion**: This is a well-structured document that has
            headings, paragraphs, lists, and bold text for proper structure.
        """))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["good.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is True
        assert r[0]["has_headings"] is True
        assert r[0]["has_paragraphs"] is True
        assert r[0]["has_structure_elements"] is True
        assert r[0]["structure_ok"] is True

    def test_no_headings_fails_structure(self, tmp_path):
        f = tmp_path / "flat.md"
        f.write_text(" ".join(["word"] * 250) + "\n\n" + " ".join(["word"] * 50))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["flat.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_headings"] is False
        assert r[0]["structure_ok"] is False

    def test_headings_but_no_content_fails(self, tmp_path):
        f = tmp_path / "skeleton.md"
        f.write_text("# Title\n\n## Section\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["skeleton.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_headings"] is True
        assert r[0]["has_paragraphs"] is False
        assert r[0]["has_structure_elements"] is False
        assert r[0]["structure_ok"] is False

    def test_headings_with_single_paragraph_no_extras(self, tmp_path):
        f = tmp_path / "minimal.md"
        f.write_text("# Title\n\nA single paragraph here.")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["minimal.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_headings"] is True
        assert r[0]["has_paragraphs"] is False
        assert r[0]["structure_ok"] is False

    def test_code_block_counts_as_structure(self, tmp_path):
        f = tmp_path / "code.md"
        f.write_text("# Title\n\n```\nsome code\n```\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["code.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_headings"] is True
        assert r[0]["has_structure_elements"] is True
        assert r[0]["structure_ok"] is True

    def test_bold_text_counts_as_structure(self, tmp_path):
        f = tmp_path / "bold.md"
        f.write_text("# Title\n\n**Important note** about something.\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["bold.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_structure_elements"] is True

    def test_table_counts_as_structure(self, tmp_path):
        f = tmp_path / "table.md"
        f.write_text("# Title\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["table.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_structure_elements"] is True

    def test_structure_fields_default_false_on_missing(self, tmp_path):
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["absent.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_headings"] is False
        assert r[0]["has_paragraphs"] is False
        assert r[0]["has_structure_elements"] is False
        assert r[0]["structure_ok"] is False
        assert r[0]["has_introduction"] is False
        assert r[0]["has_conclusion"] is False
        assert r[0]["quality_score"] == 0
        assert r[0]["verdict"] == "poor"

    def test_multiple_files(self, tmp_path):
        (tmp_path / "a.md").write_text("# A\n\n" + " ".join(["w"] * 250) + "\n\n- item\n")
        (tmp_path / "b.md").write_text("just a sentence")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["a.md", "b.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["structure_ok"] is True
        assert r[1]["structure_ok"] is False


# ── _detect_section_keyword ───────────────────────────────────────────


class TestDetectSectionKeyword:
    def test_introduction(self):
        lines = ["# Introduction", "", "Some text."]
        assert _detect_section_keyword(lines, ("introduction", "intro")) is True

    def test_case_insensitive(self):
        lines = ["## OVERVIEW OF FINDINGS"]
        assert _detect_section_keyword(lines, ("overview",)) is True

    def test_conclusion_variants(self):
        for heading in ["## Conclusion", "## Summary", "## Recommendations", "## Next Steps"]:
            assert _detect_section_keyword(
                [heading], ("conclusion", "summary", "recommendations", "next steps")
            ) is True

    def test_no_match(self):
        lines = ["# Methods", "## Results", "Some details."]
        assert _detect_section_keyword(lines, ("introduction", "intro")) is False

    def test_keyword_in_body_not_heading(self):
        lines = ["# Results", "The introduction of this study..."]
        assert _detect_section_keyword(lines, ("introduction",)) is False

    def test_empty_lines(self):
        assert _detect_section_keyword([], ("intro",)) is False


# ── _compute_quality_score ─────────────────────────────────────────────


class TestComputeQualityScore:
    def test_perfect_score(self):
        entry = {
            "word_count": 600, "has_headings": True, "has_paragraphs": True,
            "has_structure_elements": True, "has_introduction": True,
            "has_conclusion": True,
        }
        assert _compute_quality_score(entry) == 100

    def test_zero_score(self):
        entry = {"word_count": 0}
        assert _compute_quality_score(entry) == 0

    def test_word_count_partial(self):
        entry = {"word_count": 250, "has_headings": False, "has_paragraphs": False,
                 "has_structure_elements": False, "has_introduction": False,
                 "has_conclusion": False}
        score = _compute_quality_score(entry)
        assert 10 <= score <= 20  # ~15 from word count (250/500*30)

    def test_word_count_max_30(self):
        entry = {"word_count": 5000, "has_headings": False, "has_paragraphs": False,
                 "has_structure_elements": False, "has_introduction": False,
                 "has_conclusion": False}
        assert _compute_quality_score(entry) == 30

    def test_structure_only(self):
        entry = {"word_count": 0, "has_headings": True, "has_paragraphs": True,
                 "has_structure_elements": True, "has_introduction": False,
                 "has_conclusion": False}
        assert _compute_quality_score(entry) == 40

    def test_all_structure_no_words(self):
        entry = {"word_count": 0, "has_headings": True, "has_paragraphs": True,
                 "has_structure_elements": True, "has_introduction": True,
                 "has_conclusion": True}
        assert _compute_quality_score(entry) == 70


# ── _verdict_from_score ────────────────────────────────────────────────


class TestVerdictFromScore:
    def test_excellent(self):
        assert _verdict_from_score(80) == "excellent"
        assert _verdict_from_score(100) == "excellent"

    def test_good(self):
        assert _verdict_from_score(60) == "good"
        assert _verdict_from_score(79) == "good"

    def test_needs_work(self):
        assert _verdict_from_score(40) == "needs_work"
        assert _verdict_from_score(59) == "needs_work"

    def test_poor(self):
        assert _verdict_from_score(0) == "poor"
        assert _verdict_from_score(39) == "poor"


# ── check_consulting_content quality scoring ───────────────────────────


class TestCheckConsultingContentQuality:
    def test_excellent_document(self, tmp_path):
        f = tmp_path / "excellent.md"
        body = ("This is the introduction paragraph with enough content "
                "to meet the word count requirement for a proper report. " * 15)
        f.write_text(textwrap.dedent(f"""\
            # Report Title

            ## Introduction

            {body}

            ## Analysis

            - Key finding one with detailed explanation
            - Key finding two with supporting evidence

            **Important**: This is a critical insight.

            ## Conclusion

            This concludes our analysis with actionable takeaways.
        """))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["excellent.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is True
        assert r[0]["has_introduction"] is True
        assert r[0]["has_conclusion"] is True
        assert r[0]["quality_score"] >= 80
        assert r[0]["verdict"] == "excellent"

    def test_poor_document(self, tmp_path):
        f = tmp_path / "poor.md"
        f.write_text("Just a line.\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["poor.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is False
        assert r[0]["quality_score"] < 40
        assert r[0]["verdict"] == "poor"

    def test_introduction_detection(self, tmp_path):
        f = tmp_path / "intro.md"
        f.write_text("# Overview\n\n" + " ".join(["word"] * 250) + "\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["intro.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_introduction"] is True
        assert r[0]["has_conclusion"] is False

    def test_conclusion_detection(self, tmp_path):
        f = tmp_path / "concl.md"
        f.write_text("# Summary\n\n" + " ".join(["word"] * 250) + "\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["concl.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_introduction"] is False
        assert r[0]["has_conclusion"] is True

    def test_background_counts_as_intro(self, tmp_path):
        f = tmp_path / "bg.md"
        f.write_text("## Background\n\n" + " ".join(["word"] * 250) + "\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["bg.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_introduction"] is True

    def test_takeaways_counts_as_conclusion(self, tmp_path):
        f = tmp_path / "take.md"
        f.write_text("## Takeaways\n\n" + " ".join(["word"] * 250) + "\n")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["take.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["has_conclusion"] is True

    def test_good_document_score_range(self, tmp_path):
        f = tmp_path / "good.md"
        f.write_text(textwrap.dedent("""\
            # Report

            ## Intro

            """ + " ".join(["word"] * 300) + """

            ## Analysis

            - item one
            - item two

            ## Conclusion

            Final words here.
        """))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["good.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["quality_score"] >= 60
        assert r[0]["verdict"] in ("good", "excellent")


# ── read_log_tail ──────────────────────────────────────────────────────


class TestReadLogTail:
    def test_last_n(self, tmp_path):
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join([f"line {i}" for i in range(10)]))
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            tail = read_log_tail(3)
        finally:
            _mod["LOGFILE"] = orig
        assert "line 7" in tail
        assert "line 0" not in tail

    def test_missing(self, tmp_path):
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = tmp_path / "nope.log"
            tail = read_log_tail()
        finally:
            _mod["LOGFILE"] = orig
        assert tail == ""


# ── count_pending_tasks ────────────────────────────────────────────────


class TestCountPendingTasks:
    def _make_queue(self, tmp_path, content):
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_counts(self, tmp_path):
        qf = self._make_queue(tmp_path, (
            "- [ ] `golem \"a\"`\n"
            "- [!!] `golem \"b\"`\n"
            "- [x] `golem \"c\"`\n"
            "- [!] `golem \"d\"`\n"
            "- [ ] `golem \"e\"`\n"
        ))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert count_pending_tasks() == 3
        finally:
            _mod["QUEUE_FILE"] = orig

    def test_empty(self, tmp_path):
        qf = self._make_queue(tmp_path, "")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert count_pending_tasks() == 0
        finally:
            _mod["QUEUE_FILE"] = orig

    def test_missing(self, tmp_path):
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = tmp_path / "nope.md"
            assert count_pending_tasks() == 0
        finally:
            _mod["QUEUE_FILE"] = orig


# ── find_untested_modules ──────────────────────────────────────────────


class TestFindUntestedModules:
    def test_finds_untested(self, tmp_path):
        eff = tmp_path / "effectors"
        eff.mkdir()
        (eff / "foo-tool").write_text("#")
        (eff / "bar.py").write_text("#")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_foo_tool.py").write_text("#")
        orig_e = _mod["EFFECTORS_DIR"]
        orig_a = _mod["ASSAYS_DIR"]
        try:
            _mod["EFFECTORS_DIR"] = eff
            _mod["ASSAYS_DIR"] = assays
            r = find_untested_modules()
        finally:
            _mod["EFFECTORS_DIR"] = orig_e
            _mod["ASSAYS_DIR"] = orig_a
        assert "foo-tool" not in r
        assert "bar.py" in r

    def test_no_dir(self, tmp_path):
        orig = _mod["EFFECTORS_DIR"]
        try:
            _mod["EFFECTORS_DIR"] = tmp_path / "nope"
            assert find_untested_modules() == []
        finally:
            _mod["EFFECTORS_DIR"] = orig


# ── generate_queue_tasks ───────────────────────────────────────────────


class TestGenerateQueueTasks:
    def test_count(self):
        tasks = generate_queue_tasks(["a", "b"], 2)
        assert len(tasks) == 2

    def test_truncates(self):
        tasks = generate_queue_tasks(["a", "b", "c"], 2)
        assert len(tasks) == 2

    def test_providers_rotate(self):
        tasks = generate_queue_tasks(["a", "b", "c"], 3)
        providers = []
        for t in tasks:
            m = __import__("re").search(r"--provider (\w+)", t)
            if m:
                providers.append(m.group(1))
        assert len(set(providers)) >= 2

    def test_empty(self):
        assert generate_queue_tasks([], 50) == []


# ── append_tasks_to_queue ──────────────────────────────────────────────


class TestAppendTasksToQueue:
    def test_appends(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        orig_c = _mod["COPIA_DIR"]
        try:
            _mod["QUEUE_FILE"] = qf
            _mod["COPIA_DIR"] = tmp_path / "copia"
            added = append_tasks_to_queue(["- [ ] `golem \"new\"`"])
        finally:
            _mod["QUEUE_FILE"] = orig
            _mod["COPIA_DIR"] = orig_c
        assert added == 1
        assert "new" in qf.read_text()

    def test_empty(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert append_tasks_to_queue([]) == 0
        finally:
            _mod["QUEUE_FILE"] = orig


# ── write_fixed_tasks ──────────────────────────────────────────────────


class TestWriteFixedTasks:
    def test_writes(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            c = write_fixed_tasks([{"cmd": "golem t", "diagnosis": "path_issue: x"}])
        finally:
            _mod["QUEUE_FILE"] = orig
        assert c == 1
        assert "path_issue" in qf.read_text()

    def test_empty(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert write_fixed_tasks([]) == 0
        finally:
            _mod["QUEUE_FILE"] = orig


# ── generate_review ────────────────────────────────────────────────────


class TestGenerateReview:
    def test_basic(self):
        r = generate_review(
            activity={"completed": [(datetime(2026,3,31,14,0,0), "t1")], "failed": [], "timeouts": [], "start_time": None},
            recent_files=["assays/test_x.py"],
            test_results={"files": [("assays/test_x.py", 5, 0, 0)], "total_passed": 5, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[], pending_count=10,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "## Activity Summary" in r
        assert "5 passed" in r

    def test_with_failures(self):
        r = generate_review(
            activity={"completed": [], "failed": [(datetime.now(), "bad", "")], "timeouts": [(datetime.now(), "slow")], "start_time": None},
            recent_files=[], test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[{"cmd": "bad", "diagnosis": "timeout"}],
            pending_count=5, auto_requeue=True, queued_count=0, fixed_count=1,
        )
        assert "Failed Tasks" in r
        assert "1 fixed" in r

    def test_consulting_with_structure(self):
        r = generate_review(
            activity={"completed": [], "failed": [], "timeouts": [], "start_time": None},
            recent_files=[], test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[{
                "file": "loci/copia/report.md", "exists": True,
                "word_count": 350, "adequate": True,
                "has_headings": True, "has_paragraphs": True,
                "has_structure_elements": True, "structure_ok": True,
                "has_introduction": True, "has_conclusion": True,
                "quality_score": 100, "verdict": "excellent",
            }],
            failed_diagnoses=[], pending_count=5,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "OK|structured" in r
        assert "[HPSIC]" in r
        assert "score=100" in r
        assert "(excellent)" in r

    def test_consulting_unstructured(self):
        r = generate_review(
            activity={"completed": [], "failed": [], "timeouts": [], "start_time": None},
            recent_files=[], test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[{
                "file": "loci/copia/raw.md", "exists": True,
                "word_count": 50, "adequate": False,
                "has_headings": False, "has_paragraphs": False,
                "has_structure_elements": False, "structure_ok": False,
                "has_introduction": False, "has_conclusion": False,
                "quality_score": 3, "verdict": "poor",
            }],
            failed_diagnoses=[], pending_count=5,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "TOO SHORT|UNSTRUCTURED" in r
        assert "[_____]" in r
        assert "score=3" in r

    def test_empty(self):
        r = generate_review(
            {"completed": [], "failed": [], "timeouts": [], "start_time": None},
            [], {"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            [], [], 0, False, 0, 0,
        )
        assert "Golem Review" in r


# ── run_review integration ─────────────────────────────────────────────


def _setup_env(tmp_path):
    germline = tmp_path / "germline"
    germline.mkdir(parents=True)
    lp = tmp_path / "golem-daemon.log"
    lp.write_text("")
    cd = germline / "loci" / "copia"
    cd.mkdir(parents=True, exist_ok=True)
    rp = cd / "golem-review-latest.md"
    qd = germline / "loci"
    qd.mkdir(parents=True, exist_ok=True)
    qp = qd / "golem-queue.md"
    qp.write_text("## Pending\n\n## Done\n")
    ed = germline / "effectors"
    ed.mkdir()
    ad = germline / "assays"
    ad.mkdir()
    return {"GERMLINE": germline, "LOGFILE": lp, "REVIEW_FILE": rp, "COPIA_DIR": cd,
            "QUEUE_FILE": qp, "EFFECTORS_DIR": ed, "ASSAYS_DIR": ad}


class TestRunReview:
    def test_basic(self, tmp_path, capsys):
        env = _setup_env(tmp_path)
        orig = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v
            def mock_run(cmd, **kw):
                r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = ""
                return r
            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            for k, v in orig.items():
                _mod[k] = v
        assert rc == 0
        assert env["REVIEW_FILE"].exists()

    def test_with_task(self, tmp_path):
        env = _setup_env(tmp_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        env["LOGFILE"].write_text(f"[{now}] Finished (100s, exit=0): golem task A\n")
        orig = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v
            def mock_run(cmd, **kw):
                r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = ""
                return r
            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            for k, v in orig.items():
                _mod[k] = v
        assert rc == 0
        review_text = env["REVIEW_FILE"].read_text()
        assert "task A" in review_text

    def test_auto_requeue(self, tmp_path, capsys):
        env = _setup_env(tmp_path)
        for i in range(5):
            (env["EFFECTORS_DIR"] / f"mod-{i}").write_text("#")
        orig = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v
            def mock_run(cmd, **kw):
                r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = ""
                return r
            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=True, since=timedelta(minutes=5))
        finally:
            for k, v in orig.items():
                _mod[k] = v
        assert rc == 0
        q = env["QUEUE_FILE"].read_text()
        assert any(f"mod-{i}" in q for i in range(5))


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_scan_log_binary(self, tmp_path):
        lp = tmp_path / "golem-daemon.log"
        lp.write_bytes(b"\x00\x01\x02\xff")
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = lp
            r = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert isinstance(r, dict)

    def test_count_pending_unreadable(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("- [ ] `golem x`\n")
        q.chmod(0o000)
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = q
            assert count_pending_tasks() == 0
        finally:
            _mod["QUEUE_FILE"] = orig
            q.chmod(0o644)
