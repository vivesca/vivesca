"""Tests for metabolon.sortase.linter."""

from __future__ import annotations

from metabolon.sortase.linter import LintIssue, format_lint_report, lint_plan


# ---------------------------------------------------------------------------
# Fixtures as helpers
# ---------------------------------------------------------------------------

def _clean_plan() -> str:
    return """\
## Task
Build a new module at metabolon/sortase/linter.py

## Output
Write the result to metabolon/sortase/linter.py

## Constraints
- Do NOT use /tmp/ paths
- Never leave placeholder markers in code
- Must not modify existing tests without explicit instruction

## Verification
Run: cd ~/germline && .venv/bin/python -m pytest assays/test_sortase_linter.py -v

File paths: metabolon/sortase/linter.py, assays/test_sortase_linter.py
"""


def _minimal_plan() -> str:
    """Bare plan missing many sections."""
    return "Just do something."


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCleanPlanNoIssues:
    def test_clean_plan_no_issues(self) -> None:
        issues = lint_plan(_clean_plan())
        # Clean plan should have zero errors and zero warnings.
        # It may have info items but those are informational only.
        errors_and_warnings = [i for i in issues if i.severity in ("error", "warning")]
        assert errors_and_warnings == [], (
            f"Expected no errors/warnings, got: {errors_and_warnings}"
        )


class TestMissingOutputPathWarns:
    def test_missing_output_path_warns(self) -> None:
        plan = """\
## Task
Some task description.

## Constraints
- Do not break things

## Verification
Run: pytest

File: src/main.py
"""
        issues = lint_plan(plan)
        messages = [i.message for i in issues]
        assert any("No output path" in m for m in messages), (
            f"Expected 'No output path' warning, got: {messages}"
        )


class TestTmpReferenceErrors:
    def test_tmp_reference_errors(self) -> None:
        plan = """\
## Task
Write output to /tmp/scratch.md

## Output
Save to /tmp/result.txt

## Constraints
- Do not use local paths

## Verification
cat /tmp/result.txt

File: /tmp/scratch.md
"""
        issues = lint_plan(plan)
        tmp_issues = [i for i in issues if "/tmp/" in i.message]
        assert len(tmp_issues) >= 1, f"Expected /tmp/ errors, got: {issues}"
        for issue in tmp_issues:
            assert issue.severity == "error"
            assert issue.line_number is not None


class TestTodoMarkerErrors:
    def test_todo_marker_errors(self) -> None:
        plan = """\
## Task
Implement feature. TODO: add error handling later.

## Output
Write to src/feature.py

## Constraints
- Do not skip tests

## Verification
pytest src/

File: src/feature.py
"""
        issues = lint_plan(plan)
        todo_issues = [i for i in issues if "TODO" in i.message]
        assert len(todo_issues) >= 1, f"Expected TODO error, got: {issues}"
        for issue in todo_issues:
            assert issue.severity == "error"

    def test_fixme_marker_errors(self) -> None:
        plan = """\
## Task
Implement feature. FIXME: broken logic.

## Output
Write to src/feature.py

## Constraints
- Do not skip tests

## Verification
pytest src/

File: src/feature.py
"""
        issues = lint_plan(plan)
        fixme_issues = [i for i in issues if "FIXME" in i.message]
        assert len(fixme_issues) >= 1, f"Expected FIXME error, got: {issues}"
        for issue in fixme_issues:
            assert issue.severity == "error"


class TestNegatedPlaceholderNoFalsePositive:
    def test_do_not_todo_no_error(self) -> None:
        plan = """\
## Constraints
- Do NOT add TODO or FIXME

## Output
Write to: ~/out.md

## Verification
pytest
"""
        issues = lint_plan(plan)
        placeholder_issues = [i for i in issues if "placeholder marker" in i.message]
        assert placeholder_issues == [], (
            f"Expected no placeholder errors for negated instruction, got: {placeholder_issues}"
        )

    def test_never_fixme_no_error(self) -> None:
        plan = """\
## Constraints
- Never use FIXME as a crutch

## Output
Write to: ~/out.md

## Verification
pytest
"""
        issues = lint_plan(plan)
        placeholder_issues = [i for i in issues if "placeholder marker" in i.message]
        assert placeholder_issues == [], (
            f"Expected no placeholder errors for negated instruction, got: {placeholder_issues}"
        )

    def test_bare_todo_still_errors(self) -> None:
        plan = """\
## Task
TODO: implement this later

## Output
Write to: ~/out.md

## Constraints
- Do not rush

## Verification
pytest
"""
        issues = lint_plan(plan)
        todo_issues = [i for i in issues if "TODO" in i.message]
        assert len(todo_issues) >= 1, f"Expected TODO error for bare TODO, got: {issues}"


class TestNoConstraintsWarns:
    def test_no_constraints_warns(self) -> None:
        issues = lint_plan(_minimal_plan())
        messages = [i.message for i in issues]
        assert any("No constraints section" in m for m in messages), (
            f"Expected 'No constraints section' warning, got: {messages}"
        )


class TestFormatLintReport:
    def test_format_empty(self) -> None:
        report = format_lint_report([])
        assert report == "No issues found."

    def test_format_groups_by_severity(self) -> None:
        issues = [
            LintIssue("warning", "No output path"),
            LintIssue("error", "Bad /tmp/ ref", line_number=5),
            LintIssue("info", "Consider adding X"),
            LintIssue("error", "Another error", line_number=10),
        ]
        report = format_lint_report(issues)
        assert "ERROR" in report
        assert "WARNING" in report
        assert "INFO" in report
        # Errors section should come before warnings
        error_pos = report.index("ERROR")
        warning_pos = report.index("WARNING")
        assert error_pos < warning_pos

    def test_format_includes_line_numbers(self) -> None:
        issues = [
            LintIssue("error", "Bad ref", line_number=5),
        ]
        report = format_lint_report(issues)
        assert "line 5" in report

    def test_format_includes_summary(self) -> None:
        issues = [
            LintIssue("error", "E1"),
            LintIssue("warning", "W1"),
        ]
        report = format_lint_report(issues)
        assert "2 issue(s)" in report
