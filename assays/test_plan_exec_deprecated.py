from __future__ import annotations

"""Tests for effectors/plan-exec.deprecated — AI plan execution with backend fallback chain."""

import os
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Load module via exec (effectors are scripts, not importable modules) ────

EFFECTOR_PATH = Path(__file__).resolve().parent.parent / "effectors" / "plan-exec.deprecated"


def _load_module() -> dict:
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "plan_exec_deprecated", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()
BACKENDS = _mod["BACKENDS"]
RESULTS_DIR = _mod["RESULTS_DIR"]
_build_prompt = _mod["_build_prompt"]
run_backend = _mod["run_backend"]
main = _mod["main"]


# ── Constants tests ────────────────────────────────────────────────────────


class TestConstants:
    """Verify module-level constants have expected values."""

    def test_results_dir_under_home(self):
        """RESULTS_DIR lives under the user's home .cache directory."""
        assert str(RESULTS_DIR).startswith(str(Path.home()))
        assert ".cache" in str(RESULTS_DIR)

    def test_backends_is_list(self):
        """BACKENDS is a list of backend dicts."""
        assert isinstance(BACKENDS, list)
        assert len(BACKENDS) == 3

    def test_backends_names(self):
        """BACKENDS contains expected backend names in order."""
        names = [b["name"] for b in BACKENDS]
        assert names == ["gemini", "codex", "opencode"]

    def test_each_backend_has_required_keys(self):
        """Each backend dict has 'name', 'cmd', and 'cwd' keys."""
        for b in BACKENDS:
            assert "name" in b, f"Missing 'name' in {b}"
            assert "cmd" in b, f"Missing 'cmd' in {b}"
            assert "cwd" in b, f"Missing 'cwd' in {b}"

    def test_backend_cmd_is_callable(self):
        """Each backend 'cmd' and 'cwd' are callables."""
        for b in BACKENDS:
            assert callable(b["cmd"]), f"cmd not callable for {b['name']}"
            assert callable(b["cwd"]), f"cwd not callable for {b['name']}"

    def test_opencode_has_env_extra(self):
        """The opencode backend sets OPENCODE_HOME via env_extra."""
        oc = next(b for b in BACKENDS if b["name"] == "opencode")
        assert "env_extra" in oc
        assert "OPENCODE_HOME" in oc["env_extra"]

    def test_gemini_and_codex_no_env_extra(self):
        """Gemini and codex backends do not set extra env vars."""
        for name in ("gemini", "codex"):
            b = next(b for b in BACKENDS if b["name"] == name)
            assert b.get("env_extra", {}) == {}


# ── _build_prompt tests ────────────────────────────────────────────────────


class TestBuildPrompt:
    """Tests for _build_prompt(project, prompt_file)."""

    def test_build_prompt_contains_plan_content(self, tmp_path):
        """_build_prompt includes the plan file content."""
        plan = tmp_path / "plan.md"
        plan.write_text("# Task: Fix bug in auth module\n\nDetails here.")
        result = _build_prompt("/proj", str(plan))
        assert "# Task: Fix bug in auth module" in result
        assert "Details here." in result

    def test_build_prompt_contains_project_dir(self, tmp_path):
        """_build_prompt includes the project directory path."""
        plan = tmp_path / "plan.md"
        plan.write_text("do stuff")
        result = _build_prompt("/my/project", str(plan))
        assert "/my/project" in result

    def test_build_prompt_contains_rules(self, tmp_path):
        """_build_prompt includes execution rules."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        result = _build_prompt("/proj", str(plan))
        assert "RULES:" in result
        assert "Do NOT modify pyproject.toml" in result
        assert "no stubs" in result or "no TODOs" in result

    def test_build_prompt_contains_success_marker(self, tmp_path):
        """_build_prompt asks executor to print PLAN-EXEC-DONE."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        result = _build_prompt("/proj", str(plan))
        assert "PLAN-EXEC-DONE" in result

    def test_build_prompt_empty_plan(self, tmp_path):
        """_build_prompt works with empty plan file."""
        plan = tmp_path / "empty.md"
        plan.write_text("")
        result = _build_prompt("/proj", str(plan))
        assert "PLAN:" in result
        assert "PROJECT DIRECTORY: /proj" in result

    def test_build_prompt_multiline_plan(self, tmp_path):
        """_build_prompt preserves multiline content."""
        plan = tmp_path / "plan.md"
        plan.write_text("Line 1\nLine 2\nLine 3\n")
        result = _build_prompt("/proj", str(plan))
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_build_prompt_nonexistent_file_raises(self):
        """_build_prompt raises when plan file does not exist."""
        with pytest.raises(FileNotFoundError):
            _build_prompt("/proj", "/nonexistent/plan.md")


# ── Backend cmd generation tests ───────────────────────────────────────────


class TestBackendCmdGeneration:
    """Tests for backend['cmd'] lambda — verifies command structure."""

    def test_gemini_cmd_structure(self, tmp_path):
        """Gemini backend builds correct command."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        b = next(b for b in BACKENDS if b["name"] == "gemini")
        cmd = b["cmd"]("/proj", str(plan))
        assert cmd[0] == "gemini"
        assert "-m" in cmd
        assert "gemini-3.1-pro-preview" in cmd
        assert "--yolo" in cmd

    def test_codex_cmd_structure(self, tmp_path):
        """Codex backend builds correct command."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        b = next(b for b in BACKENDS if b["name"] == "codex")
        cmd = b["cmd"]("/proj", str(plan))
        assert cmd[0] == "codex"
        assert "exec" in cmd
        assert "--full-auto" in cmd
        assert "--sandbox" in cmd
        assert "danger-full-access" in cmd

    def test_opencode_cmd_structure(self, tmp_path):
        """OpenCode backend builds correct command with model from env."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        b = next(b for b in BACKENDS if b["name"] == "opencode")
        with patch.dict(os.environ, {"OPENCODE_MODEL": "test-model"}):
            cmd = b["cmd"]("/proj", str(plan))
        assert cmd[0] == "opencode"
        assert "run" in cmd
        assert "-m" in cmd
        assert "test-model" in cmd

    def test_opencode_default_model(self, tmp_path):
        """OpenCode uses 'opencode/glm-5' when OPENCODE_MODEL not set."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        b = next(b for b in BACKENDS if b["name"] == "opencode")
        env = os.environ.copy()
        env.pop("OPENCODE_MODEL", None)
        with patch.dict(os.environ, env, clear=True):
            cmd = b["cmd"]("/proj", str(plan))
        model_idx = cmd.index("-m") + 1
        assert cmd[model_idx] == "opencode/glm-5"

    def test_opencode_title_format(self, tmp_path):
        """OpenCode command includes a title starting with 'plan-exec-'."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        b = next(b for b in BACKENDS if b["name"] == "opencode")
        cmd = b["cmd"]("/proj", str(plan))
        title_idx = cmd.index("--title") + 1
        assert cmd[title_idx].startswith("plan-exec-")

    def test_cwd_returns_project(self):
        """Each backend's cwd lambda returns the project argument."""
        for b in BACKENDS:
            assert b["cwd"]("/my/project") == "/my/project"

    def test_gemini_cmd_contains_prompt_text(self, tmp_path):
        """Gemini command embeds the built prompt as -p argument."""
        plan = tmp_path / "plan.md"
        plan.write_text("MY_UNIQUE_TASK_12345")
        b = next(b for b in BACKENDS if b["name"] == "gemini")
        cmd = b["cmd"]("/proj", str(plan))
        # -p flag followed by prompt string
        p_idx = cmd.index("-p") + 1
        assert "MY_UNIQUE_TASK_12345" in cmd[p_idx]


# ── run_backend tests ──────────────────────────────────────────────────────


class TestRunBackend:
    """Tests for run_backend() — subprocess execution with fallback logic."""

    def _make_backend(self, name="gemini"):
        return next(b for b in BACKENDS if b["name"] == name)

    def test_run_backend_success_with_marker(self, tmp_path):
        """run_backend returns True when process exits 0 and output has PLAN-EXEC-DONE."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Write the success marker to the output file
            original_run = subprocess.run

            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("PLAN-EXEC-DONE\nFiles touched: []\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is True

    def test_run_backend_success_without_marker_no_error(self, tmp_path):
        """run_backend returns True when exit 0 and no 'error' in tail of output."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("All done, everything is fine.\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is True

    def test_run_backend_nonzero_exit(self, tmp_path, capsys):
        """run_backend returns False when process exits non-zero."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("some output\n")
                return MagicMock(returncode=1)

            mock_run.side_effect = side_effect
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is False
        out = capsys.readouterr().out
        assert "failed" in out.lower() or "✗" in out

    def test_run_backend_quota_error_falls_back(self, tmp_path, capsys):
        """run_backend returns False with quota error (429) in output."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("Error 429: rate limit exceeded\n")
                return MagicMock(returncode=1)

            mock_run.side_effect = side_effect
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is False
        out = capsys.readouterr().out
        assert "quota" in out.lower() or "429" in out or "falling back" in out.lower()

    def test_run_backend_timeout(self, tmp_path, capsys):
        """run_backend returns False when subprocess times out."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="gemini", timeout=600)
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is False
        out = capsys.readouterr().out
        assert "timed out" in out.lower() or "✗" in out

    def test_run_backend_not_installed(self, tmp_path, capsys):
        """run_backend returns False when backend binary not found."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gemini not found")
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is False
        out = capsys.readouterr().out
        assert "not installed" in out.lower() or "✗" in out

    def test_run_backend_strips_claudecode_env(self, tmp_path):
        """run_backend removes CLAUDECODE from environment to avoid nesting."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        captured_env = {}

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                captured_env.update(kwargs.get("env", {}))
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("PLAN-EXEC-DONE\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            with patch.dict(os.environ, {"CLAUDECODE": "1"}, clear=False):
                run_backend(backend, "/proj", str(plan), output_file)

        assert "CLAUDECODE" not in captured_env

    def test_run_backend_applies_env_extra(self, tmp_path):
        """run_backend applies backend-specific env_extra (e.g. OPENCODE_HOME)."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend("opencode")
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        captured_env = {}

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                captured_env.update(kwargs.get("env", {}))
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("PLAN-EXEC-DONE\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            run_backend(backend, "/proj", str(plan), output_file)

        assert "OPENCODE_HOME" in captured_env

    def test_run_backend_exit_zero_with_error_in_tail(self, tmp_path, capsys):
        """run_backend returns False when exit 0 but last 200 chars mention 'error'."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("x" * 250 + "error: something went wrong\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is False
        out = capsys.readouterr().out
        assert "suggests errors" in out.lower() or "✗" in out

    def test_run_backend_quota_auth_chinese(self, tmp_path, capsys):
        """run_backend detects Chinese auth error (身份验证) and falls back."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("身份验证失败\n")
                return MagicMock(returncode=1)

            mock_run.side_effect = side_effect
            result = run_backend(backend, "/proj", str(plan), output_file)

        assert result is False
        out = capsys.readouterr().out
        assert "falling back" in out.lower() or "✗" in out

    def test_run_backend_timeout_is_600_seconds(self, tmp_path):
        """run_backend passes 600s timeout to subprocess.run."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("PLAN-EXEC-DONE\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            run_backend(backend, "/proj", str(plan), output_file)

        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("timeout") == 600 or (len(call_kwargs) > 1 and call_kwargs[1].get("timeout") == 600)

    def test_run_backend_stderr_redirected_to_stdout(self, tmp_path):
        """run_backend merges stderr into stdout for output file."""
        output_file = tmp_path / "output.log"
        backend = self._make_backend()
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                    kwargs["stdout"].write("PLAN-EXEC-DONE\n")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect
            run_backend(backend, "/proj", str(plan), output_file)

        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("stderr") == subprocess.STDOUT or (len(call_kwargs) > 1 and call_kwargs[1].get("stderr") == subprocess.STDOUT)


# ── main() tests ───────────────────────────────────────────────────────────


class TestMain:
    """Tests for main() — argument parsing and orchestration."""

    def test_main_missing_plan_file_exits_1(self):
        """main exits with code 1 when plan file does not exist."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", "/nonexistent/plan.md"]):
                main()
        assert exc_info.value.code == 1

    def test_main_dry_run_exits_0(self, tmp_path, capsys):
        """main --dry-run prints backend names and exits 0."""
        plan = tmp_path / "plan.md"
        plan.write_text("task content")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan), "--dry-run"]):
                main()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "gemini" in out
        assert "codex" in out
        assert "opencode" in out
        assert "→" in out  # arrow between backends

    def test_main_dry_run_does_not_call_run_backend(self, tmp_path, capsys):
        """main --dry-run does not call run_backend."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        mock_rb = MagicMock(return_value=True)
        original = _mod["run_backend"]
        _mod["run_backend"] = mock_rb
        try:
            with pytest.raises(SystemExit) as exc_info:
                with patch("sys.argv", ["plan-exec", str(plan), "--dry-run"]):
                    main()
        finally:
            _mod["run_backend"] = original
        assert exc_info.value.code == 0
        mock_rb.assert_not_called()

    def test_main_with_backend_filter(self, tmp_path, capsys):
        """main --backend codex only tries the specified backend."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        attempted = []
        original = _mod["run_backend"]

        def track(backend, project, prompt_file, output_file):
            attempted.append(backend["name"])
            return False

        _mod["run_backend"] = track
        try:
            with pytest.raises(SystemExit) as exc_info:
                with patch("sys.argv", ["plan-exec", str(plan), "-b", "codex"]):
                    main()
        finally:
            _mod["run_backend"] = original

        assert exc_info.value.code == 1
        assert attempted == ["codex"]

    def test_main_unknown_backend_exits_1(self, tmp_path):
        """main exits with code 1 when --backend specifies unknown backend."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["plan-exec", str(plan), "-b", "nonexistent"]):
                main()
        assert exc_info.value.code == 1

    def test_main_success_on_first_backend(self, tmp_path, capsys):
        """main exits 0 when first backend succeeds."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        original = _mod["run_backend"]
        _mod["run_backend"] = MagicMock(return_value=True)
        try:
            with pytest.raises(SystemExit) as exc_info:
                with patch("sys.argv", ["plan-exec", str(plan)]):
                    main()
        finally:
            _mod["run_backend"] = original

        assert exc_info.value.code == 0

    def test_main_all_backends_fail_exits_1(self, tmp_path, capsys):
        """main exits 1 when all backends fail."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        original = _mod["run_backend"]
        _mod["run_backend"] = MagicMock(return_value=False)
        try:
            with pytest.raises(SystemExit) as exc_info:
                with patch("sys.argv", ["plan-exec", str(plan)]):
                    main()
        finally:
            _mod["run_backend"] = original

        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "All backends failed" in out or "Escalate" in out

    def test_main_creates_results_dir(self, tmp_path):
        """main creates a timestamped results directory."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        results_dir = tmp_path / "cache" / "plan-exec"

        original_rd = _mod["RESULTS_DIR"]
        original_rb = _mod["run_backend"]
        _mod["RESULTS_DIR"] = results_dir
        _mod["run_backend"] = MagicMock(return_value=True)
        try:
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["plan-exec", str(plan)]):
                    main()
        finally:
            _mod["RESULTS_DIR"] = original_rd
            _mod["run_backend"] = original_rb

        # Results dir should have been created with a timestamped subdirectory
        subdirs = list(results_dir.iterdir()) if results_dir.exists() else []
        assert len(subdirs) >= 1

    def test_main_project_default_is_cwd(self, tmp_path, capsys):
        """main defaults project to current working directory."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        original = _mod["run_backend"]
        captured = {}
        def capture_run(backend, project, prompt_file, output_file):
            captured["project"] = project
            captured["backend"] = backend["name"]
            return True
        _mod["run_backend"] = capture_run
        try:
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["plan-exec", str(plan)]):
                    main()
        finally:
            _mod["run_backend"] = original

        assert os.path.isabs(captured["project"])

    def test_main_project_override(self, tmp_path):
        """main --project sets the project directory."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()

        original = _mod["run_backend"]
        captured = {}
        def capture_run(backend, project, prompt_file, output_file):
            captured["project"] = project
            return True
        _mod["run_backend"] = capture_run
        try:
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["plan-exec", str(plan), "-p", str(project_dir)]):
                    main()
        finally:
            _mod["run_backend"] = original

        assert captured["project"] == str(project_dir)


# ── Integration-style tests ────────────────────────────────────────────────


class TestIntegration:
    """Integration tests verifying end-to-end behavior."""

    def test_backend_cmd_generates_valid_prompt_with_plan(self, tmp_path):
        """Backend cmd lambdas produce commands containing plan content."""
        plan = tmp_path / "plan.md"
        plan.write_text("IMPLEMENT_FEATURE_XYZ")
        for b in BACKENDS:
            cmd = b["cmd"]("/proj", str(plan))
            # At least one element in cmd should contain the plan content
            full = " ".join(cmd)
            assert "IMPLEMENT_FEATURE_XYZ" in full, f"{b['name']} cmd missing plan content"

    def test_fallback_chain_order(self, tmp_path, capsys):
        """Backends are tried in order: gemini → codex → opencode."""
        plan = tmp_path / "plan.md"
        plan.write_text("task")

        attempted = []
        original = _mod["run_backend"]

        def track_backend(backend, project, prompt_file, output_file):
            attempted.append(backend["name"])
            return False

        _mod["run_backend"] = track_backend
        try:
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["plan-exec", str(plan)]):
                    main()
        finally:
            _mod["run_backend"] = original

        assert attempted == ["gemini", "codex", "opencode"]
