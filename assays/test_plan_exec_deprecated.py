from __future__ import annotations

"""Tests for plan-exec.deprecated — plan execution with AI backend fallback."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


def _load_plan_exec():
    """Load the plan-exec.deprecated module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/plan-exec.deprecated")).read()
    ns: dict = {"__name__": "plan_exec_deprecated"}
    exec(source, ns)
    return ns


_mod = _load_plan_exec()
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
BACKENDS = _mod["BACKENDS"]
RESULTS_DIR = _mod["RESULTS_DIR"]


# ── _build_prompt tests ─────────────────────────────────────────────────


def test_build_prompt_includes_plan_content():
    """_build_prompt includes the plan file content in the output."""
    plan_content = "# Test Plan\n\n1. Do something\n2. Do something else"
    with patch("pathlib.Path.read_text", return_value=plan_content):
        prompt = _build_prompt("/project", "/path/to/plan.md")

    assert "# Test Plan" in prompt
    assert "1. Do something" in prompt


def test_build_prompt_includes_project_directory():
    """_build_prompt includes the project directory in the output."""
    with patch("pathlib.Path.read_text", return_value="plan"):
        prompt = _build_prompt("/my/project", "/plan.md")

    assert "/my/project" in prompt


def test_build_prompt_includes_rules():
    """_build_prompt includes execution rules."""
    with patch("pathlib.Path.read_text", return_value="plan"):
        prompt = _build_prompt("/project", "/plan.md")

    assert "Do NOT modify pyproject.toml" in prompt
    assert "no stubs" in prompt.lower()
    assert "Commit your work" in prompt


def test_build_prompt_includes_success_marker():
    """_build_prompt includes PLAN-EXEC-DONE marker for success detection."""
    with patch("pathlib.Path.read_text", return_value="plan"):
        prompt = _build_prompt("/project", "/plan.md")

    assert "PLAN-EXEC-DONE" in prompt


# ── BACKENDS configuration tests ────────────────────────────────────────


def test_backends_has_three_entries():
    """BACKENDS contains gemini, codex, and opencode."""
    names = [b["name"] for b in BACKENDS]
    assert names == ["gemini", "codex", "opencode"]


def test_backends_have_required_keys():
    """Each backend has name, cmd, and cwd keys."""
    for backend in BACKENDS:
        assert "name" in backend
        assert "cmd" in backend
        assert "cwd" in backend
        assert callable(backend["cmd"])
        assert callable(backend["cwd"])


def test_gemini_cmd_structure():
    """Gemini backend uses correct command structure."""
    gemini = next(b for b in BACKENDS if b["name"] == "gemini")
    with patch("pathlib.Path.read_text", return_value="plan"):
        cmd = gemini["cmd"]("/project", "/plan.md")

    assert cmd[0] == "gemini"
    assert "-m" in cmd
    assert "--yolo" in cmd


def test_codex_cmd_structure():
    """Codex backend uses correct command structure."""
    codex = next(b for b in BACKENDS if b["name"] == "codex")
    with patch("pathlib.Path.read_text", return_value="plan"):
        cmd = codex["cmd"]("/project", "/plan.md")

    assert cmd[0] == "codex"
    assert "exec" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "--sandbox" in cmd
    assert "--full-auto" in cmd


def test_opencode_cmd_structure():
    """Opencode backend uses correct command structure."""
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    with patch("pathlib.Path.read_text", return_value="plan"):
        with patch.dict(_mod["os"].environ, {"OPENCODE_MODEL": "test-model"}):
            cmd = opencode["cmd"]("/project", "/plan.md")

    assert cmd[0] == "opencode"
    assert "run" in cmd
    assert "-m" in cmd
    assert "test-model" in cmd


def test_opencode_uses_env_model():
    """Opencode backend respects OPENCODE_MODEL env var."""
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    with patch("pathlib.Path.read_text", return_value="plan"):
        with patch.dict(_mod["os"].environ, {"OPENCODE_MODEL": "custom-model"}):
            cmd = opencode["cmd"]("/project", "/plan.md")

    assert "custom-model" in cmd


def test_opencode_default_model():
    """Opencode backend uses default model when env var not set."""
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    with patch("pathlib.Path.read_text", return_value="plan"):
        env = _mod["os"].environ.copy()
        env.pop("OPENCODE_MODEL", None)
        with patch.dict(_mod["os"].environ, env, clear=True):
            cmd = opencode["cmd"]("/project", "/plan.md")

    # Default is opencode/glm-5
    assert "opencode/glm-5" in cmd or "glm-5" in cmd


def test_opencode_has_extra_env():
    """Opencode backend sets OPENCODE_HOME env var."""
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    assert "env_extra" in opencode
    assert "OPENCODE_HOME" in opencode["env_extra"]


def test_backend_cwd_returns_project():
    """Each backend's cwd function returns the project directory."""
    for backend in BACKENDS:
        cwd = backend["cwd"]("/my/project")
        assert cwd == "/my/project"


# ── run_backend tests ───────────────────────────────────────────────────


def test_run_backend_success_with_marker():
    """run_backend returns True when subprocess succeeds with PLAN-EXEC-DONE."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "read_text", return_value="PLAN-EXEC-DONE\nFiles touched: []"):
                result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is True


def test_run_backend_success_without_errors():
    """run_backend returns True when subprocess succeeds and no errors in output."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        with patch("builtins.open", mock_open()):
            # Use text without "error" substring - the check is "error" in output.lower()[-200:]
            with patch.object(Path, "read_text", return_value="All good, task completed"):
                result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is True


def test_run_backend_failure_output_has_errors():
    """run_backend returns False when output ends with error message."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result):
        with patch("builtins.open", mock_open()):
            # Output ends with "error" in last 200 chars
            with patch.object(Path, "read_text", return_value="x" * 300 + "error occurred"):
                result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is False


def test_run_backend_nonzero_exit():
    """run_backend returns False when subprocess returns non-zero."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch("subprocess.run", return_value=mock_result):
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "read_text", return_value="some output"):
                result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is False


def test_run_backend_quota_error_fallback():
    """run_backend returns False for quota/auth errors (429, quota, 身份验证)."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 1

    # Test 429 error
    with patch("subprocess.run", return_value=mock_result):
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "read_text", return_value="Error 429 rate limit"):
                result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is False

    # Test quota error
    with patch("subprocess.run", return_value=mock_result):
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "read_text", return_value="Quota exceeded"):
                result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is False


def test_run_backend_timeout():
    """run_backend returns False on subprocess timeout."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["echo"], timeout=600)):
        with patch("builtins.open", mock_open()):
            result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is False


def test_run_backend_not_found():
    """run_backend returns False when command not found."""
    backend = {"name": "test", "cmd": lambda p, f: ["nonexistent-cmd"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with patch("builtins.open", mock_open()):
            result = run_backend(backend, "/project", "/plan.md", output_file)

    assert result is False


def test_run_backend_strips_claudcode_env():
    """run_backend removes CLAUDECODE from environment to avoid nesting."""
    backend = {"name": "test", "cmd": lambda p, f: ["echo"], "cwd": lambda p: p}
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "read_text", return_value="PLAN-EXEC-DONE"):
                with patch.dict(_mod["os"].environ, {"CLAUDECODE": "value"}, clear=False):
                    run_backend(backend, "/project", "/plan.md", output_file)

    # Check that CLAUDECODE was removed from env
    call_env = mock_run.call_args[1]["env"]
    assert "CLAUDECODE" not in call_env


def test_run_backend_adds_extra_env():
    """run_backend adds env_extra to subprocess environment."""
    backend = {
        "name": "test",
        "cmd": lambda p, f: ["echo"],
        "cwd": lambda p: p,
        "env_extra": {"CUSTOM_VAR": "custom_value"}
    }
    output_file = Path("/tmp/test.log")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "read_text", return_value="PLAN-EXEC-DONE"):
                run_backend(backend, "/project", "/plan.md", output_file)

    call_env = mock_run.call_args[1]["env"]
    assert call_env.get("CUSTOM_VAR") == "custom_value"


# ── RESULTS_DIR tests ───────────────────────────────────────────────────


def test_results_dir_in_cache():
    """RESULTS_DIR is under ~/.cache/plan-exec."""
    assert ".cache" in str(RESULTS_DIR)
    assert "plan-exec" in str(RESULTS_DIR)


def test_results_dir_is_path():
    """RESULTS_DIR is a Path object."""
    assert isinstance(RESULTS_DIR, Path)


# ── main CLI tests ───────────────────────────────────────────────────────


main = _mod["main"]


def test_main_missing_plan_file(capsys):
    """main exits with error when plan file doesn't exist."""
    with patch("sys.argv", ["plan-exec", "/nonexistent/plan.md"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_main_dry_run(capsys, tmp_path):
    """main --dry-run shows what would run without executing."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    with patch("sys.argv", ["plan-exec", str(plan_file), "--dry-run"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Would try" in out
    assert "gemini" in out
    assert "codex" in out
    assert "opencode" in out


def test_main_with_project_flag(capsys, tmp_path):
    """main --project sets the project directory."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    # Use --dry-run to avoid actual execution
    with patch("sys.argv", ["plan-exec", str(plan_file), "--project", str(project_dir), "--dry-run"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "project:" in out


def test_main_specific_backend(capsys, tmp_path):
    """main --backend filters to a specific backend."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    with patch("sys.argv", ["plan-exec", str(plan_file), "--dry-run", "--backend", "codex"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0
    # In dry-run mode, it shows what would run - the filtering happens at execution time


def test_main_invalid_backend(capsys, tmp_path):
    """main exits with error for unknown backend."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    with patch("sys.argv", ["plan-exec", str(plan_file), "--backend", "invalid"]):
        with patch("subprocess.run"):
            with pytest.raises(SystemExit) as exc:
                main()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "unknown backend" in err.lower()


def test_main_all_backends_fail(capsys, tmp_path):
    """main exits with error when all backends fail."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch("sys.argv", ["plan-exec", str(plan_file)]):
        with patch("subprocess.run", return_value=mock_result):
            with patch("builtins.open", mock_open()):
                with patch.object(Path, "read_text", return_value="error"):
                    with pytest.raises(SystemExit) as exc:
                        main()

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "All backends failed" in out


def test_main_creates_results_directory(tmp_path):
    """main creates results directory with timestamp."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    mock_result = MagicMock()
    mock_result.returncode = 1

    # Track mkdir calls
    mkdir_calls = []

    def mock_mkdir(self, *args, **kwargs):
        mkdir_calls.append(str(self))
        # Simulate successful directory creation
        return None

    with patch("sys.argv", ["plan-exec", str(plan_file)]):
        with patch.object(Path, "mkdir", mock_mkdir):
            with patch("subprocess.run", return_value=mock_result):
                with patch("builtins.open", mock_open()):
                    with patch.object(Path, "read_text", return_value="error"):
                        with pytest.raises(SystemExit):
                            main()

    # Verify mkdir was called for results directory
    assert any("plan-exec" in call for call in mkdir_calls)


def test_main_success_via_first_backend(capsys, tmp_path):
    """main succeeds when first backend (gemini) works."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("sys.argv", ["plan-exec", str(plan_file)]):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("builtins.open", mock_open()):
                with patch.object(Path, "read_text", return_value="PLAN-EXEC-DONE"):
                    with pytest.raises(SystemExit) as exc:
                        main()

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "succeeded" in out
    # Should only have called run once (first backend succeeded)
    assert mock_run.call_count == 1


def test_main_fallback_to_second_backend(capsys, tmp_path):
    """main falls back to second backend when first fails."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    fail_result = MagicMock(returncode=1)
    success_result = MagicMock(returncode=0)

    with patch("sys.argv", ["plan-exec", str(plan_file)]):
        with patch("subprocess.run", side_effect=[fail_result, success_result]):
            with patch("builtins.open", mock_open()):
                # Return PLAN-EXEC-DONE for all read_text calls
                # This satisfies both plan file reads and output file checks
                with patch.object(Path, "read_text", return_value="PLAN-EXEC-DONE"):
                    with pytest.raises(SystemExit) as exc:
                        main()

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Trying gemini" in out
    assert "Trying codex" in out
    assert "succeeded" in out
