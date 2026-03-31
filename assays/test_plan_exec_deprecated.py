from __future__ import annotations

"""Tests for plan-exec.deprecated — AI orchestrator fallback chain."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "plan-exec.deprecated"


def _load_module():
    """Load the plan-exec module by exec-ing its Python body."""
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "plan_exec_test"}
    exec(source, ns)
    return ns


_mod = _load_module()

RESULTS_DIR = _mod["RESULTS_DIR"]
BACKENDS = _mod["BACKENDS"]
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
main = _mod["main"]


# ── Constants tests ──────────────────────────────────────────────────


class TestConstants:
    """Verify module-level constants."""

    def test_results_dir_is_under_cache(self):
        """RESULTS_DIR lives under ~/.cache/plan-exec."""
        assert str(RESULTS_DIR).endswith("plan-exec")
        assert ".cache" in str(RESULTS_DIR)

    def test_backends_list_has_three_entries(self):
        """BACKENDS has exactly 3 backend definitions."""
        assert len(BACKENDS) == 3

    def test_backends_names(self):
        """Backend names are gemini, codex, opencode in order."""
        names = [b["name"] for b in BACKENDS]
        assert names == ["gemini", "codex", "opencode"]

    def test_every_backend_has_required_keys(self):
        """Each backend dict has name, cmd, cwd."""
        for b in BACKENDS:
            assert "name" in b
            assert "cmd" in b
            assert "cwd" in b
            assert callable(b["cmd"])
            assert callable(b["cwd"])

    def test_opencode_has_env_extra(self):
        """The opencode backend sets OPENCODE_HOME."""
        oc = BACKENDS[2]
        assert oc["name"] == "opencode"
        assert "env_extra" in oc
        assert "OPENCODE_HOME" in oc["env_extra"]

    def test_results_dir_is_path(self):
        """RESULTS_DIR is a Path object."""
        assert isinstance(RESULTS_DIR, Path)


# ── _build_prompt tests ──────────────────────────────────────────────


class TestBuildPrompt:
    """Tests for _build_prompt(project, prompt_file)."""

    def test_includes_plan_content(self, tmp_path):
        """_build_prompt includes the plan file content."""
        plan = tmp_path / "plan.md"
        plan.write_text("Task 1: Implement feature X\nTask 2: Write tests")
        result = _build_prompt("/some/project", str(plan))
        assert "Task 1: Implement feature X" in result
        assert "Task 2: Write tests" in result

    def test_includes_project_directory(self, tmp_path):
        """_build_prompt includes the project directory path."""
        plan = tmp_path / "plan.md"
        plan.write_text("Do stuff")
        result = _build_prompt("/my/project", str(plan))
        assert "/my/project" in result

    def test_includes_rules_section(self, tmp_path):
        """_build_prompt includes the RULES section."""
        plan = tmp_path / "plan.md"
        plan.write_text("Do stuff")
        result = _build_prompt(".", str(plan))
        assert "RULES:" in result
        assert "Do NOT modify pyproject.toml" in result

    def test_includes_success_marker(self, tmp_path):
        """_build_prompt instructs AI to print PLAN-EXEC-DONE."""
        plan = tmp_path / "plan.md"
        plan.write_text("Do stuff")
        result = _build_prompt(".", str(plan))
        assert "PLAN-EXEC-DONE" in result

    def test_empty_plan_file(self, tmp_path):
        """_build_prompt handles an empty plan file."""
        plan = tmp_path / "empty.md"
        plan.write_text("")
        result = _build_prompt(".", str(plan))
        # Should still have the structure, just empty PLAN section
        assert "RULES:" in result
        assert "PROJECT DIRECTORY" in result

    def test_plan_with_special_characters(self, tmp_path):
        """_build_prompt preserves special characters from plan."""
        plan = tmp_path / "special.md"
        plan.write_text("Use `backticks` and 'quotes' and \"dquotes\" and $vars")
        result = _build_prompt(".", str(plan))
        assert "`backticks`" in result
        assert "'quotes'" in result

    def test_nonexistent_plan_file_raises(self, tmp_path):
        """_build_prompt raises FileNotFoundError for missing plan file."""
        with pytest.raises(FileNotFoundError):
            _build_prompt(".", str(tmp_path / "nonexistent.md"))


# ── run_backend tests ────────────────────────────────────────────────


class TestRunBackend:
    """Tests for run_backend(backend, project, prompt_file, output_file)."""

    def _make_backend(self, cmd_return=None):
        """Create a minimal backend dict for testing."""
        return {
            "name": "testbackend",
            "cmd": lambda project, pf: cmd_return or ["echo", "hello"],
            "cwd": lambda project: project,
        }

    def test_success_with_done_marker(self, tmp_path, capsys):
        """run_backend returns True when output contains PLAN-EXEC-DONE."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo PLAN-EXEC-DONE"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is True
        captured = capsys.readouterr()
        assert "succeeded" in captured.out

    def test_success_without_error_in_tail(self, tmp_path, capsys):
        """run_backend returns True when no 'error' in last 200 chars of output."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo 'All good here'"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is True

    def test_failure_nonzero_exit(self, tmp_path, capsys):
        """run_backend returns False on non-zero exit code (not quota)."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo 'something went wrong'; exit 1"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "failed" in captured.out

    def test_quota_error_falls_back(self, tmp_path, capsys):
        """run_backend returns False on 429/quota errors."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo '429 rate limited'; exit 1"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "quota" in captured.out.lower() or "falling back" in captured.out.lower()

    def test_auth_error_chinese_falls_back(self, tmp_path, capsys):
        """run_backend returns False on Chinese auth error (身份验证)."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo '身份验证失败'; exit 1"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "falling back" in captured.out.lower()

    def test_file_not_found(self, tmp_path, capsys):
        """run_backend returns False when backend binary not found."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "nonexistent_tool",
            "cmd": lambda p, pf: ["nonexistent_binary_xyz_123"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "not installed" in captured.out

    def test_timeout(self, tmp_path, capsys):
        """run_backend returns False when backend times out."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "slowbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo started && sleep 60"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        # Patch the timeout to be very short for testing
        with patch.object(_mod["subprocess"], "run", side_effect=_mod["subprocess"].TimeoutExpired(cmd=["test"], timeout=1)):
            result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "timed out" in captured.out

    def test_strips_claudecode_env(self, tmp_path):
        """run_backend removes CLAUDECODE from environment."""
        output_file = tmp_path / "test.log"
        captured_env = {}

        def mock_run(cmd, cwd, env, stdout, stderr, timeout):
            captured_env.update(env)
            result = MagicMock()
            result.returncode = 0
            return result

        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["echo", "test"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("os.environ", {"CLAUDECODE": "1", "PATH": "/usr/bin"}):
            with patch("subprocess.run", side_effect=mock_run):
                run_backend(backend, str(tmp_path), str(plan), output_file)

        assert "CLAUDECODE" not in captured_env

    def test_env_extra_merged(self, tmp_path):
        """run_backend merges env_extra from backend into environment."""
        output_file = tmp_path / "test.log"
        captured_env = {}

        def mock_run(cmd, cwd, env, stdout, stderr, timeout):
            captured_env.update(env)
            result = MagicMock()
            result.returncode = 0
            return result

        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["echo", "test"],
            "cwd": lambda p: p,
            "env_extra": {"CUSTOM_VAR": "custom_value"},
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run", side_effect=mock_run):
            run_backend(backend, str(tmp_path), str(plan), output_file)

        assert captured_env.get("CUSTOM_VAR") == "custom_value"

    def test_output_written_to_file(self, tmp_path):
        """run_backend writes stdout+stderr to the output file."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo 'hello world' && echo PLAN-EXEC-DONE"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        run_backend(backend, str(tmp_path), str(plan), output_file)
        content = output_file.read_text()
        assert "hello world" in content
        assert "PLAN-EXEC-DONE" in content

    def test_completed_with_error_in_tail(self, tmp_path, capsys):
        """run_backend returns False when returncode 0 but 'error' in last 200 chars."""
        output_file = tmp_path / "test.log"
        # Generate output where last 200 chars contain "error"
        long_ok = "x" * 300
        tail_with_error = "something went error at the end"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: [
                "bash", "-c", f"echo '{long_ok}'; echo '{tail_with_error}'",
            ],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()


# ── main() CLI tests ─────────────────────────────────────────────────


class TestMain:
    """Tests for main() CLI entry point."""

    def test_missing_plan_file_exits_1(self, tmp_path, capsys):
        """main exits with 1 when plan file does not exist."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(tmp_path / "nonexistent.md")]):
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "not found" in captured.out.lower()

    def test_dry_run_exits_0(self, tmp_path, capsys):
        """main with --dry-run prints backends and exits 0."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "--dry-run", str(plan)]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "gemini" in captured.out
        assert "codex" in captured.out
        assert "opencode" in captured.out

    def test_dry_run_shows_arrow_chain(self, tmp_path, capsys):
        """--dry-run shows backend chain with arrows."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "--dry-run", str(plan)]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "→" in captured.out or "->" in captured.out

    def test_unknown_backend_exits_1(self, tmp_path, capsys):
        """main exits 1 when --backend specifies unknown backend."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "--backend", "nonexistent", str(plan)]):
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "unknown backend" in captured.err.lower() or "unknown" in captured.out.lower()

    def test_specific_backend_filters_list(self, tmp_path, capsys):
        """main with --backend codex only tries codex."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("sys.argv", ["plan-exec", "--backend", "codex", str(plan)]):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                # The output file won't have PLAN-EXEC-DONE but also no "error"
                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Should have called subprocess.run at least once (for codex)
        if exc_info.value.code == 0:
            mock_run.assert_called_once()

    def test_all_backends_fail_exits_1(self, tmp_path, capsys):
        """main exits 1 when all backends fail."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        # All backends not installed
        with patch("sys.argv", ["plan-exec", str(plan)]):
            with patch("subprocess.run", side_effect=FileNotFoundError("not found")):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "All backends failed" in captured.out or "failed" in captured.out.lower()

    def test_first_backend_succeeds_exits_0(self, tmp_path, capsys):
        """main exits 0 when first backend succeeds."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        def mock_run(cmd, cwd, env, stdout, stderr, timeout):
            # Write PLAN-EXEC-DONE to the output file
            if hasattr(stdout, 'write'):
                stdout.write("PLAN-EXEC-DONE\n")
            result = MagicMock()
            result.returncode = 0
            return result

        with patch("sys.argv", ["plan-exec", str(plan)]):
            with patch("subprocess.run", side_effect=mock_run):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "successfully" in captured.out.lower()

    def test_project_dir_default_is_dot(self, tmp_path, capsys):
        """main defaults project to current directory."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "--dry-run", str(plan)]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "project:" in captured.out.lower()

    def test_custom_project_dir(self, tmp_path, capsys):
        """main uses --project directory when specified."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        proj = tmp_path / "myproject"
        proj.mkdir()
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "--dry-run", "-p", str(proj), str(plan)]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "myproject" in captured.out

    def test_results_dir_created(self, tmp_path, capsys):
        """main creates a timestamped results directory."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        new_results = tmp_path / "cache" / "plan-exec"
        original_results = _mod["RESULTS_DIR"]

        def mock_run(cmd, cwd, env, stdout, stderr, timeout):
            if hasattr(stdout, 'write'):
                stdout.write("PLAN-EXEC-DONE\n")
            result = MagicMock()
            result.returncode = 0
            return result

        try:
            _mod["RESULTS_DIR"] = new_results
            with patch("sys.argv", ["plan-exec", str(plan)]):
                with patch("subprocess.run", side_effect=mock_run):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
        finally:
            _mod["RESULTS_DIR"] = original_results

        assert exc_info.value.code == 0
        assert new_results.exists()

    def test_fallback_from_first_to_second(self, tmp_path, capsys):
        """main falls back from first to second backend on failure."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        call_count = 0

        def mock_run(cmd, cwd, env, stdout, stderr, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First backend fails
                result = MagicMock()
                result.returncode = 1
                return result
            else:
                # Second backend succeeds
                if hasattr(stdout, 'write'):
                    stdout.write("PLAN-EXEC-DONE\n")
                result = MagicMock()
                result.returncode = 0
                return result

        with patch("sys.argv", ["plan-exec", str(plan)]):
            with patch("subprocess.run", side_effect=mock_run):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 0
        assert call_count == 2


# ── Backend cmd lambda tests ─────────────────────────────────────────


class TestBackendCmds:
    """Tests for backend command generation lambdas."""

    def test_gemini_cmd_structure(self, tmp_path):
        """Gemini backend builds correct command structure."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        gemini = BACKENDS[0]
        cmd = gemini["cmd"]("/project", str(plan))
        assert cmd[0] == "gemini"
        assert "-m" in cmd
        assert "gemini-3.1-pro-preview" in cmd
        assert "--yolo" in cmd

    def test_codex_cmd_structure(self, tmp_path):
        """Codex backend builds correct command structure."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        codex = BACKENDS[1]
        cmd = codex["cmd"]("/project", str(plan))
        assert cmd[0] == "codex"
        assert "exec" in cmd
        assert "--full-auto" in cmd
        assert "--sandbox" in cmd

    def test_opencode_cmd_structure(self, tmp_path):
        """OpenCode backend builds correct command structure."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        oc = BACKENDS[2]
        cmd = oc["cmd"]("/project", str(plan))
        assert cmd[0] == "opencode"
        assert "run" in cmd

    def test_codex_skips_git_check(self, tmp_path):
        """Codex backend includes --skip-git-repo-check."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        codex = BACKENDS[1]
        cmd = codex["cmd"]("/project", str(plan))
        assert "--skip-git-repo-check" in cmd

    def test_opencode_uses_env_model(self, tmp_path):
        """OpenCode backend reads OPENCODE_MODEL from environment."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        oc = BACKENDS[2]
        with patch.dict(os.environ, {"OPENCODE_MODEL": "custom-model"}):
            cmd = oc["cmd"]("/project", str(plan))
        assert "custom-model" in cmd

    def test_backend_cwd_returns_project(self, tmp_path):
        """Each backend's cwd lambda returns the project directory."""
        for b in BACKENDS:
            assert b["cwd"]("/my/project") == "/my/project"

    def test_opencode_title_format(self, tmp_path):
        """OpenCode backend generates a title with plan-exec prefix."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        oc = BACKENDS[2]
        cmd = oc["cmd"]("/project", str(plan))
        # Find the --title argument
        title_idx = cmd.index("--title")
        title = cmd[title_idx + 1]
        assert title.startswith("plan-exec-")


# ── Edge case tests ──────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for plan-exec."""

    def test_build_prompt_with_multiline_plan(self, tmp_path):
        """_build_prompt handles multiline plan content."""
        plan = tmp_path / "plan.md"
        plan.write_text("Line 1\nLine 2\nLine 3\n\nLine 5")
        result = _build_prompt(".", str(plan))
        assert "Line 1" in result
        assert "Line 5" in result

    def test_build_prompt_with_unicode(self, tmp_path):
        """_build_prompt preserves unicode characters."""
        plan = tmp_path / "plan.md"
        plan.write_text("Implement features for 日本語 and 中文")
        result = _build_prompt(".", str(plan))
        assert "日本語" in result
        assert "中文" in result

    def test_run_backend_writes_output_file_even_on_failure(self, tmp_path):
        """run_backend creates the output file even when backend fails."""
        output_file = tmp_path / "fail.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo 'error output'; exit 1"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        run_backend(backend, str(tmp_path), str(plan), output_file)
        assert output_file.exists()
        content = output_file.read_text()
        assert "error output" in content

    def test_backends_fallback_order_preserved(self):
        """BACKENDS maintains gemini → codex → opencode order."""
        names = [b["name"] for b in BACKENDS]
        assert names.index("gemini") < names.index("codex") < names.index("opencode")

    def test_quota_keyword_triggers_fallback(self, tmp_path, capsys):
        """run_backend falls back on 'quota' in output."""
        output_file = tmp_path / "test.log"
        backend = {
            "name": "testbackend",
            "cmd": lambda p, pf: ["bash", "-c", "echo 'quota exceeded'; exit 1"],
            "cwd": lambda p: p,
        }
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        result = run_backend(backend, str(tmp_path), str(plan), output_file)
        assert result is False
        captured = capsys.readouterr()
        assert "quota" in captured.out.lower()

    def test_build_prompt_includes_commit_instruction(self, tmp_path):
        """_build_prompt includes instruction to commit work."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        result = _build_prompt(".", str(plan))
        assert "ommit" in result.lower()  # matches "commit"

    def test_build_prompt_includes_no_stubs_instruction(self, tmp_path):
        """_build_prompt includes instruction against stubs/TODOs."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        result = _build_prompt(".", str(plan))
        assert "stub" in result.lower() or "no stub" in result.lower()

    def test_main_with_absolute_plan_path(self, tmp_path, capsys):
        """main resolves plan file to absolute path."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        abs_path = str(plan.resolve())

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "--dry-run", abs_path]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert abs_path in captured.out
