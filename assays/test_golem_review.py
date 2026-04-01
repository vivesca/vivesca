from __future__ import annotations

import tempfile
from pathlib import Path, PurePosixPath

# Load the effector script
TEST_GERMLINE = Path(__file__).parent.parent
GOLEM_REVIEW = TEST_GERMLINE / "effectors" / "golem-review"
exec(open(GOLEM_REVIEW).read(), globals())
MAC_HOME_PREFIX = f"{PurePosixPath('/', 'Users', 'terry')}/"


def test_parse_since():
    assert parse_since("30s") == timedelta(seconds=30)
    assert parse_since("1h") == timedelta(hours=1)
    assert parse_since("2d") == timedelta(days=2)
    assert parse_since("45") == timedelta(minutes=45)
    assert parse_since("invalid") == timedelta(minutes=30)
    assert parse_since(None) == timedelta(minutes=30)


def test_parse_log_timestamp():
    assert parse_log_timestamp("2026-03-31 14:00:00") is not None
    assert parse_log_timestamp("invalid") is None
    assert parse_log_timestamp(None) is None


def test_check_consulting_content_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            (tmp_path / "loci").mkdir(parents=True, exist_ok=True)
            result = check_consulting_content(["non_existent.md"])
            assert len(result) == 1
            assert result[0]["exists"] is False
            assert result[0]["adequate"] is False
            assert result[0]["quality_score"] == 0
            assert result[0]["verdict"] == "poor"
        finally:
            globals()["GERMLINE"] = original_germline


def test_check_consulting_content_short():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        short_file = copia_dir / "short.md"
        short_file.write_text("This is short.")

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/short.md"])
            assert len(result) == 1
            assert result[0]["exists"] is True
            assert result[0]["word_count"] < 200
            assert result[0]["adequate"] is False
        finally:
            globals()["GERMLINE"] = original_germline


# ── Good content fixture — enough words to pass >200 check ──────────────

_GOOD_CONTENT = """\
# Introduction

This is a test consulting document that is designed to have enough words to
pass all quality checks. We need more than two hundred words, proper headings,
multiple paragraphs, and structural elements like lists and bold text.

The purpose of this document is to validate that the golem-review effector
correctly identifies well-structured consulting content. It should receive a
high quality score and an excellent or good verdict when evaluated.

We are now adding additional sentences to ensure the word count exceeds the
minimum threshold of two hundred words. This paragraph alone should contribute
a significant number of words to the total count.

## Analysis

Here are some key observations about the system under review:

- **Performance**: The system handles concurrent requests efficiently.
- **Reliability**: Uptime has exceeded ninety nine percent this quarter.
- **Scalability**: Horizontal scaling was demonstrated during load testing.

Additional analysis reveals that the caching layer reduces backend load by
approximately sixty percent during peak hours. This is a significant
improvement over the previous architecture.

## Conclusion

This concludes our test document. It has headings, paragraphs, structure
elements, and plenty of words to exceed the minimum threshold. The quality
checks should all pass, and the verdict should reflect the thorough structure.
"""


def test_check_consulting_content_good():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        good_file = copia_dir / "good.md"
        good_file.write_text(_GOOD_CONTENT)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/good.md"])
            assert len(result) == 1
            r = result[0]
            assert r["exists"] is True
            assert r["word_count"] > 200
            assert r["adequate"] is True
            assert r["has_headings"] is True
            assert r["structure_ok"] is True
            assert r["has_introduction"] is True
            assert r["has_conclusion"] is True
            assert r["section_count"] >= 3
            assert r["broken_sections"] == 0
            assert r["min_sections_ok"] is True
            assert r["quality_score"] > 0
            assert r["verdict"] in ("excellent", "good")
        finally:
            globals()["GERMLINE"] = original_germline


def test_check_consulting_content_headings_only():
    """Headings with no body text: broken sections, not min_sections_ok."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "headings_only.md"
        f.write_text("# Introduction\n\n## Analysis\n\n## Conclusion\n")

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/headings_only.md"])
            r = result[0]
            assert r["exists"] is True
            assert r["has_headings"] is True
            assert r["section_count"] == 3
            assert r["broken_sections"] == 3
            assert r["min_sections_ok"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_check_consulting_content_no_structure():
    """Body text but no headings or structure elements."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "no_structure.md"
        # Generate >200 words of plain text
        words = "word " * 250
        f.write_text(words)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/no_structure.md"])
            r = result[0]
            assert r["exists"] is True
            assert r["word_count"] > 200
            assert r["adequate"] is True
            assert r["has_headings"] is False
            assert r["has_introduction"] is False
            assert r["has_conclusion"] is False
            assert r["structure_ok"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_check_consulting_content_boundary():
    """Exactly 200 words is NOT adequate (must be >200)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "boundary.md"
        f.write_text("word " * 200)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/boundary.md"])
            assert result[0]["word_count"] == 200
            assert result[0]["adequate"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_check_consulting_content_multiple_files():
    """Check multiple files at once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        (copia_dir / "a.md").write_text("short")
        (copia_dir / "b.md").write_text(_GOOD_CONTENT)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content([
                "loci/copia/a.md",
                "loci/copia/b.md",
                "loci/copia/missing.md",
            ])
            assert len(result) == 3
            assert result[0]["adequate"] is False
            assert result[1]["adequate"] is True
            assert result[2]["exists"] is False
        finally:
            globals()["GERMLINE"] = original_germline


# ── Unit tests for internal helpers ─────────────────────────────────────


def test_detect_section_keyword():
    lines = ["# Introduction", "", "## Analysis", "", "# Summary"]
    assert _detect_section_keyword(lines, ("introduction",)) is True
    assert _detect_section_keyword(lines, ("summary",)) is True
    assert _detect_section_keyword(lines, ("conclusion",)) is False
    assert _detect_section_keyword([], ("anything",)) is False


def test_compute_quality_score():
    # Minimal entry
    assert _compute_quality_score({}) == 0
    assert _compute_quality_score({"word_count": 0}) == 0

    # Full marks
    entry = {
        "word_count": 600,
        "has_headings": True,
        "has_paragraphs": True,
        "has_structure_elements": True,
        "has_introduction": True,
        "has_conclusion": True,
        "min_sections_ok": True,
        "section_count": 5,
        "broken_sections": 0,
        "has_proper_heading_hierarchy": True,
        "has_filler_content": False,
    }
    score = _compute_quality_score(entry)
    assert score >= 80

    # Broken sections penalty
    entry_broken = dict(entry, broken_sections=3)
    score_broken = _compute_quality_score(entry_broken)
    assert score_broken < score


def test_verdict_from_score():
    assert _verdict_from_score(90) == "excellent"
    assert _verdict_from_score(80) == "excellent"
    assert _verdict_from_score(79) == "good"
    assert _verdict_from_score(60) == "good"
    assert _verdict_from_score(59) == "needs_work"
    assert _verdict_from_score(40) == "needs_work"
    assert _verdict_from_score(39) == "poor"
    assert _verdict_from_score(0) == "poor"


def test_count_sections():
    lines = [
        "# Title",
        "",
        "Some body text here.",
        "",
        "## Section Two",
        "",
        "More body text.",
        "",
        "## Section Three",
    ]
    total, broken = _count_sections(lines)
    assert total == 3
    assert broken == 1  # Section Three has no body

    # No headings
    assert _count_sections(["just text", "", "more text"]) == (0, 0)


# ── Other functions ─────────────────────────────────────────────────────


def test_diagnose_failure():
    assert diagnose_failure("cmd", "ModuleNotFoundError") == "import_error"
    assert diagnose_failure("cmd", "SyntaxError") == "syntax_error"
    assert diagnose_failure("cmd", MAC_HOME_PREFIX) == "path_issue"
    assert diagnose_failure("cmd", "timeout") == "timeout"
    assert diagnose_failure("cmd", "Permission denied") == "permission_error"
    assert diagnose_failure("cmd", "exit=2") == "command_error"
    assert diagnose_failure("cmd", "assert False") == "assertion_error"
    assert diagnose_failure("cmd", "unknown error") == "unknown"


def test_count_pending_tasks():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        qfile = tmp_path / "golem-queue.md"
        original_queue = globals()["QUEUE_FILE"]
        try:
            globals()["QUEUE_FILE"] = qfile
            assert count_pending_tasks() == 0

            qfile.write_text(
                "## Pending\n"
                "- [ ] task one\n"
                "- [!!] urgent task\n"
                "- [x] done task\n"
                "- [!] failed task\n"
                "## Done\n"
            )
            assert count_pending_tasks() == 2
        finally:
            globals()["QUEUE_FILE"] = original_queue


def test_generate_queue_tasks():
    tasks = generate_queue_tasks(["my-effector"], 3)
    assert len(tasks) == 1
    assert "my_effector" in tasks[0]
    assert "golem --provider" in tasks[0]

    # Empty input
    assert generate_queue_tasks([], 5) == []

    # Rotation: 5 providers, 3 modules → uses first 3 providers
    tasks = generate_queue_tasks(["a", "b", "c"], 3)
    assert len(tasks) == 3
    assert "infini" in tasks[0]
    assert "zhipu" in tasks[1]


def test_append_tasks_to_queue():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        qfile = tmp_path / "golem-queue.md"
        original_queue = globals()["QUEUE_FILE"]
        try:
            globals()["QUEUE_FILE"] = qfile
            # No file yet — creates it
            added = append_tasks_to_queue(["- [ ] new task"])
            assert added == 1
            content = qfile.read_text()
            assert "new task" in content
            assert "## Done" in content

            # Append more
            added = append_tasks_to_queue(["- [ ] another task"])
            assert added == 1

            # Empty input
            assert append_tasks_to_queue([]) == 0
        finally:
            globals()["QUEUE_FILE"] = original_queue


def test_generate_review():
    activity = {
        "completed": [(datetime(2026, 4, 1, 12, 0), "golem task A")],
        "failed": [(datetime(2026, 4, 1, 12, 5), "golem task B", "")],
        "timeouts": [],
    }
    review = generate_review(
        activity=activity,
        recent_files=["assays/test_foo.py", "loci/copia/doc.md"],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=[{
            "file": "loci/copia/doc.md", "exists": True, "word_count": 300,
            "adequate": True, "has_headings": True, "has_paragraphs": True,
            "has_structure_elements": False, "structure_ok": True,
            "has_introduction": True, "has_conclusion": True,
            "section_count": 4, "broken_sections": 0, "min_sections_ok": True,
            "has_proper_heading_hierarchy": True,
            "avg_paragraph_word_count": 30.0,
            "has_filler_content": False, "overall_quality_pass": True,
            "quality_score": 75, "verdict": "good",
        }],
        failed_diagnoses=[{"cmd": "golem task B", "diagnosis": "syntax_error"}],
        pending_count=10,
        auto_requeue=True,
        queued_count=2,
        fixed_count=1,
    )
    assert "Activity Summary" in review
    assert "Completed tasks: 1" in review
    assert "Failed Tasks" in review
    assert "Consulting Content" in review
    assert "Failure Diagnoses" in review
    assert "Auto-Requeue Actions" in review
    assert "syntax_error" in review
    assert "secs=4" in review
    assert "queued_count" not in review  # raw param name not in output


def test_main_help(capsys):
    ret = main()  # no --help → runs review but GERMLINE is real; just test --help
    # Test --help specifically
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["golem-review", "--help"]
        ret = main()
        captured = capsys.readouterr()
        assert "golem-review" in captured.out
        assert ret == 0
    finally:
        sys.argv = old_argv


# ── New quality-check tests ────────────────────────────────────────────


def test_check_heading_hierarchy_good():
    """Sequential heading levels: H1 → H2 → H3."""
    lines = ["# Title", "", "## Section", "", "### Subsection", "", "Text."]
    assert _check_heading_hierarchy(lines) is True


def test_check_heading_hierarchy_jump():
    """H1 → H4 is a jump, should fail."""
    lines = ["# Title", "", "#### Deep section", "", "Text."]
    assert _check_heading_hierarchy(lines) is False


def test_check_heading_hierarchy_single_level():
    """All H2 headings is fine (no jumps)."""
    lines = ["## A", "", "## B", "", "## C"]
    assert _check_heading_hierarchy(lines) is True


def test_check_heading_hierarchy_empty():
    assert _check_heading_hierarchy([]) is True
    assert _check_heading_hierarchy(["plain text"]) is True


def test_check_heading_hierarchy_backtracking():
    """H3 → H2 is allowed (going back up)."""
    lines = ["# H1", "", "## H2", "", "### H3", "", "## H2 again"]
    assert _check_heading_hierarchy(lines) is True


def test_check_filler_content_repetitive():
    """Same sentence repeated many times."""
    text = ". ".join(["This is a filler sentence"] * 10)
    assert _check_filler_content(text) is True


def test_check_filler_content_good():
    """Diverse, meaningful text."""
    text = (
        "The system architecture uses microservices. "
        "Each service handles a specific domain. "
        "Communication happens via message queues. "
        "The database layer uses PostgreSQL for persistence. "
        "Caching is handled by Redis instances."
    )
    assert _check_filler_content(text) is False


def test_check_filler_content_short_sentences():
    """Mostly very short sentences (<5 words) counts as filler."""
    text = "Yes. No. Maybe. So. Done. Go. Stop. Wait. Try. Run."
    assert _check_filler_content(text) is True


def test_check_filler_content_empty():
    assert _check_filler_content("") is False
    assert _check_filler_content("Short.") is False


def test_compute_paragraph_stats():
    """Average word count per paragraph block."""
    lines = [
        "First paragraph with several words in it.",
        "",
        "Second paragraph also has multiple words.",
        "",
        "Third.",
    ]
    avg = _compute_paragraph_stats(lines)
    assert avg > 0
    # First para: 7 words, Second: 6 words, Third: 1 word → avg ~4.67
    assert 3.0 < avg < 6.0


def test_compute_paragraph_stats_empty():
    assert _compute_paragraph_stats([]) == 0.0
    assert _compute_paragraph_stats(["", "", ""]) == 0.0


def test_compute_paragraph_stats_with_headings():
    """Headings should not count as paragraphs."""
    lines = [
        "# Title",
        "",
        "Body text with some words.",
        "",
        "## Section",
        "",
        "More body text here now.",
    ]
    avg = _compute_paragraph_stats(lines)
    # Two paragraphs: 5 words and 5 words → avg 5.0
    assert avg == 5.0


def test_consulting_overall_quality_pass():
    """Good content gets overall_quality_pass=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "good.md"
        f.write_text(_GOOD_CONTENT)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/good.md"])
            r = result[0]
            assert r["overall_quality_pass"] is True
            assert r["has_filler_content"] is False
            assert r["has_proper_heading_hierarchy"] is True
            assert r["avg_paragraph_word_count"] > 0
        finally:
            globals()["GERMLINE"] = original_germline


def test_consulting_overall_quality_fail_no_words():
    """Short content fails overall quality pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "short.md"
        f.write_text("# Intro\n\nShort text only.")

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/short.md"])
            assert result[0]["overall_quality_pass"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_consulting_overall_quality_fail_bad_hierarchy():
    """Bad heading hierarchy causes overall quality fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "bad_hier.md"
        # >200 words but with heading jump
        body = "# Title\n\n" + "Word " * 100 + "\n\n#### Jumped section\n\n" + "More " * 100 + "\n"
        f.write_text(body)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/bad_hier.md"])
            r = result[0]
            assert r["has_proper_heading_hierarchy"] is False
            assert r["overall_quality_pass"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_consulting_filler_detected():
    """Repetitive filler text should be flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "filler.md"
        # >200 words but repetitive
        filler = "# Analysis\n\n" + "This is a filler sentence. " * 40
        f.write_text(filler)

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/filler.md"])
            r = result[0]
            assert r["has_filler_content"] is True
            assert r["overall_quality_pass"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_consulting_content_code_only():
    """File with only code blocks: no paragraphs, no headings → unstructured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        f = copia_dir / "code_only.md"
        f.write_text("```\n" + "print('hello')\n" * 80 + "```\n")

        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["loci/copia/code_only.md"])
            r = result[0]
            assert r["has_headings"] is False
            assert r["structure_ok"] is False
            assert r["overall_quality_pass"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_consulting_new_fields_on_missing_file():
    """Missing file should have sensible defaults for new fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        original_germline = globals()["GERMLINE"]
        try:
            globals()["GERMLINE"] = tmp_path
            result = check_consulting_content(["nonexistent.md"])
            r = result[0]
            assert r["has_proper_heading_hierarchy"] is True
            assert r["avg_paragraph_word_count"] == 0.0
            assert r["has_filler_content"] is False
            assert r["overall_quality_pass"] is False
        finally:
            globals()["GERMLINE"] = original_germline


def test_consulting_new_fields_in_generate_review():
    """generate_review renders the new fields correctly."""
    review = generate_review(
        activity={"completed": [], "failed": [], "timeouts": []},
        recent_files=[],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=[{
            "file": "doc.md", "exists": True, "word_count": 300,
            "adequate": True, "has_headings": True, "has_paragraphs": True,
            "has_structure_elements": True, "structure_ok": True,
            "has_introduction": True, "has_conclusion": True,
            "section_count": 3, "broken_sections": 0, "min_sections_ok": True,
            "has_proper_heading_hierarchy": True,
            "avg_paragraph_word_count": 25.0,
            "has_filler_content": False, "overall_quality_pass": True,
            "quality_score": 80, "verdict": "excellent",
        }],
        failed_diagnoses=[],
        pending_count=5,
        auto_requeue=False,
        queued_count=0,
        fixed_count=0,
    )
    assert "avg_p=25w" in review
    assert "score=80" in review


def test_consulting_new_fields_in_generate_review_with_issues():
    """generate_review shows filler and hierarchy warnings."""
    review = generate_review(
        activity={"completed": [], "failed": [], "timeouts": []},
        recent_files=[],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=[{
            "file": "bad.md", "exists": True, "word_count": 50,
            "adequate": False, "has_headings": False, "has_paragraphs": False,
            "has_structure_elements": False, "structure_ok": False,
            "has_introduction": False, "has_conclusion": False,
            "section_count": 0, "broken_sections": 0, "min_sections_ok": False,
            "has_proper_heading_hierarchy": False,
            "avg_paragraph_word_count": 3.0,
            "has_filler_content": True, "overall_quality_pass": False,
            "quality_score": 10, "verdict": "poor",
        }],
        failed_diagnoses=[],
        pending_count=0,
        auto_requeue=False,
        queued_count=0,
        fixed_count=0,
    )
    assert "FILLER" in review
    assert "avg_p=3w" in review


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
