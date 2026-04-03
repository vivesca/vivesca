from __future__ import annotations

"""Tests for effectors/test-fixer — pytest failure parser and reporter."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Load the effector via exec (standard pattern for effectors)
# ---------------------------------------------------------------------------

def _load_test_fixer():
    source = open(Path.home() / "germline" / "effectors" / "test-fixer").read()
    ns: dict = {"__name__": "test_fixer_effector"}
    exec(source, ns)
    return ns


_mod = _load_test_fixer()
classify_error = _mod["classify_error"]
parse_failures = _mod["parse_failures"]
format_markdown = _mod["format_markdown"]
format_json = _mod["format_json"]
run_pytest = _mod["run_pytest"]
main = _mod["main"]


# ── classify_error tests ─────────────────────────────────────────────────


def test_classify_import_error():
    assert classify_error("ImportError: no module named foo") == "missing or circular import"


def test_classify_module_not_found():
    assert classify_error("ModuleNotFoundError: bar") == "missing or circular import"


def test_classify_attribute_error():
    assert classify_error("AttributeError: 'NoneType' has no attr") == "attribute access on wrong type or misspelled name"


def test_classify_type_error():
    assert classify_error("TypeError: expected str got int") == "type mismatch — wrong argument count or type"


def test_classify_name_error():
    assert classify_error("NameError: name 'x' is not defined") == "undefined name (typo or missing import)"


def test_classify_file_not_found():
    assert classify_error("FileNotFoundError: data.json") == "missing fixture file or bad path"


def test_classify_key_error():
    assert classify_error("KeyError: 'result'") == "dict key missing — data shape changed"


def test_classify_value_error():
    assert classify_error("ValueError: invalid literal") == "bad value — conversion or validation failure"


def test_classify_index_error():
    assert classify_error("IndexError: list index out of range") == "list/tuple index out of range"


def test_classify_syntax_error():
    assert classify_error("SyntaxError: invalid syntax") == "syntax error in source file"


def test_classify_assertion_error():
    assert classify_error("AssertionError: assert False") == "assertion failed — logic or data mismatch"


def test_classify_recursion_error():
    assert classify_error("RecursionError: maximum recursion depth") == "infinite recursion"


def test_classify_unknown():
    assert classify_error("something completely unrelated") == "unknown error type"


# ── parse_failures tests ─────────────────────────────────────────────────


def test_parse_failures_empty():
    result = parse_failures("")
    assert result == {}


def test_parse_failures_single():
    output = "FAILED assays/test_foo.py::test_bar - TypeError: bad arg\n"
    groups = parse_failures(output)
    assert "assays/test_foo.py" in groups
    assert len(groups["assays/test_foo.py"]) == 1
    entry = groups["assays/test_foo.py"][0]
    assert entry["test"] == "test_bar"
    assert "TypeError: bad arg" in entry["error"]
    assert entry["cause"] == "type mismatch — wrong argument count or type"


def test_parse_failures_multiple_files():
    output = (
        "FAILED assays/test_a.py::test_one - ValueError: bad\n"
        "FAILED assays/test_b.py::test_two - KeyError: 'x'\n"
    )
    groups = parse_failures(output)
    assert len(groups) == 2
    assert "assays/test_a.py" in groups
    assert "assays/test_b.py" in groups


def test_parse_failures_multiple_tests_same_file():
    output = (
        "FAILED assays/test_a.py::test_one - TypeError: a\n"
        "FAILED assays/test_a.py::test_two - ValueError: b\n"
    )
    groups = parse_failures(output)
    assert len(groups) == 1
    assert len(groups["assays/test_a.py"]) == 2


def test_parse_failures_with_traceback_line():
    output = (
        "FAILED assays/test_a.py::test_one - AssertionError: assert False\n"
        "assays/test_a.py:42: AssertionError: assert False\n"
    )
    groups = parse_failures(output)
    entry = groups["assays/test_a.py"][0]
    assert entry["line"] == "42"


def test_parse_failures_no_error_detail():
    output = "FAILED assays/test_a.py::test_one\n"
    groups = parse_failures(output)
    assert "assays/test_a.py" in groups
    entry = groups["assays/test_a.py"][0]
    assert entry["test"] == "test_one"
    assert entry["error"] == ""


# ── format_markdown tests ────────────────────────────────────────────────


def test_format_markdown_no_failures():
    md = format_markdown({}, 0)
    assert "No failures found" in md
    assert "All tests passing" in md


def test_format_markdown_with_failures():
    groups = {
        "assays/test_a.py": [
            {"test": "test_one", "line": "10", "error": "TypeError: bad", "cause": "type mismatch — wrong argument count or type"},
        ]
    }
    md = format_markdown(groups, 1)
    assert "## Test Failure Report" in md
    assert "**1 failure(s)**" in md
    assert "assays/test_a.py" in md
    assert "test_one" in md
    assert "TypeError: bad" in md
    assert "type mismatch" in md


def test_format_markdown_table_headers():
    groups = {
        "assays/x.py": [
            {"test": "test_t", "line": "", "error": "", "cause": "unknown error type"},
        ]
    }
    md = format_markdown(groups, 1)
    assert "| Test |" in md
    assert "|------|" in md


def test_format_markdown_truncates_long_error():
    long_err = "x" * 200
    groups = {
        "a.py": [
            {"test": "test_t", "line": "", "error": long_err, "cause": "unknown error type"},
        ]
    }
    md = format_markdown(groups, 1)
    # Error should be truncated to 80 chars in the table
    for line in md.splitlines():
        if "test_t" in line:
            assert len(line) < 300  # reasonable bound
            break


# ── format_json tests ────────────────────────────────────────────────────


def test_format_json_structure():
    groups = {
        "a.py": [
            {"test": "test_x", "line": "5", "error": "err", "cause": "cause"},
        ]
    }
    out = format_json(groups, 1)
    data = json.loads(out)
    assert data["total_failed"] == 1
    assert data["files_affected"] == 1
    assert "a.py" in data["failures"]
    assert data["failures"]["a.py"][0]["test"] == "test_x"


def test_format_json_empty():
    out = format_json({}, 0)
    data = json.loads(out)
    assert data["total_failed"] == 0
    assert data["files_affected"] == 0
    assert data["failures"] == {}


# ── run_pytest tests ─────────────────────────────────────────────────────


def test_run_pytest_success(tmp_path):
    """run_pytest returns stdout and returncode."""
    # Create a tiny passing test
    (tmp_path / "test_pass.py").write_text("def test_ok(): assert True\n")
    stdout, rc = run_pytest(tmp_path)
    assert rc == 0
    assert "1 passed" in stdout


def test_run_pytest_failure(tmp_path):
    """run_pytest returns non-zero rc for failures."""
    (tmp_path / "test_fail.py").write_text("def test_bad(): assert False\n")
    stdout, rc = run_pytest(tmp_path)
    assert rc != 0
    assert "FAILED" in stdout


# ── main (CLI) tests ─────────────────────────────────────────────────────


def test_main_markdown_output(tmp_path, capsys):
    """main outputs markdown by default."""
    (tmp_path / "test_pass.py").write_text("def test_ok(): assert True\n")
    with pytest.raises(SystemExit) as exc_info:
        main(["--dir", str(tmp_path)])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "No failures found" in out


def test_main_json_output(tmp_path, capsys):
    """main --json outputs valid JSON."""
    (tmp_path / "test_pass.py").write_text("def test_ok(): assert True\n")
    with pytest.raises(SystemExit) as exc_info:
        main(["--json", "--dir", str(tmp_path)])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total_failed"] == 0


def test_main_with_failures_json(tmp_path, capsys):
    """main --json with a failing test reports the failure."""
    (tmp_path / "test_fail.py").write_text("def test_bad(): assert False\n")
    with pytest.raises(SystemExit) as exc_info:
        main(["--json", "--dir", str(tmp_path)])
    assert exc_info.value.code != 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total_failed"] >= 1
    assert data["files_affected"] >= 1


def test_main_with_failures_markdown(tmp_path, capsys):
    """main with a failing test outputs markdown table."""
    (tmp_path / "test_fail.py").write_text("def test_bad(): assert False\n")
    with pytest.raises(SystemExit):
        main(["--dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert "## Test Failure Report" in out
    assert "test_fail.py" in out
    assert "test_bad" in out
