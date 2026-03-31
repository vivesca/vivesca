"""Tests for effectors/nightly — system health dashboard + flywheel report."""

import importlib.util
import json
import subprocess
import tempfile
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "effectors" / "nightly"
    loader = SourceFileLoader("nightly", str(module_path))
    spec = importlib.util.spec_from_loader("nightly", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _setup_home(tmp_path, monkeypatch):
    """Patch module HOME, HEALTH_OUT, FLYWHEEL_OUT to use tmp_path."""
    mod = _load_module()
    monkeypatch.setattr(mod, "HOME", tmp_path)
    health_out = tmp_path / ".claude" / "nightly-health.md"
    flywheel_out = tmp_path / ".claude" / "skill-flywheel-daily.md"
    health_out.parent.mkdir(parents=True, exist_ok=True)
    flywheel_out.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "HEALTH_OUT", health_out)
    monkeypatch.setattr(mod, "FLYWHEEL_OUT", flywheel_out)
    return mod


# ── _line_count ───────────────────────────────────────────────────────────────


class TestLineCount:
    def test_counts_lines(self, tmp_path):
        mod = _load_module()
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        assert mod._line_count(f) == 3

    def test_empty_file(self, tmp_path):
        mod = _load_module()
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert mod._line_count(f) == 0

    def test_missing_file_returns_none(self, tmp_path):
        mod = _load_module()
        assert mod._line_count(tmp_path / "nope.txt") is None


# ── _run ──────────────────────────────────────────────────────────────────────


class TestRun:
    def test_returns_stdout(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.stdout = "  hello world  \n"
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        assert mod._run(["echo", "test"]) == "hello world"

    def test_returns_error_on_exception(self, monkeypatch):
        mod = _load_module()

        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired("cmd", 10)

        monkeypatch.setattr(mod.subprocess, "run", raise_timeout)
        result = mod._run(["slow"])
        assert result.startswith("error:")


# ── _file_age_minutes ────────────────────────────────────────────────────────


class TestFileAgeMinutes:
    def test_returns_age(self, tmp_path):
        mod = _load_module()
        f = tmp_path / "file.txt"
        f.write_text("x")
        age = mod._file_age_minutes(f)
        assert age is not None
        assert age >= 0

    def test_missing_file_returns_none(self, tmp_path):
        mod = _load_module()
        assert mod._file_age_minutes(tmp_path / "nope") is None


# ── _is_running ───────────────────────────────────────────────────────────────


class TestIsRunning:
    def test_returns_true_when_label_present(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.stdout = "12345 0  com.vivesca.mcp\n67890 0  com.apple.system\n"
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        assert mod._is_running("com.vivesca.mcp") is True

    def test_returns_false_when_label_absent(self, monkeypatch):
        mod = _load_module()
        mock_result = MagicMock()
        mock_result.stdout = "12345 0  com.apple.system\n"
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: mock_result)
        assert mod._is_running("com.vivesca.mcp") is False

    def test_returns_false_on_exception(self, monkeypatch):
        mod = _load_module()

        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired("launchctl", 5)

        monkeypatch.setattr(mod.subprocess, "run", raise_timeout)
        assert mod._is_running("anything") is False


# ── check_health ──────────────────────────────────────────────────────────────


class TestCheckHealth:
    def _make_mem_file(self, tmp_path, n_lines):
        mem = tmp_path / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"
        mem.parent.mkdir(parents=True, exist_ok=True)
        mem.write_text("\n".join(["line"] * n_lines))
        return mem

    def test_memory_md_ok(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        self._make_mem_file(tmp_path, 100)

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 1
        assert mem_rows[0][2] == "ok"

    def test_memory_md_warn(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        self._make_mem_file(tmp_path, 160)

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 1
        assert mem_rows[0][2] == "warn"

    def test_memory_md_red(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        self._make_mem_file(tmp_path, 250)

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 1
        assert mem_rows[0][2] == "red"

    def test_mcp_server_down(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")  # no MCP label
            rows = mod.check_health()
        mcp_rows = [r for r in rows if r[0] == "MCP server"]
        assert len(mcp_rows) == 1
        assert mcp_rows[0][1] == "DOWN"
        assert mcp_rows[0][2] == "red"

    def test_agent_browser_profile_present(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        (tmp_path / ".agent-browser-profile").mkdir()

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        abp_rows = [r for r in rows if r[0] == "Agent-browser profile"]
        assert len(abp_rows) == 1
        assert abp_rows[0][1] == "present"

    def test_agent_browser_profile_missing(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        abp_rows = [r for r in rows if r[0] == "Agent-browser profile"]
        assert len(abp_rows) == 1
        assert abp_rows[0][1] == "missing"

    def test_op_env_cache_present(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        cache_dir = tmp_path / "tmp"
        cache_dir.mkdir()
        cache_file = cache_dir / "op-env-cache.sh"
        cache_file.write_text("export FOO=bar\n" * 20)  # > 100 bytes

        with patch("tempfile.gettempdir", return_value=str(cache_dir)), \
             patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        op_rows = [r for r in rows if r[0] == "op-env-cache"]
        assert len(op_rows) == 1
        assert op_rows[0][2] == "ok"

    def test_op_env_cache_missing(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        cache_dir = tmp_path / "tmp"
        cache_dir.mkdir()

        with patch("tempfile.gettempdir", return_value=str(cache_dir)), \
             patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        op_rows = [r for r in rows if r[0] == "op-env-cache"]
        assert len(op_rows) == 1
        assert op_rows[0][2] == "warn"

    def test_vault_sync_stale_warns(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        vault_dir = tmp_path / "epigenome" / "chromatin" / ".obsidian"
        vault_dir.mkdir(parents=True)
        ws = vault_dir / "workspace.json"
        ws.write_text("{}")
        old_time = time.time() - 180 * 60
        import os
        os.utime(ws, (old_time, old_time))

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        vault_rows = [r for r in rows if r[0] == "Vault sync"]
        assert len(vault_rows) == 1
        assert vault_rows[0][2] == "warn"

    def test_hook_fires_counted(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        hook_log = log_dir / "hooks.jsonl"
        now = time.time()
        entries = [json.dumps({"ts": now - i * 100, "action": "test"}) for i in range(5)]
        hook_log.write_text("\n".join(entries) + "\n")

        with patch.object(mod.subprocess, "run") as mock_run:
            mock_run.return_value = MagicMock(stdout="com.vivesca.mcp\n")
            rows = mod.check_health()
        hook_rows = [r for r in rows if r[0] == "Hook fires (24h)"]
        assert len(hook_rows) == 1
        assert hook_rows[0][1] == "5"


# ── write_health ──────────────────────────────────────────────────────────────


class TestWriteHealth:
    def test_writes_markdown_table(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)

        rows = [
            ("MEMORY.md lines", "50/150", "ok"),
            ("MCP server", "running", "ok"),
            ("Agent-browser profile", "missing", "warn"),
        ]
        with patch("builtins.print"):
            mod.write_health(rows)

        content = mod.HEALTH_OUT.read_text()
        assert "| Metric | Value | Status |" in content
        assert "MEMORY.md lines" in content
        assert "MCP server" in content
        assert "Agent-browser profile" in content

    def test_auto_fix_op_env_cache(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)

        rows = [("op-env-cache", "0B", "red")]

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch.object(mod.subprocess, "run", return_value=mock_result), \
             patch("builtins.print"):
            mod.write_health(rows)

        content = mod.HEALTH_OUT.read_text()
        assert "Auto-fixes" in content

    def test_no_auto_fix_when_ok(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)

        rows = [("MEMORY.md lines", "50/150", "ok")]

        with patch.object(mod.subprocess, "run") as mock_run, \
             patch("builtins.print"):
            mod.write_health(rows)

        content = mod.HEALTH_OUT.read_text()
        assert "Auto-fixes" not in content


# ── write_flywheel ────────────────────────────────────────────────────────────


class TestWriteFlywheel:
    def test_writes_flywheel_report(self, tmp_path, monkeypatch):
        mod = _setup_home(tmp_path, monkeypatch)

        with patch("builtins.print"):
            mod.write_flywheel()

        content = mod.FLYWHEEL_OUT.read_text()
        assert "Skill Flywheel" in content
        assert "Mechanical Report" in content


# ── main ──────────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_runs_all(self, tmp_path, monkeypatch, capsys):
        mod = _setup_home(tmp_path, monkeypatch)

        with patch.object(mod, "check_health", return_value=[("Test", "val", "ok")]), \
             patch.object(mod, "write_health") as mock_wh, \
             patch.object(mod, "write_flywheel") as mock_wf:
            mod.main()
            mock_wh.assert_called_once()
            mock_wf.assert_called_once()

        out = capsys.readouterr().out
        assert "Nightly run" in out
        assert "Done" in out
