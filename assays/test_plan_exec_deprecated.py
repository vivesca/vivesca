from __future__ import annotations

"""Tests for plan-exec.deprecated — AI plan executor with fallback chain."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path("/home/terry/germline/effectors/plan-exec.deprecated")


def _load():
    """Load the effector by exec-ing its Python body."""
    source = EFFECTOR.read_text()
    ns: dict = {"__name__": "plan_exec_deprecated"}
    exec(source, ns)
    return ns


_mod = _load()
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
main = _mod["main"]
BACKENDS = _mod["BACKENDS"]
RESULTS_DIR = _mod["RESULTS_DIR"]


# ── _build_prompt tests ──────────────────────────────────────────────


def test_build_prompt_contains_plan_content(tmp_path):
    """_build_prompt embeds the plan file content."""
    plan = tmp_path / "plan.md"
    plan.write_text("Task 1: do the thing\nTask 2: do another thing")
    result = _build_prompt("/fake/project", str(plan))
    assert "Task 1: do the thing" in result
    assert "Task 2: do another thing" in result


def test_build_prompt_contains_project_dir(tmp_path):
    """_build_prompt embeds the project directory."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    result = _build_prompt("/my/project", str(plan))
    assert "/my/project" in result


def test_build_prompt_contains_rules(tmp_path):
    """_build_prompt includes the RULES section."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    result = _build_prompt("/proj", str(plan))
    assert "RULES:" in result
    assert "Do NOT modify pyproject.toml" in result


def test_build_prompt_contains_success_marker(tmp_path):
    """_build_prompt includes the PLAN-EXEC-DONE marker instruction."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    result = _build_prompt("/proj", str(plan))
    assert "PLAN-EXEC-DONE" in result


def test_build_prompt_empty_plan(tmp_path):
    """_build_prompt handles an empty plan file."""
    plan = tmp_path / "empty.md"
    plan.write_text("")
    result = _build_prompt("/proj", str(plan))
    assert "RULES:" in result
    assert "PROJECT DIRECTORY: /proj" in result


# ── run_backend tests ────────────────────────────────────────────────


def test_run_backend_success_with_marker(tmp_path):
    """run_backend returns True when exit code 0 and output has PLAN-EXEC-DONE."""
    output_file = tmp_path / "gemini.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["echo", "hello"],
        "cwd": lambda project: project,
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("PLAN-EXEC-DONE\nFiles touched: [a.py]")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=_write_output):
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is True


def test_run_backend_success_no_marker_no_error(tmp_path):
    """run_backend returns True when exit code 0 and no 'error' in last 200 chars."""
    output_file = tmp_path / "codex.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["echo", "hello"],
        "cwd": lambda project: project,
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("All good, everything ran fine. Done.")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=_write_output):
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is True


def test_run_backend_success_but_error_in_tail(tmp_path):
    """run_backend returns False when exit 0 but 'error' in last 200 chars."""
    output_file = tmp_path / "opencode.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["echo", "hello"],
        "cwd": lambda project: project,
    }
    error_tail = "x" * 300 + "Error: something went wrong"

    def _write_output(*args, **kwargs):
        # Simulate subprocess writing to the file (mocked run bypasses the
        # file handle passed as stdout, so write directly to the output path).
        output_file.write_text(error_tail)
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=_write_output):
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is False


def test_run_backend_nonzero_exit(tmp_path):
    """run_backend returns False on non-zero exit code."""
    output_file = tmp_path / "gemini.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["false"],
        "cwd": lambda project: project,
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("some output")
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=_write_output):
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is False


def test_run_backend_quota_error(tmp_path):
    """run_backend returns False on 429/quota error."""
    output_file = tmp_path / "gemini.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["false"],
        "cwd": lambda project: project,
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("HTTP 429 Too Many Requests")
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=_write_output):
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is False


def test_run_backend_quota_chinese_auth_error(tmp_path):
    """run_backend returns False when Chinese auth error detected."""
    output_file = tmp_path / "gemini.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["false"],
        "cwd": lambda project: project,
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("身份验证失败")
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=_write_output):
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is False


def test_run_backend_timeout(tmp_path):
    """run_backend returns False on subprocess timeout."""
    import subprocess

    output_file = tmp_path / "slow.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["sleep", "999"],
        "cwd": lambda project: project,
    }
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=600)
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is False


def test_run_backend_not_installed(tmp_path):
    """run_backend returns False when command not found."""
    import subprocess

    output_file = tmp_path / "missing.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["nonexistent_tool_xyz"],
        "cwd": lambda project: project,
    }
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("nonexistent_tool_xyz")
        result = run_backend(backend, "/proj", "/plan.md", output_file)
    assert result is False


def test_run_backend_env_extra(tmp_path):
    """run_backend applies env_extra to subprocess environment."""
    output_file = tmp_path / "test.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["echo", "hi"],
        "cwd": lambda project: project,
        "env_extra": {"MY_KEY": "my_value"},
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("PLAN-EXEC-DONE")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=_write_output) as mock_run:
        run_backend(backend, "/proj", "/plan.md", output_file)
    call_kwargs = mock_run.call_args
    assert call_kwargs.kwargs["env"]["MY_KEY"] == "my_value"


def test_run_backend_strips_claudecode(tmp_path):
    """run_backend removes CLAUDECODE from env to avoid nesting."""
    output_file = tmp_path / "test.log"
    backend = {
        "name": "fake",
        "cmd": lambda project, pf: ["echo", "hi"],
        "cwd": lambda project: project,
    }

    def _write_output(*args, **kwargs):
        output_file.write_text("PLAN-EXEC-DONE")
        return MagicMock(returncode=0)

    with patch.dict(os.environ, {"CLAUDECODE": "1"}):
        with patch("subprocess.run", side_effect=_write_output) as mock_run:
            run_backend(backend, "/proj", "/plan.md", output_file)
    call_kwargs = mock_run.call_args
    assert "CLAUDECODE" not in call_kwargs.kwargs["env"]


# ── BACKENDS structure tests ─────────────────────────────────────────


def test_backends_has_three_entries():
    """BACKENDS list has gemini, codex, opencode."""
    assert len(BACKENDS) == 3
    assert BACKENDS[0]["name"] == "gemini"
    assert BACKENDS[1]["name"] == "codex"
    assert BACKENDS[2]["name"] == "opencode"


def test_backends_each_has_required_keys():
    """Each backend has name, cmd, cwd keys."""
    for b in BACKENDS:
        assert "name" in b
        assert "cmd" in b
        assert "cwd" in b


def test_backends_cmd_returns_list(tmp_path):
    """Each backend cmd callable returns a list."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    for b in BACKENDS:
        cmd = b["cmd"]("/fake/project", str(plan))
        assert isinstance(cmd, list)
        assert len(cmd) > 0


def test_backends_cwd_returns_project():
    """Each backend cwd returns the project directory."""
    for b in BACKENDS:
        assert b["cwd"]("/my/project") == "/my/project"


# ── main() tests ─────────────────────────────────────────────────────


def test_main_missing_plan_file():
    """main exits 1 when plan file does not exist."""
    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", "/nonexistent/plan.md"]):
            main()
    assert exc_info.value.code == 1


def test_main_dry_run(tmp_path):
    """main with --dry-run prints backends and exits 0."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", str(plan), "--dry-run"]):
            main()
    assert exc_info.value.code == 0


def test_main_unknown_backend(tmp_path):
    """main exits 1 when --backend specifies unknown backend."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", str(plan), "--backend", "nonexistent"]):
            main()
    assert exc_info.value.code == 1


def test_main_specific_backend_succeeds(tmp_path):
    """main exits 0 when forced backend succeeds."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan), "--backend", "gemini"]):
                main()
    assert exc_info.value.code == 0


def test_main_all_backends_fail(tmp_path):
    """main exits 1 when all backends fail."""
    plan = tmp_path / "plan.md"
    plan.write_text("do stuff")
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("not found")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan)]):
                main()
    assert exc_info.value.code == 1


# ── RESULTS_DIR test ─────────────────────────────────────────────────


def test_results_dir_under_home_cache():
    """RESULTS_DIR is under ~/.cache/plan-exec."""
    assert RESULTS_DIR == Path.home() / ".cache" / "plan-exec"
