"""Tests for sortase validator."""
from __future__ import annotations

from pathlib import Path

from metabolon.sortase.validator import (
    ValidationIssue,
    check_dependency_pollution,
    check_scope,
    run_test_command,
    scan_for_placeholders,
    validate_execution,
)

# Marker constants — avoid triggering the scanner on this test file itself.
_MARKER_TODO = "T" + "ODO"
_MARKER_FIXME = "FI" + "XME"
_MARKER_STUB = "stu" + "b"


def _write_pyproject(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "pyproject.toml"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# check_dependency_pollution
# ---------------------------------------------------------------------------


class TestCheckDependencyPollution:
    def test_no_pyproject_returns_empty(self, tmp_path):
        issues = check_dependency_pollution(pyproject_path=tmp_path / "nonexistent.toml")
        assert issues == []

    def test_clean_pyproject_no_overlap(self, tmp_path):
        pyproject = _write_pyproject(
            tmp_path,
            '[project]\nname = "x"\ndependencies = ["rich"]\n'
            '[project.optional-dependencies]\ndev = ["pytest"]\n',
        )
        issues = check_dependency_pollution(pyproject_path=pyproject)
        assert issues == []

    def test_polluted_pyproject_detects_overlap(self, tmp_path):
        pyproject = _write_pyproject(
            tmp_path,
            '[project]\nname = "x"\ndependencies = ["rich", "requests"]\n'
            '[project.optional-dependencies]\ndev = ["rich"]\n',
        )
        issues = check_dependency_pollution(pyproject_path=pyproject)
        assert len(issues) == 1
        assert issues[0].check == "dependency-pollution"
        assert "rich" in issues[0].message
        assert issues[0].severity == "error"

    def test_multiple_overlaps(self, tmp_path):
        pyproject = _write_pyproject(
            tmp_path,
            '[project]\nname = "x"\ndependencies = ["rich", "requests", "click"]\n'
            '[project.optional-dependencies]\ndev = ["rich", "click"]\n',
        )
        issues = check_dependency_pollution(pyproject_path=pyproject)
        assert len(issues) == 1
        assert "rich" in issues[0].message
        assert "click" in issues[0].message

    def test_normalizes_version_specifiers(self, tmp_path):
        pyproject = _write_pyproject(
            tmp_path,
            '[project]\nname = "x"\ndependencies = ["rich>=10.0"]\n'
            '[project.optional-dependencies]\ndev = ["rich"]\n',
        )
        issues = check_dependency_pollution(pyproject_path=pyproject)
        assert len(issues) == 1

    def test_none_pyproject_returns_empty(self):
        issues = check_dependency_pollution(pyproject_path=None)
        assert issues == []

    def test_no_dependencies_key(self, tmp_path):
        pyproject = _write_pyproject(tmp_path, '[project]\nname = "x"\n')
        issues = check_dependency_pollution(pyproject_path=pyproject)
        assert issues == []


# ---------------------------------------------------------------------------
# check_scope
# ---------------------------------------------------------------------------


class TestCheckScope:
    def test_under_limit_no_issues(self, tmp_path):
        files = [f"file_{i}.py" for i in range(10)]
        issues = check_scope(tmp_path, max_files=20, changed_files=files)
        assert issues == []

    def test_exactly_at_limit_no_issues(self, tmp_path):
        files = [f"file_{i}.py" for i in range(20)]
        issues = check_scope(tmp_path, max_files=20, changed_files=files)
        assert issues == []

    def test_over_limit_warns(self, tmp_path):
        files = [f"file_{i}.py" for i in range(25)]
        issues = check_scope(tmp_path, max_files=20, changed_files=files)
        assert len(issues) == 1
        assert issues[0].check == "scope-check"
        assert issues[0].severity == "warning"
        assert "25" in issues[0].message

    def test_empty_changed_files(self, tmp_path):
        issues = check_scope(tmp_path, changed_files=[])
        assert issues == []

    def test_default_max_files(self, tmp_path):
        files = [f"file_{i}.py" for i in range(21)]
        issues = check_scope(tmp_path, changed_files=files)
        assert len(issues) == 1


# ---------------------------------------------------------------------------
# scan_for_placeholders
# ---------------------------------------------------------------------------


class TestScanForPlaceholders:
    def test_clean_file_no_issues(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text('print("hello")\n', encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["clean.py"])
        assert issues == []

    def test_todo_marker_detected_as_warning(self, tmp_path):
        f = tmp_path / "has_marker.py"
        f.write_text(f"# {_MARKER_TODO}: finish later\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["has_marker.py"])
        assert len(issues) == 1
        assert issues[0].check == "placeholder-scan"
        assert issues[0].severity == "warning"

    def test_fixme_marker_detected_as_warning(self, tmp_path):
        f = tmp_path / "has_marker2.py"
        f.write_text(f"# {_MARKER_FIXME}: broken logic\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["has_marker2.py"])
        assert len(issues) == 1
        assert issues[0].check == "placeholder-scan"
        assert issues[0].severity == "warning"

    def test_stub_marker_detected_as_error(self, tmp_path):
        f = tmp_path / "has_stub.py"
        f.write_text(f"# This is a {_MARKER_STUB} implementation\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["has_stub.py"])
        assert len(issues) == 1
        assert issues[0].check == "placeholder-scan"
        assert issues[0].severity == "error"

    def test_case_insensitive_markers(self, tmp_path):
        f = tmp_path / "upper.py"
        f.write_text(f"# {_MARKER_STUB.upper()} impl\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["upper.py"])
        assert len(issues) == 1
        assert issues[0].severity == "error"

    def test_empty_new_files_list(self, tmp_path):
        issues = scan_for_placeholders(tmp_path, [])
        assert issues == []

    def test_nonexistent_file_skipped(self, tmp_path):
        issues = scan_for_placeholders(tmp_path, ["does_not_exist.py"])
        assert issues == []

    def test_directory_entry_skipped(self, tmp_path):
        d = tmp_path / "subdir.py"
        d.mkdir()
        # "subdir.py" exists but is a directory, not a file
        issues = scan_for_placeholders(tmp_path, ["subdir.py"])
        assert issues == []

    def test_skip_dirs_excluded(self, tmp_path):
        nested = tmp_path / ".git" / "hooks"
        nested.mkdir(parents=True)
        f = nested / "hook.py"
        f.write_text(f"# {_MARKER_TODO}: remove later\n", encoding="utf-8")
        rel = str(Path(".git") / "hooks" / "hook.py")
        issues = scan_for_placeholders(tmp_path, [rel])
        assert issues == []

    def test_node_modules_excluded(self, tmp_path):
        nested = tmp_path / "node_modules" / "pkg"
        nested.mkdir(parents=True)
        f = nested / "index.js"
        f.write_text(f"// {_MARKER_TODO} something\n", encoding="utf-8")
        rel = str(Path("node_modules") / "pkg" / "index.js")
        issues = scan_for_placeholders(tmp_path, [rel])
        assert issues == []

    def test_pycache_excluded(self, tmp_path):
        nested = tmp_path / "__pycache__"
        nested.mkdir()
        f = nested / "mod.py"
        f.write_text(f"# {_MARKER_TODO}\n", encoding="utf-8")
        rel = str(Path("__pycache__") / "mod.py")
        issues = scan_for_placeholders(tmp_path, [rel])
        assert issues == []

    def test_venv_excluded(self, tmp_path):
        nested = tmp_path / ".venv" / "lib"
        nested.mkdir(parents=True)
        f = nested / "site.py"
        f.write_text(f"# {_MARKER_FIXME}\n", encoding="utf-8")
        rel = str(Path(".venv") / "lib" / "site.py")
        issues = scan_for_placeholders(tmp_path, [rel])
        assert issues == []

    def test_target_excluded(self, tmp_path):
        nested = tmp_path / "target" / "debug"
        nested.mkdir(parents=True)
        f = nested / "main.rs"
        f.write_text(f"// {_MARKER_TODO}\n", encoding="utf-8")
        rel = str(Path("target") / "debug" / "main.rs")
        issues = scan_for_placeholders(tmp_path, [rel])
        assert issues == []

    def test_multiple_files_with_markers(self, tmp_path):
        (tmp_path / "a.py").write_text(f"# {_MARKER_TODO}: a\n", encoding="utf-8")
        (tmp_path / "b.py").write_text(f"# {_MARKER_FIXME}: b\n", encoding="utf-8")
        (tmp_path / "c.py").write_text('print("ok")\n', encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["a.py", "b.py", "c.py"])
        assert len(issues) == 2
        assert all(i.severity == "warning" for i in issues)

    def test_mixed_stub_and_todo_in_one_file(self, tmp_path):
        f = tmp_path / "mixed.py"
        f.write_text(f"# {_MARKER_STUB}: impl\n# {_MARKER_TODO}: later\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["mixed.py"])
        assert len(issues) == 2
        severities = {i.severity for i in issues}
        assert severities == {"error", "warning"}

    def test_word_boundary_prevents_partial_match(self, tmp_path):
        f = tmp_path / "partial.py"
        # "astur" contains "stu" but with word boundary \b, "stub" won't match "astur"
        f.write_text("astur\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["partial.py"])
        assert issues == []

    def test_embedded_in_code(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(f'raise NotImplementedError("{_MARKER_TODO}: implement me")\n', encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["code.py"])
        assert len(issues) == 1
        assert issues[0].severity == "warning"

    def test_message_includes_filename(self, tmp_path):
        f = tmp_path / "specific_name.py"
        f.write_text(f"# {_MARKER_TODO}\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["specific_name.py"])
        assert "specific_name.py" in issues[0].message
        assert issues[0].severity == "warning"

    # --- HEAD-comparison tests (pre-existing vs new markers) ---

    @staticmethod
    def _init_git_repo(repo_dir: Path) -> None:
        """Create a git repo with an initial commit so HEAD exists."""
        import subprocess

        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        # Create a dummy file and commit so HEAD exists.
        readme = repo_dir / "README.md"
        readme.write_text("# test\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

    def test_preexisting_marker_not_flagged(self, tmp_path):
        """A TODO that was already in the file at HEAD should NOT be flagged."""
        import subprocess

        self._init_git_repo(tmp_path)
        f = tmp_path / "code.py"
        f.write_text(f"# {_MARKER_TODO}: pre-existing\nprint('hello')\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "add marker"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        # Now modify the file WITHOUT changing the marker line.
        f.write_text(f"# {_MARKER_TODO}: pre-existing\nprint('hello')\nprint('new line')\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["code.py"])
        assert issues == []

    def test_new_marker_in_existing_file_flagged(self, tmp_path):
        """A NEW TODO added to a file that existed at HEAD should be flagged."""
        import subprocess

        self._init_git_repo(tmp_path)
        f = tmp_path / "code.py"
        f.write_text("print('hello')\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "add code"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        # Add a new TODO marker.
        f.write_text(f"# {_MARKER_TODO}: new marker\nprint('hello')\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["code.py"])
        assert len(issues) == 1
        assert issues[0].check == "placeholder-scan"
        assert issues[0].severity == "warning"

    def test_brand_new_file_with_marker_flagged(self, tmp_path):
        """A brand-new file (not in HEAD) with a marker should be flagged."""

        self._init_git_repo(tmp_path)
        f = tmp_path / "new_file.py"
        f.write_text(f"# {_MARKER_TODO}: new file marker\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["new_file.py"])
        assert len(issues) == 1
        assert issues[0].severity == "warning"

    def test_preexisting_marker_plus_new_marker_flagged(self, tmp_path):
        """File with a pre-existing marker that also gets a NEW marker should be flagged."""
        import subprocess

        self._init_git_repo(tmp_path)
        f = tmp_path / "code.py"
        f.write_text(f"# {_MARKER_TODO}: old\nprint('x')\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "add old marker"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        # Add a new FIXME alongside the existing TODO.
        f.write_text(f"# {_MARKER_TODO}: old\n# {_MARKER_FIXME}: new\nprint('x')\n", encoding="utf-8")
        issues = scan_for_placeholders(tmp_path, ["code.py"])
        assert len(issues) == 1
        assert issues[0].severity == "warning"


# ---------------------------------------------------------------------------
# run_test_command
# ---------------------------------------------------------------------------


class TestRunTestCommand:
    def test_no_command_returns_success(self, tmp_path):
        ok, msg = run_test_command(tmp_path, None)
        assert ok is True
        assert "No test command" in msg

    def test_successful_command(self, tmp_path):
        ok, _output = run_test_command(tmp_path, "true")
        assert ok is True

    def test_failing_command(self, tmp_path):
        ok, _output = run_test_command(tmp_path, "false")
        assert ok is False

    def test_command_with_stderr_output(self, tmp_path):
        script = tmp_path / "echo_test.sh"
        script.write_text('#!/bin/bash\necho "hello stderr" >&2\n', encoding="utf-8")
        script.chmod(0o755)
        ok, output = run_test_command(tmp_path, str(script))
        assert ok is True
        assert "hello stderr" in output

    def test_command_with_stdout_output(self, tmp_path):
        script = tmp_path / "stdout_test.sh"
        script.write_text('#!/bin/bash\necho "hello stdout"\n', encoding="utf-8")
        script.chmod(0o755)
        ok, output = run_test_command(tmp_path, str(script))
        assert ok is True
        assert "hello stdout" in output


# ---------------------------------------------------------------------------
# validate_execution (integration)
# ---------------------------------------------------------------------------


class TestValidateExecution:
    def test_clean_project_no_issues(self, tmp_path):
        (tmp_path / "clean.py").write_text('print("hello")\n', encoding="utf-8")
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=["clean.py"],
        )
        assert issues == []

    def test_empty_new_files_list(self, tmp_path):
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=[],
        )
        placeholder_issues = [i for i in issues if i.check == "placeholder-scan"]
        assert placeholder_issues == []

    def test_placeholder_in_new_file(self, tmp_path):
        (tmp_path / "marked.py").write_text(f"# {_MARKER_TODO}: pending\n", encoding="utf-8")
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=["marked.py"],
        )
        placeholder_issues = [i for i in issues if i.check == "placeholder-scan"]
        assert len(placeholder_issues) == 1

    def test_failing_test_command(self, tmp_path):
        (tmp_path / "clean.py").write_text('print("ok")\n', encoding="utf-8")
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=["clean.py"],
            test_command="false",
        )
        test_issues = [i for i in issues if i.check == "tests"]
        assert len(test_issues) == 1
        assert test_issues[0].severity == "error"

    def test_dependency_pollution_in_integration(self, tmp_path):
        pyproject = _write_pyproject(
            tmp_path,
            '[project]\nname = "x"\ndependencies = ["rich"]\n'
            '[project.optional-dependencies]\ndev = ["rich"]\n',
        )
        (tmp_path / "clean.py").write_text('print("ok")\n', encoding="utf-8")
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=["clean.py"],
            pyproject_path=pyproject,
        )
        dep_issues = [i for i in issues if i.check == "dependency-pollution"]
        assert len(dep_issues) == 1

    def test_multiple_issues_combined(self, tmp_path):
        pyproject = _write_pyproject(
            tmp_path,
            '[project]\nname = "x"\ndependencies = ["click"]\n'
            '[project.optional-dependencies]\ndev = ["click"]\n',
        )
        (tmp_path / "bad.py").write_text(f"# {_MARKER_FIXME}: broken\n", encoding="utf-8")
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=["bad.py"],
            test_command="false",
            pyproject_path=pyproject,
        )
        checks = {i.check for i in issues}
        assert "dependency-pollution" in checks
        assert "placeholder-scan" in checks
        assert "tests" in checks

    def test_no_test_command_no_test_issue(self, tmp_path):
        (tmp_path / "clean.py").write_text('print("ok")\n', encoding="utf-8")
        issues = validate_execution(
            project_dir=tmp_path,
            new_files=["clean.py"],
            test_command=None,
        )
        test_issues = [i for i in issues if i.check == "tests"]
        assert test_issues == []


# ---------------------------------------------------------------------------
# ValidationIssue dataclass
# ---------------------------------------------------------------------------


class TestValidationIssue:
    def test_fields(self):
        issue = ValidationIssue(check="test-check", message="test message", severity="warning")
        assert issue.check == "test-check"
        assert issue.message == "test message"
        assert issue.severity == "warning"

    def test_default_severity_is_error(self):
        issue = ValidationIssue(check="x", message="m")
        assert issue.severity == "error"

    def test_frozen(self):
        issue = ValidationIssue(check="x", message="m")
        raised = False
        try:
            issue.check = "y"  # type: ignore[misc]
        except AttributeError:
            raised = True
        assert raised, "Should have raised AttributeError on frozen dataclass"

    def test_equality(self):
        a = ValidationIssue(check="c", message="m")
        b = ValidationIssue(check="c", message="m")
        assert a == b

    def test_hashable(self):
        a = ValidationIssue(check="c", message="m")
        b = ValidationIssue(check="c", message="m")
        assert hash(a) == hash(b)
        assert len({a, b}) == 1
