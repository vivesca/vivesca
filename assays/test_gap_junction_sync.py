from __future__ import annotations
"""Tests for effectors/gap_junction_sync — bash wrapper script.

Effectors are scripts, not importable modules. We test via:
  1. Static analysis of script content (shebang, PYTHONPATH, exec line)
  2. Subprocess invocation with mocked python3 (to test arg forwarding)
"""

import os
import stat
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "gap_junction_sync"


# ── Static content tests ────────────────────────────────────────────────


def _read_script() -> str:
    return EFFECTOR.read_text()


def test_script_exists():
    """Effector file exists."""
    assert EFFECTOR.exists()


def test_script_is_executable():
    """Effector is executable."""
    assert os.access(EFFECTOR, os.X_OK)


def test_script_has_bash_shebang():
    """Script starts with #!/bin/bash (or #!/usr/bin/env bash)."""
    first_line = _read_script().splitlines()[0]
    assert first_line.startswith("#!") and "bash" in first_line


def test_script_sets_pythonpath():
    """Script exports PYTHONPATH including ~/germline."""
    content = _read_script()
    assert "PYTHONPATH" in content
    assert "germline" in content


def test_script_execs_correct_module():
    """Script execs python3 -m metabolon.organelles.gap_junction."""
    content = _read_script()
    assert "metabolon.organelles.gap_junction" in content
    assert "sync" in content
    assert "catchup" in content


def test_script_uses_exec():
    """Script uses exec to replace the shell process."""
    content = _read_script()
    assert "exec " in content


def test_script_no_bash_array_or_loop():
    """Script is simple — no arrays, loops, or conditionals."""
    content = _read_script()
    for keyword in ("for ", "while ", "if ", "case ", "declare ", "local "):
        assert keyword not in content


# ── Subprocess invocation tests (mocked python3) ───────────────────────


class TestSubprocessInvocation:
    """Test actual script execution with mocked python3."""

    def test_invokes_python3_with_sync_catchup(self, tmp_path):
        """Script passes 'sync catchup' to python3 -m gap_junction."""
        # Create a fake python3 that records its arguments
        recorder = tmp_path / "python3"
        recorder.write_text(
            '#!/bin/bash\n'
            'echo "$@" > "$0.rec"\n'
        )
        recorder.chmod(0o755)
        rec_file = tmp_path / "python3.rec"

        env = os.environ.copy()
        env["PATH"] = str(tmp_path) + ":" + env.get("PATH", "")
        env["HOME"] = str(tmp_path)
        (tmp_path / "germline").mkdir()

        result = subprocess.run(
            ["/usr/bin/bash", str(EFFECTOR)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Our fake python3 should have been called
        assert rec_file.exists(), "python3 was never invoked"
        args = rec_file.read_text().strip()
        assert "-m" in args
        assert "metabolon.organelles.gap_junction" in args
        assert "sync" in args
        assert "catchup" in args

    def test_script_exits_on_missing_python3(self, tmp_path):
        """Script fails cleanly when python3 is unavailable."""
        env = os.environ.copy()
        env["PATH"] = str(tmp_path)  # Empty dir, no python3
        env["HOME"] = str(tmp_path)
        (tmp_path / "germline").mkdir()

        result = subprocess.run(
            ["/usr/bin/bash", str(EFFECTOR)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should fail (non-zero exit) because python3 not found
        assert result.returncode != 0


# ── Integration with underlying module ──────────────────────────────────


def _load_module():
    """Load gap_junction module via exec (effector pattern)."""
    source = Path.home().joinpath(
        "germline", "metabolon", "organelles", "gap_junction.py"
    ).read_text()
    ns = {"__name__": "gap_junction_test"}
    exec(source, ns)
    return ns


_mod = _load_module()
_cli = _mod["_cli"]
sync_catchup = _mod["sync_catchup"]


class TestModuleCliSyncCatchup:
    """Test the underlying _cli() handles 'sync catchup' correctly."""

    def test_cli_sync_catchup_calls_sync_catchup(self, capsys, monkeypatch):
        """_cli dispatches 'sync catchup' to sync_catchup()."""
        original = _mod["sync_catchup"]
        _mod["sync_catchup"] = lambda: "synced OK"
        monkeypatch.setattr("sys.argv", ["gap_junction", "sync", "catchup"])
        try:
            _cli()
        finally:
            _mod["sync_catchup"] = original
        out = capsys.readouterr().out
        assert "synced OK" in out

    def test_cli_sync_catchup_locked_exits_zero(self, capsys, monkeypatch):
        """_cli exits 0 when wacli store is locked (daemon already running)."""
        original = _mod["sync_catchup"]
        _mod["sync_catchup"] = lambda: (_ for _ in ()).throw(ValueError("store is locked"))
        monkeypatch.setattr("sys.argv", ["gap_junction", "sync", "catchup"])
        try:
            with pytest.raises(SystemExit) as exc_info:
                _cli()
        finally:
            _mod["sync_catchup"] = original
        assert exc_info.value.code == 0
        err = capsys.readouterr().err
        assert "daemon is running" in err

    def test_cli_sync_catchup_value_error_exits_1(self, capsys, monkeypatch):
        """_cli exits 1 on generic ValueError from sync_catchup."""
        original = _mod["sync_catchup"]
        _mod["sync_catchup"] = lambda: (_ for _ in ()).throw(ValueError("something broke"))
        monkeypatch.setattr("sys.argv", ["gap_junction", "sync", "catchup"])
        try:
            with pytest.raises(SystemExit) as exc_info:
                _cli()
        finally:
            _mod["sync_catchup"] = original
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "something broke" in err

    def test_cli_wrong_args_exits_2(self, capsys, monkeypatch):
        """_cli exits 2 with usage message for wrong arguments."""
        monkeypatch.setattr("sys.argv", ["gap_junction", "bad", "args"])
        with pytest.raises(SystemExit) as exc_info:
            _cli()
        assert exc_info.value.code == 2
        err = capsys.readouterr().err
        assert "usage" in err

    def test_cli_no_args_exits_2(self, capsys, monkeypatch):
        """_cli exits 2 when called with no arguments."""
        monkeypatch.setattr("sys.argv", ["gap_junction"])
        with pytest.raises(SystemExit) as exc_info:
            _cli()
        assert exc_info.value.code == 2
        err = capsys.readouterr().err
        assert "usage" in err
