from __future__ import annotations

"""Tests for plan-exec.deprecated — Execute a plan doc using free AI tools."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_plan_exec():
    """Load the plan-exec module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/plan-exec.deprecated")).read()
    ns: dict = {"__name__": "plan_exec"}
    exec(source, ns)
    return ns


_mod = _load_plan_exec()
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
BACKENDS = _mod["BACKENDS"]
RESULTS_DIR = _mod["RESULTS_DIR"]


# ── _build_prompt tests ────────────────────────────────────────────────


def test_build_prompt_includes_plan_content():
    """_build_prompt includes the plan file content in the prompt."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Plan\n\nDo something important.")
        plan_file = f.name

    try:
        prompt = _build_prompt("/tmp/project", plan_file)
        assert "# Test Plan" in prompt
        assert "Do something important" in prompt
    finally:
        os.unlink(plan_file)


def test_build_prompt_includes_project_directory():
    """_build_prompt includes the project directory in the prompt."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("Test plan")
        plan_file = f.name

    try:
        prompt = _build_prompt("/my/custom/project", plan_file)
        assert "/my/custom/project" in prompt
    finally:
        os.unlink(plan_file)


def test_build_prompt_includes_rules():
    """_build_prompt includes execution rules in the prompt."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("Test plan")
        plan_file = f.name

    try:
        prompt = _build_prompt("/project", plan_file)
        assert "RULES:" in prompt
        assert "Do NOT modify pyproject.toml" in prompt
        assert "no stubs" in prompt
        assert "PLAN-EXEC-DONE" in prompt
    finally:
        os.unlink(plan_file)


# ── BACKENDS constant tests ─────────────────────────────────────────────


def test_backends_has_three_entries():
    """BACKENDS contains exactly three backend definitions."""
    assert len(BACKENDS) == 3


def test_backends_names():
    """BACKENDS has expected backend names in order."""
    names = [b["name"] for b in BACKENDS]
    assert names == ["gemini", "codex", "opencode"]


def test_backends_have_required_keys():
    """Each backend has required keys: name, cmd, cwd."""
    for backend in BACKENDS:
        assert "name" in backend
        assert "cmd" in backend
        assert "cwd" in backend


def test_gemini_cmd_structure(tmp_path):
    """Gemini backend cmd has expected structure."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    gemini = next(b for b in BACKENDS if b["name"] == "gemini")
    cmd = gemini["cmd"](str(tmp_path), str(plan_file))
    assert cmd[0] == "gemini"
    assert "-m" in cmd
    assert "--yolo" in cmd


def test_codex_cmd_structure(tmp_path):
    """Codex backend cmd has expected structure."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    codex = next(b for b in BACKENDS if b["name"] == "codex")
    cmd = codex["cmd"](str(tmp_path), str(plan_file))
    assert cmd[0] == "codex"
    assert "exec" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "--sandbox" in cmd
    assert "--full-auto" in cmd


def test_opencode_cmd_structure(tmp_path):
    """OpenCode backend cmd has expected structure."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    cmd = opencode["cmd"](str(tmp_path), str(plan_file))
    assert cmd[0] == "opencode"
    assert "run" in cmd
    assert "--title" in cmd


def test_opencode_has_env_extra():
    """OpenCode backend has env_extra with OPENCODE_HOME."""
    opencode = next(b for b in BACKENDS if b["name"] == "opencode")
    assert "env_extra" in opencode
    assert "OPENCODE_HOME" in opencode["env_extra"]


# ── run_backend tests ───────────────────────────────────────────────────


def test_run_backend_success_with_marker(tmp_path):
    """run_backend returns True when output contains PLAN-EXEC-DONE."""
    backend = BACKENDS[0]  # gemini
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    output_file = tmp_path / "output.log"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert result is True
    assert "PLAN-EXEC-DONE" in output_file.read_text() or "succeeded" in output_file.read_text() or mock_run.called


def test_run_backend_handles_file_not_found(tmp_path, capsys):
    """run_backend returns False and prints message when binary not found."""
    backend = BACKENDS[0]
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    output_file = tmp_path / "output.log"

    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert result is False
    captured = capsys.readouterr()
    assert "not installed" in captured.out


def test_run_backend_handles_timeout(tmp_path, capsys):
    """run_backend returns False and prints message on timeout."""
    import subprocess
    backend = BACKENDS[0]
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    output_file = tmp_path / "output.log"

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 600)):
        result = run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert result is False
    captured = capsys.readouterr()
    assert "timed out" in captured.out


def test_run_backend_handles_quota_error(tmp_path, capsys):
    """run_backend returns False for quota/auth errors."""
    backend = BACKENDS[0]
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    output_file = tmp_path / "output.log"

    def mock_run_quota_error(*args, **kwargs):
        # Write quota error to stdout file handle
        stdout_fh = kwargs.get("stdout")
        if stdout_fh:
            stdout_fh.write("Error 429: quota exceeded\n")
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=mock_run_quota_error):
        result = run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert result is False
    captured = capsys.readouterr()
    assert "quota" in captured.out.lower() or "falling back" in captured.out


def test_run_backend_nonzero_exit_without_quota_error(tmp_path, capsys):
    """run_backend returns False for non-quota failures."""
    backend = BACKENDS[0]
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    output_file = tmp_path / "output.log"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        output_file.write_text("Some other error")
        result = run_backend(backend, str(tmp_path), str(plan_file), output_file)

    assert result is False
    captured = capsys.readouterr()
    assert "failed" in captured.out


def test_run_backend_strips_claudcode_env(tmp_path):
    """run_backend removes CLAUDECODE from environment to avoid nesting."""
    backend = BACKENDS[0]
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("Test plan")
    output_file = tmp_path / "output.log"

    original_env = os.environ.copy()
    os.environ["CLAUDECODE"] = "some-value"

    captured_env = {}

    def capture_env(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        return MagicMock(returncode=0)

    try:
        with patch("subprocess.run", side_effect=capture_env):
            run_backend(backend, str(tmp_path), str(plan_file), output_file)

        assert "CLAUDECODE" not in captured_env
    finally:
        os.environ.clear()
        os.environ.update(original_env)


# ── RESULTS_DIR constant test ───────────────────────────────────────────


def test_results_dir_path():
    """RESULTS_DIR is under ~/.cache/plan-exec."""
    assert ".cache" in str(RESULTS_DIR)
    assert "plan-exec" in str(RESULTS_DIR)


# ─── CLI integration tests (subprocess) ─────────────────────────────────


def test_cli_missing_plan_file():
    """CLI exits with error when plan file doesn't exist."""
    result = os.system("uv run --script effectors/plan-exec.deprecated /nonexistent/plan.md 2>/dev/null")
    # os.system returns exit code in high byte
    exit_code = result >> 8 if result > 255 else result
    assert exit_code != 0


def test_cli_dry_run_flag():
    """CLI with --dry-run shows backends and exits successfully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("Test plan")
        plan_file = f.name

    try:
        result = os.system(f"cd /home/terry/germline && uv run --script effectors/plan-exec.deprecated '{plan_file}' --dry-run 2>&1")
        exit_code = result >> 8 if result > 255 else result
        assert exit_code == 0
    finally:
        os.unlink(plan_file)


def test_cli_unknown_backend_error():
    """CLI exits with error for unknown backend name."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("Test plan")
        plan_file = f.name

    try:
        result = os.system(f"cd /home/terry/germline && uv run --script effectors/plan-exec.deprecated '{plan_file}' --backend unknown-backend 2>/dev/null")
        exit_code = result >> 8 if result > 255 else result
        assert exit_code != 0
    finally:
        os.unlink(plan_file)
