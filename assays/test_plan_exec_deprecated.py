from __future__ import annotations

"""Tests for plan-exec.deprecated — AI plan executor with fallback chain."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_plan_exec():
    """Load the plan-exec.deprecated module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/plan-exec.deprecated").read()
    ns: dict = {"__name__": "plan_exec"}
    exec(source, ns)
    return ns


_mod = _load_plan_exec()
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
BACKENDS = _mod["BACKENDS"]
RESULTS_DIR = _mod["RESULTS_DIR"]


# ── _build_prompt tests ─────────────────────────────────────────────────


def test_build_prompt_reads_plan_file(tmp_path):
    """_build_prompt reads and includes plan file content."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("## Task 1\nImplement feature X\n")
    
    prompt = _build_prompt("/project", str(plan_file))
    
    assert "## Task 1" in prompt
    assert "Implement feature X" in prompt


def test_build_prompt_includes_project_directory(tmp_path):
    """_build_prompt includes project directory in prompt."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task content")
    
    prompt = _build_prompt("/my/project", str(plan_file))
    
    assert "PROJECT DIRECTORY: /my/project" in prompt


def test_build_prompt_includes_rules(tmp_path):
    """_build_prompt includes execution rules."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    
    prompt = _build_prompt("/project", str(plan_file))
    
    assert "Do NOT modify pyproject.toml" in prompt
    assert "no stubs" in prompt
    assert "no TODO" in prompt
    assert "Run tests after implementation" in prompt


def test_build_prompt_includes_success_marker(tmp_path):
    """_build_prompt includes PLAN-EXEC-DONE marker for success detection."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    
    prompt = _build_prompt("/project", str(plan_file))
    
    assert "PLAN-EXEC-DONE" in prompt


# ── BACKENDS structure tests ───────────────────────────────────────────────


def test_backends_has_three_entries():
    """BACKENDS contains gemini, codex, opencode in order."""
    assert len(BACKENDS) == 3
    assert BACKENDS[0]["name"] == "gemini"
    assert BACKENDS[1]["name"] == "codex"
    assert BACKENDS[2]["name"] == "opencode"


def test_backends_have_required_keys():
    """Each backend has name, cmd, and cwd keys."""
    for backend in BACKENDS:
        assert "name" in backend
        assert "cmd" in backend
        assert "cwd" in backend
        assert callable(backend["cmd"])
        assert callable(backend["cwd"])


def test_gemini_backend_command():
    """Gemini backend builds correct command."""
    backend = BACKENDS[0]
    with patch.object(_mod["Path"], "read_text", return_value="plan content"):
        cmd = backend["cmd"]("/project", "/plan.md")
    
    assert cmd[0] == "gemini"
    assert "-m" in cmd
    assert "gemini-3.1-pro-preview" in cmd
    assert "--yolo" in cmd


def test_codex_backend_command():
    """Codex backend builds correct command."""
    backend = BACKENDS[1]
    with patch.object(_mod["Path"], "read_text", return_value="plan content"):
        cmd = backend["cmd"]("/project", "/plan.md")
    
    assert cmd[0] == "codex"
    assert "exec" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "--sandbox" in cmd
    assert "danger-full-access" in cmd
    assert "--full-auto" in cmd


def test_opencode_backend_command():
    """Opencode backend builds correct command."""
    backend = BACKENDS[2]
    with patch.object(_mod["Path"], "read_text", return_value="plan content"):
        with patch.dict(os.environ, {"OPENCODE_MODEL": "test-model"}):
            cmd = backend["cmd"]("/project", "/plan.md")
    
    assert cmd[0] == "opencode"
    assert "run" in cmd
    assert "-m" in cmd
    assert "test-model" in cmd


def test_opencode_backend_default_model():
    """Opencode backend uses default model if OPENCODE_MODEL not set."""
    backend = BACKENDS[2]
    with patch.object(_mod["Path"], "read_text", return_value="plan content"):
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENCODE_MODEL if set
            os.environ.pop("OPENCODE_MODEL", None)
            cmd = backend["cmd"]("/project", "/plan.md")
    
    assert "opencode/glm-5" in cmd


def test_opencode_backend_env_extra():
    """Opencode backend sets OPENCODE_HOME env var."""
    backend = BACKENDS[2]
    assert "env_extra" in backend
    assert "OPENCODE_HOME" in backend["env_extra"]
    assert ".opencode-lean" in backend["env_extra"]["OPENCODE_HOME"]


def test_backend_cwd_returns_project():
    """All backends' cwd function returns the project directory."""
    for backend in BACKENDS:
        assert backend["cwd"]("/my/project") == "/my/project"


# ── run_backend tests ───────────────────────────────────────────────────────


def test_run_backend_success_on_exit_0(tmp_path, capsys):
    """run_backend returns True when subprocess exits 0."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["echo", "PLAN-EXEC-DONE"],
        "cwd": lambda p: p,
    }
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_backend(backend, "/project", str(plan_file), output_file)
    
    assert result is True


def test_run_backend_detects_quota_error(tmp_path, capsys):
    """run_backend returns False and detects quota errors (429)."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    output_file.write_text("Error 429: quota exceeded")
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["test"],
        "cwd": lambda p: p,
    }
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = run_backend(backend, "/project", str(plan_file), output_file)
    
    assert result is False


def test_run_backend_detects_auth_error(tmp_path, capsys):
    """run_backend returns False for auth errors (身份验证)."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    output_file.write_text("身份验证失败")
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["test"],
        "cwd": lambda p: p,
    }
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = run_backend(backend, "/project", str(plan_file), output_file)
    
    assert result is False


def test_run_backend_handles_timeout(tmp_path, capsys):
    """run_backend returns False on timeout."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["sleep", "999"],
        "cwd": lambda p: p,
    }
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = _mod["subprocess"].TimeoutExpired(cmd=["test"], timeout=600)
        result = run_backend(backend, "/project", str(plan_file), output_file)
    
    assert result is False


def test_run_backend_handles_not_installed(tmp_path, capsys):
    """run_backend returns False when command not found."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["nonexistent-command-xyz"],
        "cwd": lambda p: p,
    }
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = run_backend(backend, "/project", str(plan_file), output_file)
    
    assert result is False


def test_run_backend_writes_output_to_file(tmp_path):
    """run_backend writes stdout to output file."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["echo", "test output"],
        "cwd": lambda p: p,
    }
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Actually write to the file during mock
        def side_effect(*args, **kwargs):
            if "stdout" in kwargs and kwargs["stdout"] != _mod["subprocess"].PIPE:
                kwargs["stdout"].write(b"test output\n")
            return MagicMock(returncode=0)
        mock_run.side_effect = side_effect
        run_backend(backend, "/project", str(plan_file), output_file)
    
    # Output file should have been created
    assert output_file.exists()


def test_run_backend_strips_claudcode_env(tmp_path):
    """run_backend removes CLAUDECODE from environment to avoid nesting."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["echo"],
        "cwd": lambda p: p,
    }
    
    captured_env = {}
    
    def capture_env(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        return MagicMock(returncode=0)
    
    with patch.dict(os.environ, {"CLAUDECODE": "some-value"}):
        with patch("subprocess.run", side_effect=capture_env):
            run_backend(backend, "/project", str(plan_file), output_file)
    
    assert "CLAUDECODE" not in captured_env


def test_run_backend_includes_env_extra(tmp_path):
    """run_backend adds env_extra to subprocess environment."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Task")
    output_file = tmp_path / "output.log"
    
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["echo"],
        "cwd": lambda p: p,
        "env_extra": {"CUSTOM_VAR": "custom_value"},
    }
    
    captured_env = {}
    
    def capture_env(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        return MagicMock(returncode=0)
    
    with patch("subprocess.run", side_effect=capture_env):
        run_backend(backend, "/project", str(plan_file), output_file)
    
    assert captured_env.get("CUSTOM_VAR") == "custom_value"


# ── CLI integration tests ───────────────────────────────────────────────────


def test_cli_missing_plan_file(tmp_path):
    """CLI exits 1 when plan file does not exist."""
    result = _mod["subprocess"].run(
        ["uv", "run", "python", "/home/terry/germline/effectors/plan-exec.deprecated",
         "/nonexistent/plan.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()


def test_cli_dry_run_exits_0(tmp_path):
    """CLI with --dry-run exits 0 without running backends."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test task")
    
    result = _mod["subprocess"].run(
        ["uv", "run", "python", "/home/terry/germline/effectors/plan-exec.deprecated",
         str(plan_file), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Would try" in result.stdout


def test_cli_dry_run_shows_backend_chain(tmp_path):
    """CLI --dry-run shows the fallback chain."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test task")
    
    result = _mod["subprocess"].run(
        ["uv", "run", "python", "/home/terry/germline/effectors/plan-exec.deprecated",
         str(plan_file), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert "gemini" in result.stdout
    assert "codex" in result.stdout
    assert "opencode" in result.stdout


def test_cli_project_flag(tmp_path):
    """CLI --project flag sets project directory."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test task")
    
    result = _mod["subprocess"].run(
        ["uv", "run", "python", "/home/terry/germline/effectors/plan-exec.deprecated",
         str(plan_file), "--project", "/custom/project", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "/custom/project" in result.stdout


def test_cli_invalid_backend(tmp_path):
    """CLI exits 1 for unknown --backend value."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test task")
    
    result = _mod["subprocess"].run(
        ["uv", "run", "python", "/home/terry/germline/effectors/plan-exec.deprecated",
         str(plan_file), "--backend", "nonexistent"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "unknown backend" in result.stderr.lower()


# ── Edge case tests ─────────────────────────────────────────────────────────


class TestBuildPromptEdgeCases:
    """Edge cases for _build_prompt."""

    def test_empty_plan_file(self, tmp_path):
        """_build_prompt handles empty plan file."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("")
        
        prompt = _build_prompt("/project", str(plan_file))
        
        assert "PROJECT DIRECTORY:" in prompt
        assert "PLAN:" in prompt

    def test_plan_file_with_unicode(self, tmp_path):
        """_build_prompt handles unicode content."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("## 任务\n实现功能 🚀\n")
        
        prompt = _build_prompt("/project", str(plan_file))
        
        assert "任务" in prompt
        assert "🚀" in prompt

    def test_plan_file_with_special_chars(self, tmp_path):
        """_build_prompt handles special characters."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Task: `code` and $VAR and 'quotes'\n")
        
        prompt = _build_prompt("/project", str(plan_file))
        
        assert "`code`" in prompt
        assert "$VAR" in prompt
        assert "'quotes'" in prompt


class TestRunBackendEdgeCases:
    """Edge cases for run_backend."""

    def test_output_file_created_if_missing(self, tmp_path):
        """run_backend creates output file even if it doesn't exist."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Task")
        output_file = tmp_path / "subdir" / "output.log"
        
        backend = {
            "name": "test",
            "cmd": lambda p, f: ["echo"],
            "cwd": lambda p: p,
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # The real run_backend opens the file for writing
            # We need to let it actually write
            def do_write(*args, **kwargs):
                f = kwargs.get("stdout")
                if f and hasattr(f, "write"):
                    f.write(b"output\n")
                return MagicMock(returncode=0)
            mock_run.side_effect = do_write
            run_backend(backend, "/project", str(plan_file), output_file)

    def test_success_without_marker_but_no_errors(self, tmp_path):
        """run_backend succeeds on exit 0 even without PLAN-EXEC-DONE if no errors."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Task")
        output_file = tmp_path / "output.log"
        output_file.write_text("All good, no errors here")
        
        backend = {
            "name": "test",
            "cmd": lambda p, f: ["echo"],
            "cwd": lambda p: p,
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = run_backend(backend, "/project", str(plan_file), output_file)
        
        assert result is True

    def test_failure_with_error_in_last_200_chars(self, tmp_path):
        """run_backend fails if exit 0 but 'error' in last 200 chars."""
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("Task")
        output_file = tmp_path / "output.log"
        # Put error in last 200 chars
        output_file.write_text("x" * 500 + "error occurred")
        
        backend = {
            "name": "test",
            "cmd": lambda p, f: ["echo"],
            "cwd": lambda p: p,
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = run_backend(backend, "/project", str(plan_file), output_file)
        
        assert result is False


class TestBackendsEdgeCases:
    """Edge cases for BACKENDS configuration."""

    def test_backends_are_ordered_correctly(self):
        """BACKENDS has correct fallback order."""
        names = [b["name"] for b in BACKENDS]
        assert names == ["gemini", "codex", "opencode"]

    def test_all_backends_have_callable_cmd(self):
        """All backends have callable cmd functions."""
        for backend in BACKENDS:
            assert callable(backend["cmd"])

    def test_all_backends_have_callable_cwd(self):
        """All backends have callable cwd functions."""
        for backend in BACKENDS:
            assert callable(backend["cwd"])


# ── RESULTS_DIR constant tests ─────────────────────────────────────────────


def test_results_dir_is_in_cache():
    """RESULTS_DIR is under ~/.cache/plan-exec."""
    assert ".cache" in str(RESULTS_DIR)
    assert "plan-exec" in str(RESULTS_DIR)


def test_results_dir_uses_home():
    """RESULTS_DIR uses Path.home() for user's home directory."""
    # RESULTS_DIR should be an absolute path
    assert RESULTS_DIR.is_absolute()
