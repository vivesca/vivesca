from __future__ import annotations

"""Tests for test-fixer — pytest failure parser and markdown reporter."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_test_fixer():
    """Load test-fixer by exec-ing its source (effector pattern)."""
    source = open(Path.home() / "germline/effectors/test-fixer").read()
    ns: dict = {"__name__": "test_fixer"}
    exec(source, ns)
    return ns


# ── Unit tests: parse_pytest_output ──────────────────────────────────

SAMPLE_OUTPUT_SIMPLE = """\
FAILED assays/test_foo.py::test_bar - AssertionError: expected 1, got 0
FAILED assays/test_foo.py::test_baz - TypeError: unsupported operand
FAILED assays/test_qux.py::test_spam - ModuleNotFoundError: No module named 'x'
1 passed, 3 failed in 0.5s
"""

SAMPLE_OUTPUT_TRACEBACKS = """\
FAILED assays/test_alpha.py::test_one - assert False
FAILED assays/test_alpha.py::test_two - ValueError: bad value
FAILED assays/test_beta.py::test_three - ImportError: nope
=========================== short test summary info ============================
FAILED assays/test_alpha.py::test_one - assert False
FAILED assays/test_alpha.py::test_two - ValueError: bad value
FAILED assays/test_beta.py::test_three - ImportError: nope
============================== 2 failed in 0.3s ===============================
"""

SAMPLE_OUTPUT_EMPTY = """\
3 passed in 0.2s
"""

SAMPLE_OUTPUT_ERROR = """\
ERROR assays/test_broken.py::setup - fixture 'db' not found
FAILED assays/test_broken.py::test_query - AssertionError: 0 != 1
1 failed, 1 error in 0.1s
"""

SAMPLE_MIXED_FAILURES = """\
FAILED assays/test_api.py::test_get_user - AssertionError: 404 != 200
FAILED assays/test_api.py::test_post_user - json.decoder.JSONDecodeError: Expecting value
FAILED assays/test_db.py::test_connect - ConnectionRefusedError: [Errno 111]
FAILED assays/test_db.py::test_insert - sqlite3.OperationalError: no such table: users
FAILED assays/test_utils.py::test_helper - AttributeError: 'NoneType' has no attribute 'split'
1 passed, 5 failed in 1.2s
"""


_mod = _load_test_fixer()
parse_pytest_output = _mod["parse_pytest_output"]
group_by_file = _mod["group_by_file"]
diagnose_failure = _mod["diagnose_failure"]
generate_markdown = _mod["generate_markdown"]
run_pytest = _mod["run_pytest"]
main = _mod["main"]


# ── parse_pytest_output ──────────────────────────────────────────────


def test_parse_simple_failures():
    """parse_pytest_output extracts test name, file, and error from FAILED lines."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    assert len(results) == 3
    assert results[0]["file"] == "assays/test_foo.py"
    assert results[0]["test"] == "test_bar"
    assert "AssertionError" in results[0]["error"]
    assert results[1]["file"] == "assays/test_foo.py"
    assert results[1]["test"] == "test_baz"
    assert "TypeError" in results[1]["error"]
    assert results[2]["file"] == "assays/test_qux.py"
    assert results[2]["test"] == "test_spam"


def test_parse_skips_duplicate_summary_lines():
    """parse_pytest_output deduplicates the short summary section."""
    results = parse_pytest_output(SAMPLE_OUTPUT_TRACEBACKS)
    assert len(results) == 3


def test_parse_empty_output():
    """parse_pytest_output returns empty list when all tests pass."""
    results = parse_pytest_output(SAMPLE_OUTPUT_EMPTY)
    assert results == []


def test_parse_captures_error_prefix():
    """parse_pytest_output handles ERROR lines (fixture failures)."""
    results = parse_pytest_output(SAMPLE_OUTPUT_ERROR)
    # Should have at least the FAILED line; ERROR is also captured
    files = {r["file"] for r in results}
    assert "assays/test_broken.py" in files


def test_parse_extracts_error_type():
    """Each parsed result has 'error_type' field with the exception class."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    assert results[0]["error_type"] == "AssertionError"
    assert results[1]["error_type"] == "TypeError"
    assert results[2]["error_type"] == "ModuleNotFoundError"


# ── group_by_file ────────────────────────────────────────────────────


def test_group_by_file_groups_correctly():
    """group_by_file returns dict keyed by file path."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    grouped = group_by_file(results)
    assert "assays/test_foo.py" in grouped
    assert len(grouped["assays/test_foo.py"]) == 2
    assert "assays/test_qux.py" in grouped
    assert len(grouped["assays/test_qux.py"]) == 1


def test_group_by_file_empty():
    """group_by_file returns empty dict for empty results."""
    assert group_by_file([]) == {}


# ── diagnose_failure ─────────────────────────────────────────────────


def test_diagnose_assertion_error():
    """AssertionError diagnosed as logic/assertion issue."""
    cause = diagnose_failure("AssertionError", "expected 1, got 0")
    assert "assert" in cause.lower() or "logic" in cause.lower()


def test_diagnose_import_error():
    """ImportError/ModuleNotFoundError diagnosed as missing dependency."""
    cause = diagnose_failure("ModuleNotFoundError", "No module named 'x'")
    assert "import" in cause.lower() or "module" in cause.lower() or "depend" in cause.lower()


def test_diagnose_type_error():
    """TypeError diagnosed as type mismatch."""
    cause = diagnose_failure("TypeError", "unsupported operand")
    assert "type" in cause.lower()


def test_diagnose_attribute_error():
    """AttributeError diagnosed as missing attribute/None access."""
    cause = diagnose_failure("AttributeError", "'NoneType' has no attribute 'split'")
    assert "attribute" in cause.lower() or "none" in cause.lower()


def test_diagnose_connection_error():
    """Connection errors diagnosed as infrastructure issue."""
    cause = diagnose_failure("ConnectionRefusedError", "[Errno 111]")
    assert "connection" in cause.lower() or "network" in cause.lower() or "infra" in cause.lower()


def test_diagnose_unknown_error():
    """Unknown error types get a generic diagnosis."""
    cause = diagnose_failure("FoobarError", "something weird")
    assert len(cause) > 0


# ── generate_markdown ────────────────────────────────────────────────


def test_generate_markdown_includes_headers():
    """Markdown report has title and file section headers."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    grouped = group_by_file(results)
    md = generate_markdown(grouped, results)
    assert "# Test Failure Report" in md
    assert "assays/test_foo.py" in md
    assert "assays/test_qux.py" in md


def test_generate_markdown_includes_test_names():
    """Markdown report lists individual failing test names."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    grouped = group_by_file(results)
    md = generate_markdown(grouped, results)
    assert "test_bar" in md
    assert "test_baz" in md
    assert "test_spam" in md


def test_generate_markdown_includes_diagnosis():
    """Markdown report includes likely cause for each failure."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    grouped = group_by_file(results)
    md = generate_markdown(grouped, results)
    # Should have diagnosis sections
    assert "Likely cause" in md or "likely" in md.lower() or "Cause" in md


def test_generate_markdown_includes_summary():
    """Markdown report includes a summary section with counts."""
    results = parse_pytest_output(SAMPLE_OUTPUT_SIMPLE)
    grouped = group_by_file(results)
    md = generate_markdown(grouped, results)
    assert "Summary" in md or "summary" in md
    assert "3" in md  # 3 total failures


def test_generate_markdown_empty():
    """Empty results produce a 'no failures' message."""
    md = generate_markdown({}, [])
    assert "no failures" in md.lower() or "all tests passed" in md.lower()


def test_generate_markdown_mixed_errors():
    """Report correctly handles mixed error types from different files."""
    results = parse_pytest_output(SAMPLE_MIXED_FAILURES)
    grouped = group_by_file(results)
    md = generate_markdown(grouped, results)
    assert "assays/test_api.py" in md
    assert "assays/test_db.py" in md
    assert "assays/test_utils.py" in md


# ── main / CLI integration ──────────────────────────────────────────


def _mock_completed_process(stdout: str, returncode: int) -> MagicMock:
    """Build a CompletedProcess-like mock with both stdout and stderr."""
    return MagicMock(stdout=stdout, stderr="", returncode=returncode)


def test_main_outputs_markdown_by_default(capsys):
    """main() prints markdown report to stdout."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_completed_process(SAMPLE_OUTPUT_SIMPLE, 1)
        main([])
        captured = capsys.readouterr()
        assert "Test Failure Report" in captured.out


def test_main_json_flag(capsys):
    """main(['--json']) outputs valid JSON."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_completed_process(SAMPLE_OUTPUT_SIMPLE, 1)
        main(["--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "failures" in data
        assert len(data["failures"]) == 3


def test_main_all_pass(capsys):
    """main() handles all-passing test suites."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_completed_process(SAMPLE_OUTPUT_EMPTY, 0)
        main([])
        captured = capsys.readouterr()
        assert "no failures" in captured.out.lower() or "all tests passed" in captured.out.lower()


def test_main_json_all_pass(capsys):
    """main(['--json']) with no failures returns empty list."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_completed_process(SAMPLE_OUTPUT_EMPTY, 0)
        main(["--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["failures"] == []
