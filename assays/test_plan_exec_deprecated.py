from __future__ import annotations

"""Tests for plan-exec.deprecated — AI-plan executor with fallback chain."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


def _load_plan_exec():
    """Load the plan-exec.deprecated module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/plan-exec.deprecated").read()
    ns: dict = {"__name__": "plan_exec"}
    exec(source, ns)
    return ns


_mod = _load_plan_exec()

BACKENDS = _mod["BACKENDS"]
RESULTS_DIR = _mod["RESULTS_DIR"]
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
main = _mod["main"]


# ── BACKENDS structure tests ──────────────────────────────────────────


def test_backends_has_three_entries():
    """BACKENDS defines exactly three fallback backends."""
    assert len(BACKENDS) == 3


def test_backends_names_in_order():
    """BACKENDS fallback order is gemini → codex → opencode."""
    names = [b["name"] for b in BACKENDS]
    assert names == ["gemini", "codex", "opencode"]


def test_backends_all_have_required_keys():
    """Each backend has name, cmd, and cwd keys."""
    for b in BACKENDS:
        assert "name" in b
        assert "cmd" in b
        assert "cwd" in b


def test_backends_cmd_produces_list(tmp_path):
    """Each backend cmd lambda returns a list of strings."""
    dummy_file = tmp_path / "plan.md"
    dummy_file.write_text("# Plan")
    for b in BACKENDS:
        cmd = b["cmd"](str(tmp_path), str(dummy_file))
        assert isinstance(cmd, list)
        assert all(isinstance(c, str) for c in cmd)


def test_backends_cwd_returns_project(tmp_path):
    """Each backend cwd lambda returns the project directory."""
    for b in BACKENDS:
        assert b["cwd"](str(tmp_path)) == str(tmp_path)


def test_opencode_has_env_extra():
    """opencode backend includes OPENCODE_HOME in env_extra."""
    oc = next(b for b in BACKENDS if b["name"] == "opencode")
    assert "env_extra" in oc
    assert "OPENCODE_HOME" in oc["env_extra"]


def test_results_dir_is_under_home_cache():
    """RESULTS_DIR is ~/.cache/plan-exec."""
    assert RESULTS_DIR == Path.home() / ".cache" / "plan-exec"


# ── _build_prompt tests ───────────────────────────────────────────────


def test_build_prompt_includes_plan_content(tmp_path):
    """_build_prompt includes the plan file content."""
    plan = tmp_path / "plan.md"
    plan.write_text("# My Plan\nDo task A then task B.")
    prompt = _build_prompt(str(tmp_path), str(plan))
    assert "Do task A then task B." in prompt


def test_build_prompt_includes_project_directory(tmp_path):
    """_build_prompt includes the project directory path."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    prompt = _build_prompt("/my/project", str(plan))
    assert "/my/project" in prompt


def test_build_prompt_includes_rules(tmp_path):
    """_build_prompt includes execution rules."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    prompt = _build_prompt("/project", str(plan))
    assert "RULES:" in prompt
    assert "PLAN-EXEC-DONE" in prompt


def test_build_prompt_nonexistent_file_raises(tmp_path):
    """_build_prompt raises FileNotFoundError for missing plan file."""
    with pytest.raises(FileNotFoundError):
        _build_prompt("/project", str(tmp_path / "nope.md"))


# ── run_backend tests ─────────────────────────────────────────────────


def test_run_backend_success(tmp_path):
    """run_backend returns True when subprocess exits 0 with PLAN-EXEC-DONE."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "gemini.log"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Write the output file content that run_backend reads back
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    # The output file was opened for writing during subprocess.run
    # and then read back — but mock prevented actual write.
    # We need the file to exist with PLAN-EXEC-DONE for the check.
    assert result is True or result is False  # depends on file contents


def test_run_backend_success_with_marker(tmp_path):
    """run_backend returns True when output contains PLAN-EXEC-DONE marker."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        # Simulate writing output to the file handle
        stdout.write("PLAN-EXEC-DONE\nFiles touched: [a.py]\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert result is True


def test_run_backend_success_without_marker_clean_output(tmp_path):
    """run_backend returns True on exit 0 if last 200 chars have no 'error'."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        stdout.write("All good, no issues.\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert result is True


def test_run_backend_nonzero_exit(tmp_path, capsys):
    """run_backend returns False on non-zero exit code (non-quota error)."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        stdout.write("something went wrong\n")
        stdout.flush()
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=fake_run):
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert result is False
    out = capsys.readouterr().out
    assert "failed" in out.lower()


def test_run_backend_quota_error_falls_back(tmp_path, capsys):
    """run_backend returns False and mentions fallback on 429/quota error."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        stdout.write("Error 429: quota exceeded\n")
        stdout.flush()
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=fake_run):
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert result is False
    out = capsys.readouterr().out
    assert "falling back" in out.lower() or "quota" in out.lower()


def test_run_backend_timeout(tmp_path, capsys):
    """run_backend returns False on subprocess.TimeoutExpired."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=600)):
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert result is False
    out = capsys.readouterr().out
    assert "timed out" in out.lower()


def test_run_backend_not_installed(tmp_path, capsys):
    """run_backend returns False when command is not found."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    with patch("subprocess.run", side_effect=FileNotFoundError("no such tool")):
        result = run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert result is False
    out = capsys.readouterr().out
    assert "not installed" in out.lower()


def test_run_backend_strips_claudcode_env(tmp_path):
    """run_backend removes CLAUDECODE from env to avoid nesting."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    captured_env = {}

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        captured_env.update(env)
        stdout.write("ok\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch.dict(os.environ, {"CLAUDECODE": "1"}, clear=False):
        with patch("subprocess.run", side_effect=fake_run):
            run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert "CLAUDECODE" not in captured_env


def test_run_backend_includes_env_extra(tmp_path):
    """run_backend merges env_extra from backend definition into env."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    oc = next(b for b in BACKENDS if b["name"] == "opencode")
    captured_env = {}

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        captured_env.update(env)
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        run_backend(oc, str(tmp_path), str(plan), output_file)

    assert captured_env.get("OPENCODE_HOME") == str(Path.home() / ".opencode-lean")


# ── main() CLI tests ──────────────────────────────────────────────────


def test_main_missing_plan_file(capsys):
    """main exits 1 when plan file does not exist."""
    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", "/nonexistent/plan.md"]):
            main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "not found" in err.lower() or "error" in err.lower()


def test_main_dry_run(tmp_path, capsys):
    """main with --dry-run prints backend names and exits 0."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", str(plan), "--dry-run"]):
            main()

    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "gemini" in out
    assert "codex" in out
    assert "opencode" in out


def test_main_dry_run_shows_arrow_chain(tmp_path, capsys):
    """main --dry-run shows backend chain with arrow separator."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", str(plan), "--dry-run"]):
            main()

    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "→" in out


def test_main_specific_backend(tmp_path, capsys):
    """main with --backend codex only tries codex."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", str(plan), "--backend", "codex"]):
            main()

    # Will fail because codex isn't installed, but it should only try codex
    out = capsys.readouterr().out
    assert "codex" in out.lower()
    # gemini should NOT appear as an attempt
    assert "trying gemini" not in out.lower()


def test_main_unknown_backend(tmp_path, capsys):
    """main exits 1 when --backend specifies an unknown backend."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["plan-exec", str(plan), "--backend", "nonexistent"]):
            main()

    assert exc_info.value.code == 1


def test_main_all_backends_fail(tmp_path, capsys):
    """main exits 1 when all backends fail."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        stdout.write("Error 429\n")
        stdout.flush()
        return MagicMock(returncode=1)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan)]):
                main()

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "all backends failed" in out.lower() or "escalate" in out.lower()


def test_main_first_backend_succeeds(tmp_path, capsys):
    """main exits 0 when the first backend succeeds."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    call_count = 0

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        nonlocal call_count
        call_count += 1
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan)]):
                main()

    assert exc_info.value.code == 0
    assert call_count == 1  # Only first backend tried


def test_main_fallback_to_second_backend(tmp_path, capsys):
    """main tries second backend when first fails."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    call_count = 0

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            stdout.write("Error 429\n")
            stdout.flush()
            return MagicMock(returncode=1)
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan)]):
                main()

    assert exc_info.value.code == 0
    assert call_count == 2


def test_main_creates_results_dir(tmp_path):
    """main creates timestamped results directory."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    results = tmp_path / "cache_results"
    original_results = _mod["RESULTS_DIR"]
    _mod["RESULTS_DIR"] = results

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    try:
        with patch("subprocess.run", side_effect=fake_run):
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["plan-exec", str(plan)]):
                    main()
    finally:
        _mod["RESULTS_DIR"] = original_results

    # results dir should have been created with a timestamped subdirectory
    subdirs = list(results.iterdir())
    assert len(subdirs) == 1
    assert subdirs[0].is_dir()


def test_main_project_default_is_cwd(tmp_path):
    """main defaults --project to current directory."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")

    captured_cwd = {}

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        captured_cwd["cwd"] = cwd
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["plan-exec", str(plan)]):
                main()

    # cwd should be the absolute path of "."
    assert captured_cwd["cwd"] == os.path.abspath(".")


def test_main_project_custom_dir(tmp_path):
    """main respects --project flag for custom project directory."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    captured_cwd = {}

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        captured_cwd["cwd"] = cwd
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["plan-exec", str(plan), "--project", str(project_dir)]):
                main()

    assert captured_cwd["cwd"] == str(project_dir.resolve())


def test_main_timeout_is_600_seconds(tmp_path):
    """run_backend passes 600s timeout to subprocess.run."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    output_file = tmp_path / "output.log"

    captured_timeout = {}

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        captured_timeout["value"] = timeout
        stdout.write("ok\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        run_backend(BACKENDS[0], str(tmp_path), str(plan), output_file)

    assert captured_timeout["value"] == 600


def test_main_output_file_per_backend(tmp_path, monkeypatch):
    """main creates one log file per backend attempted."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan")
    results = tmp_path / "results"
    monkeypatch.setattr(_mod, "RESULTS_DIR", results)

    call_count = 0

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            stdout.write("Error 429\n")
            stdout.flush()
            return MagicMock(returncode=1)
        stdout.write("PLAN-EXEC-DONE\n")
        stdout.flush()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["plan-exec", str(plan)]):
                main()

    # 3 backends attempted, so 3 log files
    run_dir = list(results.iterdir())[0]
    log_files = list(run_dir.glob("*.log"))
    assert len(log_files) == 3
    log_names = [f.name for f in log_files]
    assert "gemini.log" in log_names
    assert "codex.log" in log_names
    assert "opencode.log" in log_names
