"""Tests for metabolon.sortase.validator."""
from __future__ import annotations

import tempfile
from pathlib import Path

from metabolon.sortase.validator import (
    ValidationIssue,
    check_dependency_pollution,
    check_scope,
    check_test_coverage,
    run_test_command,
    scan_for_placeholders,
    validate_execution,
    _normalize_dep,
)


def test_normalize_dep_strips_version():
    assert _normalize_dep("pytest>=7.0") == "pytest"
    assert _normalize_dep("requests[security]~=2.31") == "requests"
    assert _normalize_dep("flask<3") == "flask"
    assert _normalize_dep("jinja2") == "jinja2"


def test_validationissue_defaults():
    issue = ValidationIssue("check", "message")
    assert issue.severity == "error"
    assert issue.check == "check"
    assert issue.message == "message"


class TestCheckDependencyPollution:
    def test_no_pyproject_returns_empty(self):
        issues = check_dependency_pollution(pyproject_path=Path("/nonexistent/pyproject.toml"))
        assert issues == []

    def test_none_pyproject_returns_empty(self):
        issues = check_dependency_pollution(pyproject_path=None)
        assert issues == []

    def test_clean_pyproject_no_overlap(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[project]
dependencies = ["pytest", "requests"]
optional-dependencies = {"dev" = ["black", "mypy"]}
            """.strip())
        path = Path(f.name)
        try:
            issues = check_dependency_pollution(pyproject_path=path)
            assert issues == []
        finally:
            path.unlink()

    def test_polluted_pyproject_detects_overlap(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""
[project]
dependencies = ["pytest", "requests", "black"]
optional-dependencies = {"dev" = ["black", "mypy"]}
            """.strip())
        path = Path(f.name)
        try:
            issues = check_dependency_pollution(pyproject_path=path)
            assert len(issues) == 1
            assert "black" in issues[0].message
            assert issues[0].check == "dependency-pollution"
        finally:
            path.unlink()


class TestCheckScope:
    def test_under_limit_no_issues(self):
        issues = check_scope(Path.cwd(), max_files=10, max_dirs=3, changed_files=["a.py", "b.py"])
        assert issues == []

    def test_over_limit_warns(self):
        files = [f"f{i}.py" for i in range(21)]
        issues = check_scope(Path.cwd(), max_files=20, max_dirs=3, changed_files=files)
        # 21 top-level files will trigger both file count and directory spread warnings
        assert len(issues) == 2
        assert any("21 files" in issue.message for issue in issues)
        assert all(issue.severity == "warning" for issue in issues)

    def test_four_directories_over_limit_warns(self):
        files = ["d1/a.py", "d2/b.py", "d3/c.py", "d4/d.py"]
        issues = check_scope(Path.cwd(), max_files=20, max_dirs=3, changed_files=files)
        assert len(issues) == 1
        assert "4 top-level" in issues[0].message

    def test_empty_changed_files(self):
        issues = check_scope(Path.cwd(), max_files=10, max_dirs=3, changed_files=[])
        assert issues == []


class TestScanForPlaceholders:
    def test_clean_file_no_issues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            f = tmpdir / "test.py"
            f.write_text("def hello(): return 42")
            issues = scan_for_placeholders(tmpdir, ["test.py"])
            assert issues == []

    def test_stub_marker_detected_as_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            f = tmpdir / "test.py"
            f.write_text("# stub implementation here")
            issues = scan_for_placeholders(tmpdir, ["test.py"])
            assert len(issues) == 1
            assert issues[0].severity == "error"
            assert "Stub" in issues[0].message

    def test_todo_marker_detected_as_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            f = tmpdir / "test.py"
            f.write_text("# TODO: fix this later")
            issues = scan_for_placeholders(tmpdir, ["test.py"])
            assert len(issues) == 1
            assert issues[0].severity == "warning"
            assert "TODO" in issues[0].message

    def test_nonexistent_file_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            issues = scan_for_placeholders(tmpdir, ["nonexistent.py"])
            assert issues == []

    def test_skip_dirs_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "__pycache__").mkdir()
            f = tmpdir / "__pycache__" / "test.py"
            f.write_text("# stub")
            issues = scan_for_placeholders(tmpdir, ["__pycache__/test.py"])
            assert issues == []


class TestRunTestCommand:
    def test_no_command_returns_success(self):
        ok, output = run_test_command(Path.cwd(), None)
        assert ok
        assert "No test command" in output

    def test_successful_command(self):
        ok, output = run_test_command(Path.cwd(), "echo hello")
        assert ok
        assert "hello" in output

    def test_failing_command(self):
        ok, output = run_test_command(Path.cwd(), "false")
        assert not ok


class TestValidateExecution:
    def test_clean_project_no_issues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            issues = validate_execution(tmpdir, [], test_command="echo ok")
            assert len([i for i in issues if i.severity == "error"]) == 0
