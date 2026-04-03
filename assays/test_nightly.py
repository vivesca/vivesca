from __future__ import annotations

"""Tests for effectors/nightly — system health dashboard + flywheel report."""

import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ── Load effector via exec (never import) ─────────────────────────────────────

_NIGHTLY_PATH = Path(__file__).resolve().parents[1] / "effectors" / "nightly"
_NIGHTLY_CODE = _NIGHTLY_PATH.read_text()
_mod: dict = {"__name__": "nightly", "__file__": str(_NIGHTLY_PATH)}
exec(_NIGHTLY_CODE, _mod)


class _M:
    """Proxy that reads/writes the exec'd module dict."""

    def __getattr__(self, name):
        return _mod[name]

    def __setattr__(self, name, value):
        _mod[name] = value


nightly = _M()


@contextlib.contextmanager
def _patch_attr(name, value):
    """Temporarily set a top-level name in the exec'd module dict."""
    old = _mod.get(name)
    _mod[name] = value
    try:
        yield
    finally:
        if old is None:
            _mod.pop(name, None)
        else:
            _mod[name] = old


def _setup_home(tmp_path):
    """Patch HOME, HEALTH_OUT, FLYWHEEL_OUT, _MEMORY_DIR to tmp_path and return output paths."""
    health_out = tmp_path / ".claude" / "nightly-health.md"
    flywheel_out = tmp_path / ".claude" / "skill-flywheel-daily.md"
    health_out.parent.mkdir(parents=True, exist_ok=True)
    flywheel_out.parent.mkdir(parents=True, exist_ok=True)
    _mod["HOME"] = tmp_path
    _mod["HEALTH_OUT"] = health_out
    _mod["FLYWHEEL_OUT"] = flywheel_out
    home_stem = str(tmp_path).strip("/").replace("/", "-")
    _mod["_MEMORY_DIR"] = tmp_path / ".claude" / "projects" / f"-{home_stem}" / "memory"
    return health_out, flywheel_out


# ── Script structure tests ────────────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert _NIGHTLY_PATH.exists()

    def test_has_python_shebang(self):
        first = _NIGHTLY_PATH.read_text().splitlines()[0]
        assert "python" in first.lower()

    def test_has_main_guard(self):
        assert 'if __name__ == "__main__"' in _NIGHTLY_CODE


# ── _line_count ───────────────────────────────────────────────────────────────


class TestLineCount:
    def test_counts_lines(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        assert nightly._line_count(f) == 3

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert nightly._line_count(f) == 0

    def test_missing_file_returns_none(self, tmp_path):
        assert nightly._line_count(tmp_path / "nope.txt") is None


# ── _run ──────────────────────────────────────────────────────────────────────


class TestRun:
    def test_returns_stdout(self):
        mock_result = MagicMock()
        mock_result.stdout = "  hello world  \n"
        with _patch_attr("subprocess", MagicMock(run=lambda *a, **kw: mock_result)):
            assert nightly._run(["echo", "test"]) == "hello world"

    def test_returns_error_on_exception(self):
        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired("cmd", 10)

        with _patch_attr("subprocess", MagicMock(run=raise_timeout)):
            result = nightly._run(["slow"])
            assert result.startswith("error:")


# ── _file_age_minutes ─────────────────────────────────────────────────────────


class TestFileAgeMinutes:
    def test_returns_age(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        age = nightly._file_age_minutes(f)
        assert age is not None
        assert age >= 0

    def test_missing_file_returns_none(self, tmp_path):
        assert nightly._file_age_minutes(tmp_path / "nope") is None


# ── _is_running ───────────────────────────────────────────────────────────────


class TestIsRunning:
    def test_returns_true_when_label_present(self):
        mock_result = MagicMock()
        mock_result.stdout = "active\n"
        with _patch_attr("subprocess", MagicMock(run=lambda *a, **kw: mock_result)):
            assert nightly._is_running("com.vivesca.mcp") is True

    def test_returns_false_when_label_absent(self):
        mock_result = MagicMock()
        mock_result.stdout = "12345 0  com.apple.system\n"
        with _patch_attr("subprocess", MagicMock(run=lambda *a, **kw: mock_result)):
            assert nightly._is_running("com.vivesca.mcp") is False

    def test_returns_false_on_exception(self):
        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired("launchctl", 5)

        with _patch_attr("subprocess", MagicMock(run=raise_timeout)):
            assert nightly._is_running("anything") is False


# ── check_health ──────────────────────────────────────────────────────────────


class TestCheckHealth:
    def _make_mem_file(self, tmp_path, n_lines):
        mem = _mod["_MEMORY_DIR"] / "MEMORY.md"
        mem.parent.mkdir(parents=True, exist_ok=True)
        mem.write_text("\n".join(["line"] * n_lines))
        return mem

    def test_memory_md_ok(self, tmp_path):
        _setup_home(tmp_path)
        self._make_mem_file(tmp_path, 100)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 1
        assert mem_rows[0][2] == "ok"

    def test_memory_md_warn(self, tmp_path):
        _setup_home(tmp_path)
        self._make_mem_file(tmp_path, 160)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 1
        assert mem_rows[0][2] == "warn"

    def test_memory_md_red(self, tmp_path):
        _setup_home(tmp_path)
        self._make_mem_file(tmp_path, 250)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 1
        assert mem_rows[0][2] == "red"

    def test_memory_md_missing_gives_no_row(self, tmp_path):
        _setup_home(tmp_path)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        mem_rows = [r for r in rows if r[0] == "MEMORY.md lines"]
        assert len(mem_rows) == 0

    def test_mcp_server_down(self, tmp_path):
        _setup_home(tmp_path)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        mcp_rows = [r for r in rows if r[0] == "MCP server"]
        assert len(mcp_rows) == 1
        assert mcp_rows[0][1] == "DOWN"
        assert mcp_rows[0][2] == "red"

    def test_mcp_server_running(self, tmp_path):
        _setup_home(tmp_path)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        mcp_rows = [r for r in rows if r[0] == "MCP server"]
        assert len(mcp_rows) == 1
        assert mcp_rows[0][1] == "running"
        assert mcp_rows[0][2] == "ok"

    def test_agent_browser_profile_present(self, tmp_path):
        _setup_home(tmp_path)
        (tmp_path / ".agent-browser-profile").mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        abp_rows = [r for r in rows if r[0] == "Agent-browser profile"]
        assert len(abp_rows) == 1
        assert abp_rows[0][1] == "present"
        assert abp_rows[0][2] == "ok"

    def test_agent_browser_profile_missing(self, tmp_path):
        _setup_home(tmp_path)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        abp_rows = [r for r in rows if r[0] == "Agent-browser profile"]
        assert len(abp_rows) == 1
        assert abp_rows[0][1] == "missing"
        assert abp_rows[0][2] == "warn"

    def test_op_env_cache_present(self, tmp_path):
        _setup_home(tmp_path)
        cache_dir = tmp_path / "tmp"
        cache_dir.mkdir()
        cache_file = cache_dir / "op-env-cache.sh"
        cache_file.write_text("export FOO=bar\n" * 20)  # > 100 bytes

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess), \
             patch("tempfile.gettempdir", return_value=str(cache_dir)):
            rows = nightly.check_health()
        op_rows = [r for r in rows if r[0] == "op-env-cache"]
        assert len(op_rows) == 1
        assert op_rows[0][2] == "ok"

    def test_op_env_cache_too_small_is_red(self, tmp_path):
        _setup_home(tmp_path)
        cache_dir = tmp_path / "tmp"
        cache_dir.mkdir()
        cache_file = cache_dir / "op-env-cache.sh"
        cache_file.write_text("x")  # < 100 bytes

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess), \
             patch("tempfile.gettempdir", return_value=str(cache_dir)):
            rows = nightly.check_health()
        op_rows = [r for r in rows if r[0] == "op-env-cache"]
        assert len(op_rows) == 1
        assert op_rows[0][2] == "red"

    def test_op_env_cache_missing(self, tmp_path):
        _setup_home(tmp_path)
        cache_dir = tmp_path / "tmp"
        cache_dir.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess), \
             patch("tempfile.gettempdir", return_value=str(cache_dir)):
            rows = nightly.check_health()
        op_rows = [r for r in rows if r[0] == "op-env-cache"]
        assert len(op_rows) == 1
        assert op_rows[0][2] == "warn"

    def test_vault_sync_ok(self, tmp_path):
        _setup_home(tmp_path)
        vault_dir = tmp_path / "epigenome" / "chromatin" / ".obsidian"
        vault_dir.mkdir(parents=True)
        ws = vault_dir / "workspace.json"
        ws.write_text("{}")

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        vault_rows = [r for r in rows if r[0] == "Vault sync"]
        assert len(vault_rows) == 1
        assert vault_rows[0][2] == "ok"

    def test_vault_sync_stale_warns(self, tmp_path):
        _setup_home(tmp_path)
        vault_dir = tmp_path / "epigenome" / "chromatin" / ".obsidian"
        vault_dir.mkdir(parents=True)
        ws = vault_dir / "workspace.json"
        ws.write_text("{}")
        old_time = time.time() - 180 * 60
        os.utime(ws, (old_time, old_time))

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        vault_rows = [r for r in rows if r[0] == "Vault sync"]
        assert len(vault_rows) == 1
        assert vault_rows[0][2] == "warn"

    def test_hook_fires_counted(self, tmp_path):
        _setup_home(tmp_path)
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        hook_log = log_dir / "hooks.jsonl"
        now = time.time()
        entries = [json.dumps({"ts": now - i * 100, "action": "test"}) for i in range(5)]
        hook_log.write_text("\n".join(entries) + "\n")

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        hook_rows = [r for r in rows if r[0] == "Hook fires (24h)"]
        assert len(hook_rows) == 1
        assert hook_rows[0][1] == "5"

    def test_dr_sync_ok(self, tmp_path):
        _setup_home(tmp_path)
        dr_marker = tmp_path / ".cache" / "mitosis-last-sync"
        dr_marker.parent.mkdir(parents=True, exist_ok=True)
        dr_marker.write_text("sync")

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(stdout="active\n")
        with _patch_attr("subprocess", mock_subprocess):
            rows = nightly.check_health()
        dr_rows = [r for r in rows if r[0] == "DR sync"]
        assert len(dr_rows) == 1
        assert dr_rows[0][2] == "ok"


# ── write_health ──────────────────────────────────────────────────────────────


class TestWriteHealth:
    def test_writes_markdown_table(self, tmp_path):
        health_out, _ = _setup_home(tmp_path)

        rows = [
            ("MEMORY.md lines", "50/150", "ok"),
            ("MCP server", "running", "ok"),
            ("Agent-browser profile", "missing", "warn"),
        ]
        with patch("builtins.print"):
            nightly.write_health(rows)

        content = health_out.read_text()
        assert "| Metric | Value | Status |" in content
        assert "MEMORY.md lines" in content
        assert "MCP server" in content
        assert "Agent-browser profile" in content

    def test_contains_today_date(self, tmp_path):
        health_out, _ = _setup_home(tmp_path)

        with patch("builtins.print"):
            nightly.write_health([("Test", "val", "ok")])

        content = health_out.read_text()
        from datetime import datetime
        assert datetime.now().strftime("%Y-%m-%d") in content

    def test_auto_fix_op_env_cache(self, tmp_path):
        health_out, _ = _setup_home(tmp_path)

        rows = [("op-env-cache", "0B", "red")]
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(returncode=0)

        with _patch_attr("subprocess", mock_subprocess), \
             patch("builtins.print"):
            nightly.write_health(rows)

        content = health_out.read_text()
        assert "Auto-fixes" in content

    def test_no_auto_fix_when_ok(self, tmp_path):
        health_out, _ = _setup_home(tmp_path)

        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = MagicMock(returncode=0)
        with _patch_attr("subprocess", mock_subprocess), \
             patch("builtins.print"):
            nightly.write_health([("MEMORY.md lines", "50/150", "ok")])

        content = health_out.read_text()
        assert "Auto-fixes" not in content

    def test_status_icons(self, tmp_path):
        health_out, _ = _setup_home(tmp_path)

        rows = [
            ("ok_item", "val1", "ok"),
            ("warn_item", "val2", "warn"),
            ("red_item", "val3", "red"),
        ]
        with patch("builtins.print"):
            nightly.write_health(rows)

        content = health_out.read_text()
        assert "✅" in content
        assert "⚠️" in content
        assert "❌" in content


# ── write_flywheel ────────────────────────────────────────────────────────────


class TestWriteFlywheel:
    def test_writes_flywheel_report(self, tmp_path):
        _, flywheel_out = _setup_home(tmp_path)

        with patch("builtins.print"):
            nightly.write_flywheel()

        content = flywheel_out.read_text()
        assert "Skill Flywheel" in content
        assert "Mechanical Report" in content

    def test_flywheel_contains_today_date(self, tmp_path):
        _, flywheel_out = _setup_home(tmp_path)

        with patch("builtins.print"):
            nightly.write_flywheel()

        content = flywheel_out.read_text()
        from datetime import datetime
        assert datetime.now().strftime("%Y-%m-%d") in content


# ── main ──────────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_runs_all(self, tmp_path, capsys):
        _setup_home(tmp_path)

        mock_wh = MagicMock()
        mock_wf = MagicMock()
        with _patch_attr("check_health", MagicMock(return_value=[("Test", "val", "ok")])), \
             _patch_attr("write_health", mock_wh), \
             _patch_attr("write_flywheel", mock_wf):
            nightly.main()
            mock_wh.assert_called_once()
            mock_wf.assert_called_once()

        out = capsys.readouterr().out
        assert "Nightly run" in out
        assert "Done" in out

    def test_main_prints_banner(self, tmp_path, capsys):
        _setup_home(tmp_path)

        with _patch_attr("check_health", MagicMock(return_value=[])), \
             _patch_attr("write_health", MagicMock()), \
             _patch_attr("write_flywheel", MagicMock()):
            nightly.main()

        out = capsys.readouterr().out
        assert "Running health checks" in out
        assert "Running skill flywheel" in out


# ── health_to_json ─────────────────────────────────────────────────────────────


class TestHealthToJson:
    def test_produces_valid_json(self):
        rows = [("MEMORY.md lines", "50/150", "ok")]
        result = nightly.health_to_json(rows)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_json_fields(self):
        rows = [("MCP server", "running", "ok")]
        result = nightly.health_to_json(rows)
        parsed = json.loads(result)
        entry = parsed[0]
        assert entry["component"] == "MCP server"
        assert entry["status"] == "ok"
        assert entry["details"] == "running"

    def test_json_multiple_rows(self):
        rows = [
            ("MEMORY.md lines", "50/150", "ok"),
            ("MCP server", "DOWN", "red"),
            ("Agent-browser profile", "missing", "warn"),
        ]
        result = nightly.health_to_json(rows)
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["component"] == "MEMORY.md lines"
        assert parsed[1]["status"] == "red"
        assert parsed[2]["details"] == "missing"

    def test_json_empty_rows(self):
        result = nightly.health_to_json([])
        parsed = json.loads(result)
        assert parsed == []

    def test_json_is_pretty_printed(self):
        rows = [("Test", "val", "ok")]
        result = nightly.health_to_json(rows)
        assert "\n" in result  # indent=2 produces newlines


# ── main --json ────────────────────────────────────────────────────────────────


class TestMainJson:
    def test_json_flag_outputs_json(self, tmp_path, capsys):
        _setup_home(tmp_path)

        test_rows = [("MEMORY.md lines", "50/150", "ok")]
        with patch.object(sys, "argv", ["nightly", "--json"]), \
             _patch_attr("check_health", MagicMock(return_value=test_rows)):
            nightly.main()

        out = capsys.readouterr().out
        # Skip the "[nightly] Running health checks..." line
        json_lines = [l for l in out.strip().splitlines() if not l.startswith("[nightly]")]
        parsed = json.loads("\n".join(json_lines))
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["component"] == "MEMORY.md lines"
        assert parsed[0]["status"] == "ok"
        assert parsed[0]["details"] == "50/150"

    def test_json_flag_skips_file_writes(self, tmp_path, capsys):
        health_out, flywheel_out = _setup_home(tmp_path)

        with patch.object(sys, "argv", ["nightly", "--json"]), \
             _patch_attr("check_health", MagicMock(return_value=[("Test", "val", "ok")])):
            nightly.main()

        assert not health_out.exists()
        assert not flywheel_out.exists()

    def test_json_flag_no_banner(self, tmp_path, capsys):
        _setup_home(tmp_path)

        with patch.object(sys, "argv", ["nightly", "--json"]), \
             _patch_attr("check_health", MagicMock(return_value=[("Test", "val", "ok")])):
            nightly.main()

        out = capsys.readouterr().out
        assert "=== Nightly run" not in out


# ── Integration: subprocess execution ─────────────────────────────────────────


class TestSubprocessExecution:
    def test_script_runs_without_error(self):
        result = subprocess.run(
            [sys.executable, str(_NIGHTLY_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Nightly run" in result.stdout

    def test_json_flag_subprocess(self):
        result = subprocess.run(
            [sys.executable, str(_NIGHTLY_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        # Find the JSON output (after the "[nightly] Running health checks..." line)
        lines = result.stdout.strip().splitlines()
        # Skip the "[nightly] Running health checks..." line, parse the rest as JSON
        json_lines = [l for l in lines if not l.startswith("[nightly]")]
        json_text = "\n".join(json_lines)
        parsed = json.loads(json_text)
        assert isinstance(parsed, list)
        for entry in parsed:
            assert "component" in entry
            assert "status" in entry
            assert "details" in entry
