from __future__ import annotations

"""Tests for effectors/gap_junction_sync — bash wrapper + Python _cli."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "gap_junction_sync"
MODULE = Path(__file__).parent.parent / "metabolon" / "organelles" / "gap_junction.py"


def _load_module():
    """Load gap_junction.py via exec for _cli unit testing."""
    source = MODULE.read_text()
    ns: dict = {"__name__": "gap_junction_test"}
    exec(source, ns)
    return ns


# ── Bash script structure and integration tests ─────────────────────────


class TestBashScript:
    """Tests for the gap_junction_sync bash wrapper."""

    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_shebang_is_bash(self):
        lines = SCRIPT.read_text().splitlines()
        assert lines[0] == "#!/bin/bash"

    def test_sets_pythonpath_to_germline(self):
        content = SCRIPT.read_text()
        assert 'PYTHONPATH="${HOME}/germline' in content

    def test_execs_correct_module(self):
        content = SCRIPT.read_text()
        assert "exec python3 -m metabolon.organelles.gap_junction" in content

    def test_passes_sync_catchup_args(self):
        content = SCRIPT.read_text()
        assert "sync catchup" in content

    def test_no_arg_forwarding(self):
        """Script does not forward caller $@ or $* to python."""
        content = SCRIPT.read_text()
        for line in content.splitlines():
            if line.startswith("#"):
                continue
            assert "$@" not in line
            assert "$*" not in line

    def test_invokes_python3_with_correct_args(self, tmp_path):
        """Verify the script passes -m module sync catchup to python3."""
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text('#!/bin/bash\necho "INVOKED: $@"\n')
        fake_python.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert "INVOKED: -m metabolon.organelles.gap_junction sync catchup" in r.stdout

    def test_pythonpath_includes_home_germline(self, tmp_path):
        """Verify PYTHONPATH is set to $HOME/germline."""
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text('#!/bin/bash\necho "PP=$PYTHONPATH"\n')
        fake_python.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
        env["HOME"] = str(tmp_path / "myhome")

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert f"{tmp_path}/myhome/germline" in r.stdout


# ── Python _cli unit tests ─────────────────────────────────────────────


class TestCliSyncCatchup:
    """Tests for _cli() sync catchup behavior via exec."""

    @staticmethod
    def _mod():
        """Fresh module load per test to avoid state pollution."""
        return _load_module()

    def test_success_prints_result(self, capsys):
        """_cli prints wacli sync result on stdout."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="sync complete")
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()
        assert "sync complete" in capsys.readouterr().out

    def test_calls_wacli_with_sync_once(self):
        """_cli calls _wacli(['sync', '--once'], timeout=120)."""
        mod = self._mod()
        mock_wacli = MagicMock(return_value="ok")
        mod["_wacli"] = mock_wacli
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()
        mock_wacli.assert_called_once_with(["sync", "--once"], timeout=120)

    def test_empty_result_prints_empty_line(self, capsys):
        """_cli prints empty string when sync returns empty."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="")
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()
        out = capsys.readouterr().out
        assert out.strip() == ""

    def test_no_exit_on_success(self):
        """_cli does not call sys.exit on success."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(return_value="ok")
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            mod["_cli"]()  # no SystemExit raised

    def test_store_locked_exits_0(self):
        """_cli exits 0 when wacli reports store is locked."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("store is locked by daemon"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 0

    def test_store_locked_stderr_message(self, capsys):
        """_cli prints 'daemon is running' to stderr when store is locked."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("store is locked"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        assert "daemon is running" in capsys.readouterr().err

    def test_other_valueerror_exits_1(self):
        """_cli exits 1 for non-locked ValueError."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("connection refused"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 1

    def test_error_message_on_stderr(self, capsys):
        """_cli prints error details to stderr for non-locked errors."""
        mod = self._mod()
        mod["_wacli"] = MagicMock(side_effect=ValueError("connection refused"))
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        assert "connection refused" in capsys.readouterr().err


class TestCliWrongArgs:
    """Tests for _cli() with invalid arguments."""

    @staticmethod
    def _mod():
        return _load_module()

    def test_no_args_exits_2(self):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_wrong_args_exits_2(self):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction", "foo", "bar"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_partial_args_exits_2(self):
        """Only 'sync' without 'catchup' is not valid."""
        mod = self._mod()
        with patch("sys.argv", ["gap_junction", "sync"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_extra_args_exits_2(self):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction", "sync", "catchup", "extra"]):
            with pytest.raises(SystemExit) as exc:
                mod["_cli"]()
        assert exc.value.code == 2

    def test_usage_message_on_stderr(self, capsys):
        mod = self._mod()
        with patch("sys.argv", ["gap_junction"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        err = capsys.readouterr().err
        assert "usage" in err.lower()
        assert "gap_junction" in err

    def test_wrong_args_does_not_call_wacli(self):
        """_cli never calls _wacli when args are wrong."""
        mod = self._mod()
        mock_wacli = MagicMock()
        original_wacli = mod["_wacli"]
        mod["_wacli"] = mock_wacli
        with patch("sys.argv", ["gap_junction", "bad"]):
            with pytest.raises(SystemExit):
                mod["_cli"]()
        mock_wacli.assert_not_called()
