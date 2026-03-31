from __future__ import annotations
"""Tests for metabolon.sortase.linter."""

from metabolon.sortase.linter import lint_plan, format_lint_report, LintIssue


def test_empty_plan_errors():
    issues = lint_plan("")
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "empty" in issues[0].message.lower()


def test_clean_plan_no_issues():
    plan = """# Implementation Plan

## Constraints
- Do not break existing API
- Keep changes minimal

## Output path
Write the result to ~/germline/metabolon/sortase/new.py

## Verification
Run pytest on the test file to verify

Do NOT commit large binary files.
"""
    issues = lint_plan(plan)
    assert not [i for i in issues if i.severity == "error"]
    # Expect maybe info messages but no errors
    assert all(i.severity != "error" for i in issues)


def test_missing_output_path_warns():
    plan = """# Plan
## Constraints
- Just do it

No output mentioned here at all.
"""
    issues = lint_plan(plan)
    assert any("output path" in i.message.lower() and i.severity == "warning" for i in issues)


def test_tmp_reference_errors():
    plan = """# Plan
Write output to /tmp/myoutput.txt
"""
    issues = lint_plan(plan)
    assert any("/tmp/" in i.message for i in issues)
    assert any(i.severity == "error" for i in issues)
    assert any(i.line_number == 2 for i in issues)


def test_todo_marker_errors():
    plan = """# Plan
# TODO: implement this later
"""
    issues = lint_plan(plan)
    assert any("TODO" in i.message for i in issues)
    assert any(i.severity == "error" for i in issues)


def test_fixme_marker_errors():
    plan = """# Plan
# FIXME: fix this bug
"""
    issues = lint_plan(plan)
    assert any("FIXME" in i.message for i in issues)
    assert any(i.severity == "error" for i in issues)


def test_negated_todo_no_error():
    plan = """# Plan
Do NOT add TODO comments here.
"""
    issues = lint_plan(plan)
    # Should not error because TODO is negated
    assert not any("Contains placeholder marker: TODO" in i.message for i in issues)


def test_no_constraints_warns():
    plan = """# Plan
Just do this.
"""
    issues = lint_plan(plan)
    assert any("constraints" in i.message.lower() for i in issues)


def test_format_lint_report_empty():
    report = format_lint_report([])
    assert "No issues found" in report


def test_format_lint_report_groups_by_severity():
    issues = [
        LintIssue("error", "bad thing happened", 10),
        LintIssue("warning", "something could be better"),
    ]
    report = format_lint_report(issues)
    assert "ERROR" in report
    assert "WARNING" in report
    assert "bad thing happened" in report
    assert "(line 10)" in report


def test_format_lint_report_includes_summary():
    issues = [
        LintIssue("error", "err1"),
        LintIssue("error", "err2"),
        LintIssue("warning", "warn1"),
    ]
    report = format_lint_report(issues)
    assert "3 issue(s) found" in report
