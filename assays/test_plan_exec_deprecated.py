from __future__ import annotations

"""Tests for plan-exec.deprecated — execute plan docs with AI backend fallback."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ── _build_prompt tests ─────────────────────────────────────────────


def test_build_prompt_includes_project_directory():
    """_build_prompt includes the project directory in the prompt."""
    plan_file = Path(__file__).parent / "test_plan_exec_sample.md"
    plan_file.write_text("# Sample Plan\n\n- [ ] Task 1\n- [ ] Task 2\n")

    try:
        prompt = _build_prompt("/my/project", str(plan_file))
        assert "PROJECT DIRECTORY: /my/project" in prompt
    finally:
        plan_file.unlink()


def test_build_prompt_includes_plan_content():
    """_build_prompt includes the plan content in the prompt."""
    plan_file = Path(__file__).parent / "test_plan_exec_sample.md"
    plan_file.write_text("# My Plan\n\nDo something important.\n")

    try:
        prompt = _build_prompt("/project", str(plan_file))
        assert "# My Plan" in prompt
        assert "Do something important" in prompt
    finally:
        plan_file.unlink()


def test_build_prompt_includes_rules():
    """_build_prompt includes execution rules in the prompt."""
    plan_file = Path(__file__).parent / "test_plan_exec_sample.md"
    plan_file.write_text("plan content\n")

    try:
        prompt = _build_prompt("/project", str(plan_file))
        assert "RULES:" in prompt
        assert "Do NOT modify pyproject.toml" in prompt
        assert "no stubs" in prompt
        assert "PLAN-EXEC-DONE" in prompt
    finally:
        plan_file.unlink()


# ── run_backend tests ───────────────────────────────────────────────


def test_run_backend_success_with_marker(tmp_path):
    """run_backend returns True when output contains PLAN-EXEC-DONE."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["echo", "PLAN-EXEC-DONE"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is True
    assert "PLAN-EXEC-DONE" in output_file.read_text()


def test_run_backend_success_no_error_in_output(tmp_path):
    """run_backend returns True when exit 0 and no 'error' in last 200 chars."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["echo", "All done successfully"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is True


def test_run_backend_failure_nonzero_exit(tmp_path, capsys):
    """run_backend returns False when subprocess returns non-zero exit code."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["sh", "-c", "echo 'failed'; exit 1"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is False
    captured = capsys.readouterr()
    assert "failed" in captured.out


def test_run_backend_failure_with_error_in_output(tmp_path, capsys):
    """run_backend returns False when exit 0 but output ends with 'error'."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    # Create output that ends with 'error' (within last 200 chars)
    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["sh", "-c", "echo 'some output'; echo 'error occurred'"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is False
    captured = capsys.readouterr()
    assert "output suggests errors" in captured.out


def test_run_backend_quota_error_fallback(tmp_path, capsys):
    """run_backend returns False and reports quota error when 429 in output."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["sh", "-c", "echo 'HTTP 429 rate limit'; exit 1"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is False
    captured = capsys.readouterr()
    assert "quota/auth error" in captured.out


def test_run_backend_auth_error_chinese(tmp_path, capsys):
    """run_backend detects Chinese auth error message."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["sh", "-c", "echo '身份验证失败'; exit 1"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is False
    captured = capsys.readouterr()
    assert "quota/auth error" in captured.out


def test_run_backend_timeout(tmp_path, capsys):
    """run_backend returns False when subprocess times out."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["sleep", "7200"],  # Would timeout if not mocked
        "cwd": lambda p: tmp_path,
    }

    # Mock subprocess.run to raise TimeoutExpired
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep", "7200"], timeout=600)
        result = run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert result is False
    captured = capsys.readouterr()
    assert "timed out" in captured.out


def test_run_backend_not_installed(tmp_path, capsys):
    """run_backend returns False when backend command not found."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    backend = {
        "name": "nonexistent_backend",
        "cmd": lambda p, f: ["this_command_does_not_exist_12345"],
        "cwd": lambda p: tmp_path,
    }

    result = run_backend(backend, str(tmp_path), str(plan_file), output_file)
    assert result is False
    captured = capsys.readouterr()
    assert "not installed" in captured.out


def test_run_backend_env_extra(tmp_path):
    """run_backend adds env_extra to subprocess environment."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    captured_env = {}

    def mock_run(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        result = MagicMock()
        result.returncode = 0
        return result

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["echo", "test"],
        "cwd": lambda p: tmp_path,
        "env_extra": {"CUSTOM_VAR": "custom_value"},
    }

    with patch("subprocess.run", side_effect=mock_run):
        run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert captured_env.get("CUSTOM_VAR") == "custom_value"


def test_run_backend_strips_claudedcode(tmp_path):
    """run_backend removes CLAUDECODE from environment to avoid nesting."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    output_file = tmp_path / "output.log"

    captured_env = {}

    def mock_run(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        result = MagicMock()
        result.returncode = 0
        return result

    backend = {
        "name": "test_backend",
        "cmd": lambda p, f: ["echo", "test"],
        "cwd": lambda p: tmp_path,
    }

    with patch.dict("os.environ", {"CLAUDECODE": "some_value"}):
        with patch("subprocess.run", side_effect=mock_run):
            run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert "CLAUDECODE" not in captured_env


# ── BACKENDS configuration tests ─────────────────────────────────────


def test_backends_has_gemini():
    """BACKENDS includes gemini backend."""
    names = [b["name"] for b in BACKENDS]
    assert "gemini" in names


def test_backends_has_codex():
    """BACKENDS includes codex backend."""
    names = [b["name"] for b in BACKENDS]
    assert "codex" in names


def test_backends_has_opencode():
    """BACKENDS includes opencode backend."""
    names = [b["name"] for b in BACKENDS]
    assert "opencode" in names


def test_backends_order():
    """BACKENDS are in expected fallback order: gemini, codex, opencode."""
    names = [b["name"] for b in BACKENDS]
    assert names == ["gemini", "codex", "opencode"]


def test_backends_all_have_required_keys():
    """Each backend has name, cmd, and cwd keys."""
    for backend in BACKENDS:
        assert "name" in backend
        assert "cmd" in backend
        assert "cwd" in backend


# ── RESULTS_DIR tests ────────────────────────────────────────────────


def test_results_dir_under_cache():
    """RESULTS_DIR is under ~/.cache/plan-exec."""
    assert ".cache" in str(RESULTS_DIR)
    assert "plan-exec" in str(RESULTS_DIR)


# ── CLI tests via subprocess ──────────────────────────────────────────


def test_cli_missing_plan_file(tmp_path):
    """CLI exits with error when plan file does not exist."""
    result = subprocess.run(
        [
            str(Path.home() / "germline/effectors/plan-exec.deprecated"),
            "/nonexistent/plan.md",
            "--project",
            str(tmp_path.resolve()),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "plan file not found" in result.stderr


def test_cli_dry_run(tmp_path):
    """CLI --dry-run shows what would run without executing."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    result = subprocess.run(
        [
            str(Path.home() / "germline/effectors/plan-exec.deprecated"),
            str(plan_file.resolve()),
            "--project",
            str(tmp_path.resolve()),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Would try" in result.stdout
    assert "gemini" in result.stdout


def test_cli_unknown_backend(tmp_path):
    """CLI exits with error when --backend is unknown."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    result = subprocess.run(
        [
            str(Path.home() / "germline/effectors/plan-exec.deprecated"),
            str(plan_file.resolve()),
            "--project",
            str(tmp_path.resolve()),
            "--backend",
            "unknown_backend",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "unknown backend" in result.stderr


def test_cli_project_argument(tmp_path):
    """CLI respects --project argument."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    result = subprocess.run(
        [
            str(Path.home() / "germline/effectors/plan-exec.deprecated"),
            str(plan_file.resolve()),
            "--project",
            str(project_dir.resolve()),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(project_dir) in result.stdout or "project:" in result.stdout


def test_cli_short_options(tmp_path):
    """CLI short options -p work."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    result = subprocess.run(
        [
            str(Path.home() / "germline/effectors/plan-exec.deprecated"),
            str(plan_file.resolve()),
            "-p",
            str(project_dir.resolve()),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


# ── Integration: backend command structure tests ──────────────────────


def test_gemini_backend_cmd_structure(tmp_path):
    """Gemini backend command has expected structure."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    gemini = next(b for b in BACKENDS if b["name"] == "gemini")
    cmd = gemini["cmd"](str(tmp_path), str(plan_file))

    assert cmd[0] == "gemini"
    assert "-m" in cmd
    assert "--yolo" in cmd


def test_codex_backend_cmd_structure(tmp_path):
    """Codex backend command has expected structure."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    codex = next(b for b in BACKENDS if b["name"] == "codex")
    cmd = codex["cmd"](str(tmp_path), str(plan_file))

    assert cmd[0] == "codex"
    assert "exec" in cmd
    assert "--full-auto" in cmd


def test_opencode_backend_cmd_structure(tmp_path):
    """Opencode backend command has expected structure."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("test plan")

    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    cmd = opencode["cmd"](str(tmp_path), str(plan_file))

    assert cmd[0] == "opencode"
    assert "run" in cmd


def test_opencode_backend_env_extra():
    """Opencode backend sets OPENCODE_HOME env var."""
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    assert "env_extra" in opencode
    assert "OPENCODE_HOME" in opencode["env_extra"]
    assert ".opencode-lean" in opencode["env_extra"]["OPENCODE_HOME"]
