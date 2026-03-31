from __future__ import annotations

"""Tests for effectors/plan-exec.deprecated — execute plan with free AI backends.

plan-exec.deprecated is a script (effectors/plan-exec.deprecated), not an importable module.
It is loaded via exec() so that module-level functions can be tested.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PLAN_EXEC_PATH = Path(__file__).resolve().parents[1] / "effectors" / "plan-exec.deprecated"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def pe(tmp_path):
    """Load plan-exec.deprecated via exec, redirect results directory to tmp."""
    ns: dict = {"__name__": "test_plan_exec_deprecated"}
    source = PLAN_EXEC_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect results cache to tmp
    results_dir = tmp_path / "cache" / "plan-exec"
    results_dir.mkdir(parents=True)
    ns["RESULTS_DIR"] = results_dir

    return ns


# ── _build_prompt ─────────────────────────────────────────────────────────────


class TestBuildPrompt:
    def test_includes_plan_content_and_project(self, pe, tmp_path):
        plan_file = tmp_path / "plan.md"
        plan_content = """
# Implement feature X

1. Add function foo
2. Add tests
3. Run pytest
"""
        plan_file.write_text(plan_content, encoding="utf-8")
        project = "/home/user/project"

        result = pe["_build_prompt"](project, str(plan_file))

        assert "PROJECT DIRECTORY: /home/user/project" in result
        assert "Implement feature X" in result
        assert "Add function foo" in result
        assert "RULES" in result
        assert "Do NOT modify pyproject.toml" in result
        assert "PLAN-EXEC-DONE" in result

    def test_reads_plan_correctly(self, pe, tmp_path):
        plan_file = tmp_path / "simple.plan"
        plan_file.write_text("Just do this one thing", encoding="utf-8")
        result = pe["_build_prompt"]("/project", str(plan_file))
        assert "Just do this one thing" in result


# ── BACKENDS constant ─────────────────────────────────────────────────────────


class TestBackends:
    def test_has_three_backends(self, pe):
        assert len(pe["BACKENDS"]) == 3
        names = [b["name"] for b in pe["BACKENDS"]]
        assert names == ["gemini", "codex", "opencode"]

    def test_each_backend_has_cmd(self, pe):
        for backend in pe["BACKENDS"]:
            assert "name" in backend
            assert callable(backend["cmd"])
            assert "cwd" in backend

    def test_opencode_has_env_extra(self, pe):
        opencode = next(b for b in pe["BACKENDS"] if b["name"] == "opencode")
        assert "env_extra" in opencode
        assert "OPENCODE_HOME" in opencode["env_extra"]


# ── run_backend ───────────────────────────────────────────────────────────────


class TestRunBackend:
    def test_returns_true_on_zero_exit_and_success_marker(self, pe, tmp_path):
        backend = pe["BACKENDS"][0]  # gemini
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"
        prompt_file.write_text("test", encoding="utf-8")

        def mock_run(cmd, *args, **kwargs):
            output_file.write_text("some output\nPLAN-EXEC-DONE\n", encoding="utf-8")
            return MagicMock(returncode=0)

        with patch.object(pe["subprocess"], "run", mock_run):
            result = pe["run_backend"](backend, project, str(prompt_file), output_file)
        assert result is True

    def test_returns_true_on_zero_exit_no_error_in_final_output(self, pe, tmp_path):
        backend = pe["BACKENDS"][0]
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"

        def mock_run(cmd, *args, **kwargs):
            output_file.write_text("all tasks done\ncompiled ok\n", encoding="utf-8")
            return MagicMock(returncode=0)

        with patch.object(pe["subprocess"], "run", mock_run):
            result = pe["run_backend"](backend, project, str(prompt_file), output_file)
        assert result is True

    def test_returns_false_on_zero_exit_but_errors_at_end(self, pe, tmp_path):
        backend = pe["BACKENDS"][0]
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"

        prompt_file.write_text("test plan", encoding="utf-8")

        def mock_run(cmd, *args, **kwargs):
            output_file.write_text("did some work\nError: failed to compile\n", encoding="utf-8")
            return MagicMock(returncode=0)

        with patch.object(pe["subprocess"], "run", mock_run):
            result = pe["run_backend"](backend, project, str(prompt_file), output_file)
        assert result is False

    def test_returns_false_on_nonzero_quota_error(self, pe, tmp_path, capsys):
        backend = pe["BACKENDS"][0]
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"
        prompt_file.write_text("test plan", encoding="utf-8")

        def mock_run(cmd, *args, **kwargs):
            output_file.write_text("429 quota exceeded\n", encoding="utf-8")
            return MagicMock(returncode=1)

        with patch.object(pe["subprocess"], "run", mock_run):
            result = pe["run_backend"](backend, project, str(prompt_file), output_file)
        assert result is False
        out = capsys.readouterr().out
        assert "quota/auth error" in out

    def test_returns_false_on_timeout(self, pe, tmp_path, capsys):
        backend = pe["BACKENDS"][0]
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"
        prompt_file.write_text("test plan", encoding="utf-8")

        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("cmd", 600))
        with patch.object(pe["subprocess"], "run", mock_run):
            result = pe["run_backend"](backend, project, str(prompt_file), output_file)
        assert result is False
        out = capsys.readouterr().out
        assert "timed out" in out

    def test_returns_false_on_file_not_found(self, pe, tmp_path, capsys):
        backend = pe["BACKENDS"][0]
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"
        prompt_file.write_text("test plan", encoding="utf-8")

        mock_run = MagicMock(side_effect=FileNotFoundError)
        with patch.object(pe["subprocess"], "run", mock_run):
            result = pe["run_backend"](backend, project, str(prompt_file), output_file)
        assert result is False
        out = capsys.readouterr().out
        assert "not installed" in out

    def test_pops_claudecode_from_env(self, pe, tmp_path):
        backend = pe["BACKENDS"][0]
        output_file = tmp_path / "gemini.log"
        project = str(tmp_path)
        prompt_file = tmp_path / "plan.md"
        prompt_file.write_text("test", encoding="utf-8")

        captured_env = None
        def mock_run(cmd, *args, **kwargs):
            nonlocal captured_env
            captured_env = kwargs["env"]
            output_file.write_text("PLAN-EXEC-DONE", encoding="utf-8")
            return MagicMock(returncode=0)

        # Set CLAUDECODE in current env
        original_env = os.environ.get("CLAUDECODE")
        os.environ["CLAUDECODE"] = "1"

        try:
            with patch.object(pe["subprocess"], "run", mock_run):
                pe["run_backend"](backend, project, str(prompt_file), output_file)
        finally:
            if original_env is not None:
                os.environ["CLAUDECODE"] = original_env
            else:
                os.environ.pop("CLAUDECODE", None)

        assert "CLAUDECODE" not in captured_env


# ── main argument parsing ────────────────────────────────────────────────────


class TestMainArgumentParsing:
    def test_missing_plan_file_exits_nonzero(self, pe, capsys):
        with patch.object(pe["sys"], "argv", ["plan-exec"]):
            with pytest.raises(SystemExit) as excinfo:
                pe["main"]()
        assert excinfo.value.code != 0

    def test_plan_file_not_found_exits_nonzero(self, pe, capsys):
        with patch.object(pe["sys"], "argv", ["plan-exec", "nonexistent_plan.md"]):
            with pytest.raises(SystemExit) as excinfo:
                pe["main"]()
        assert excinfo.value.code != 0
        err = capsys.readouterr().err
        assert "plan file not found" in err

    def test_dry_run_prints_would_backends_and_exits_zero(self, pe, tmp_path, capsys):
        plan_file = tmp_path / "test.plan"
        plan_file.write_text("test", encoding="utf-8")
        with patch.object(pe["sys"], "argv", ["plan-exec", str(plan_file), "--dry-run"]):
            with pytest.raises(SystemExit) as excinfo:
                pe["main"]()
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert "Would try:" in out
        assert "gemini → codex → opencode" in out

    def test_filter_by_backend_unknown_exits_nonzero(self, pe, tmp_path, capsys):
        plan_file = tmp_path / "test.plan"
        plan_file.write_text("test", encoding="utf-8")
        with patch.object(pe["sys"], "argv", ["plan-exec", str(plan_file), "--backend", "nonexistent"]):
            with pytest.raises(SystemExit) as excinfo:
                pe["main"]()
        assert excinfo.value.code != 0
        err = capsys.readouterr().err
        assert "unknown backend" in err

    def test_force_specific_backend_only_tries_that(self, pe, tmp_path, capsys):
        plan_file = tmp_path / "test.plan"
        plan_file.write_text("test", encoding="utf-8")

        called = []
        def mock_run_backend(backend, *args, **kwargs):
            called.append(backend["name"])
            return False

        with patch.dict(pe, {"run_backend": mock_run_backend}):
            with patch.object(pe["sys"], "argv", ["plan-exec", str(plan_file), "--backend", "codex", "--dry-run"]):
                try:
                    pe["main"]()
                except SystemExit:
                    pass  # dry-run exits
        # Dry run exits before trying backends, so not called
        assert len(called) == 0


# ── main execution flow ──────────────────────────────────────────────────────


class TestMainExecution:
    def test_first_backend_succeeds_exits_zero(self, pe, tmp_path, capsys):
        plan_file = tmp_path / "test.plan"
        plan_file.write_text("implement something", encoding="utf-8")

        called_backends = []
        def mock_run_backend(backend, *args, **kwargs):
            called_backends.append(backend["name"])
            return backend["name"] == "gemini"

        with patch.dict(pe, {"run_backend": mock_run_backend}):
            with patch.object(pe["sys"], "argv", ["plan-exec", str(plan_file)]):
                with pytest.raises(SystemExit) as excinfo:
                    pe["main"]()
        assert excinfo.value.code == 0
        assert called_backends == ["gemini"]
        out = capsys.readouterr().out
        assert "Plan executed successfully via gemini" in out

    def test_all_backends_fail_exits_nonzero(self, pe, tmp_path, capsys):
        plan_file = tmp_path / "test.plan"
        plan_file.write_text("implement something", encoding="utf-8")

        called_backends = []
        def mock_run_backend(backend, *args, **kwargs):
            called_backends.append(backend["name"])
            return False

        with patch.dict(pe, {"run_backend": mock_run_backend}):
            with patch.object(pe["sys"], "argv", ["plan-exec", str(plan_file)]):
                with pytest.raises(SystemExit) as excinfo:
                    pe["main"]()
        assert excinfo.value.code != 0
        assert sorted(called_backends) == sorted(["gemini", "codex", "opencode"])
        out = capsys.readouterr().out
        assert "All backends failed" in out

    def test_second_backend_succeeds_stops_early(self, pe, tmp_path):
        plan_file = tmp_path / "test.plan"
        plan_file.write_text("implement something", encoding="utf-8")

        called_backends = []
        def mock_run_backend(backend, *args, **kwargs):
            called_backends.append(backend["name"])
            return backend["name"] == "codex"

        with patch.dict(pe, {"run_backend": mock_run_backend}):
            with patch.object(pe["sys"], "argv", ["plan-exec", str(plan_file)]):
                with pytest.raises(SystemExit) as excinfo:
                    pe["main"]()
        assert excinfo.value.code == 0
        assert called_backends == ["gemini", "codex"]
        # opencode not called


# ── CLI integration ───────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_help_exits_zero(self):
        r = subprocess.run(
            ["uv", "run", "--script", str(PLAN_EXEC_PATH), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "Execute plan with free AI tools" in r.stdout
        assert "--dry-run" in r.stdout
