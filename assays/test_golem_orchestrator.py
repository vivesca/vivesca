from __future__ import annotations

"""Tests for golem-orchestrator — Switch between golem-daemon, Hatchet, and Temporal backends."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


def _load_orchestrator():
    """Load the golem-orchestrator module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/golem-orchestrator")).read()
    # Provide __file__ so Path(__file__) works
    ns: dict = {
        "__name__": "golem_orchestrator",
        "__file__": str(Path.home() / "germline/effectors/golem-orchestrator"),
    }
    exec(source, ns)
    return ns


_mod = _load_orchestrator()
_source_env = _mod["_source_env"]
_docker = _mod["_docker"]
_find_worker_pid = _mod["_find_worker_pid"]
_is_running = _mod["_is_running"]
cmd_status = _mod["cmd_status"]
cmd_stop = _mod["cmd_stop"]
cmd_start = _mod["cmd_start"]
cmd_switch = _mod["cmd_switch"]
cmd_dispatch = _mod["cmd_dispatch"]
BACKENDS = _mod["BACKENDS"]
WORKER_PIDFILES = _mod["WORKER_PIDFILES"]
main = _mod["main"]


# ── Constants tests ─────────────────────────────────────────────────────


def test_backends_constant():
    """BACKENDS contains expected values."""
    assert "daemon" in BACKENDS
    assert "hatchet" in BACKENDS
    assert "temporal" in BACKENDS
    assert len(BACKENDS) == 3


def test_worker_pidfiles_paths():
    """WORKER_PIDFILES has correct keys and paths under LOG_DIR."""
    assert "hatchet" in WORKER_PIDFILES
    assert "temporal" in WORKER_PIDFILES
    # Paths should be under user home directory structure
    for backend, path in WORKER_PIDFILES.items():
        assert "hatchet-worker.pid" in str(path) or "temporal-worker.pid" in str(path)


# ── _source_env tests ───────────────────────────────────────────────────


def test_source_env_returns_dict():
    """_source_env returns a dictionary."""
    result = _source_env()
    assert isinstance(result, dict)


def test_source_env_includes_os_environ():
    """_source_env includes current environment variables."""
    with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
        result = _source_env()
        assert result["TEST_VAR"] == "test_value"


def test_source_env_parses_export_lines():
    """_source_env parses export lines from .env.fly."""
    env_content = """
export API_KEY="secret123"
export DB_HOST='localhost'
"""
    with patch("os.path.exists", return_value=True),          patch("builtins.open", mock_open(read_data=env_content)):
        result = _source_env()
        assert result.get("API_KEY") == "secret123"
        assert result.get("DB_HOST") == "localhost"


def test_source_env_handles_missing_file():
    """_source_env handles missing .env.fly gracefully."""
    with patch("os.path.exists", return_value=False):
        result = _source_env()
        assert isinstance(result, dict)


def test_source_env_skips_non_export_lines():
    """_source_env skips lines that are not export statements."""
    env_content = """
# This is a comment
API_KEY=no_export_prefix
export VALID_KEY="valid"
"""
    with patch("os.path.exists", return_value=True),          patch("builtins.open", mock_open(read_data=env_content)):
        result = _source_env()
        assert "VALID_KEY" in result
        # Non-export line should not be parsed
        assert result.get("API_KEY") != "no_export_prefix"


# ── _docker tests ───────────────────────────────────────────────────────


def test_docker_runs_sg_docker():
    """_docker runs command via sg docker."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        _docker("ps")
        
        # Verify sg docker -c "docker ps" was called
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "sg"
        assert call_args[1] == "docker"
        assert "docker ps" in call_args[3]


def test_docker_returns_completed_process():
    """_docker returns a CompletedProcess."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="container1\n", stderr=""
        )
        result = _docker("ps")
        assert result.returncode == 0
        assert "container1" in result.stdout


def test_docker_handles_multiple_args():
    """_docker handles multiple arguments."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        _docker("compose", "up", "-d")
        
        call_args = mock_run.call_args[0][0]
        assert "docker compose up -d" in call_args[3]


# ── _find_worker_pid tests ──────────────────────────────────────────────


def test_find_worker_pid_returns_none_for_missing_pidfile():
    """_find_worker_pid returns None if pidfile does not exist."""
    with patch.object(Path, "exists", return_value=False):
        result = _find_worker_pid("hatchet")
        assert result is None


def test_find_worker_pid_returns_pid_from_file():
    """_find_worker_pid returns PID from pidfile if process alive."""
    with patch.object(Path, "exists", return_value=True),          patch.object(Path, "read_text", return_value="12345"),          patch("os.kill") as mock_kill:
        result = _find_worker_pid("hatchet")
        assert result == 12345
        # Should verify process is alive with signal 0
        mock_kill.assert_called_with(12345, 0)


def test_find_worker_pid_removes_stale_pidfile():
    """_find_worker_pid removes pidfile if process is dead."""
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.read_text.return_value = "12345"
    
    with patch.dict(WORKER_PIDFILES, {"hatchet": mock_path}),          patch("os.kill", side_effect=ProcessLookupError):
        result = _find_worker_pid("hatchet")
        assert result is None
        mock_path.unlink.assert_called_once_with(missing_ok=True)


def test_find_worker_pid_handles_invalid_pid():
    """_find_worker_pid handles invalid PID in file."""
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.read_text.return_value = "not_a_number"
    
    with patch.dict(WORKER_PIDFILES, {"hatchet": mock_path}):
        result = _find_worker_pid("hatchet")
        assert result is None
        mock_path.unlink.assert_called_once_with(missing_ok=True)


# ── _is_running tests ───────────────────────────────────────────────────


def test_is_running_daemon_from_pidfile():
    """_is_running detects daemon via pidfile."""
    with patch.object(Path, "exists", return_value=True),          patch.object(Path, "read_text", return_value="9999"),          patch("os.kill") as mock_kill:
        result = _is_running("daemon")
        assert result is not None
        assert result["backend"] == "daemon"
        assert result["pid"] == 9999


def test_is_running_daemon_not_running():
    """_is_running returns None when daemon not running."""
    with patch.object(Path, "exists", return_value=False),          patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )
        result = _is_running("daemon")
        assert result is None


def test_is_running_daemon_from_pgrep():
    """_is_running detects daemon via pgrep when pidfile missing."""
    with patch.object(Path, "exists", return_value=False),          patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="8888
", stderr=""
        )
        result = _is_running("daemon")
        assert result is not None
        assert result["pid"] == 8888


def test_is_running_hatchet_with_containers():
    """_is_running detects hatchet with Docker containers."""
    with patch("subprocess.run") as mock_run,          patch.object(_mod, "_find_worker_pid", return_value=None):
        # Mock docker ps output
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="hatchet-golem-server
hatchet-golem-db
", stderr=""
        )
        result = _is_running("hatchet")
        assert result is not None
        assert result["backend"] == "hatchet"
        assert result["containers"] == 2


def test_is_running_hatchet_with_worker():
    """_is_running detects hatchet with worker PID."""
    with patch("subprocess.run") as mock_run,          patch.object(_mod, "_find_worker_pid", return_value=5555):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        result = _is_running("hatchet")
        assert result is not None
        assert result["worker_pid"] == 5555


def test_is_running_temporal_with_containers():
    """_is_running detects temporal with Docker containers."""
    with patch("subprocess.run") as mock_run,          patch.object(_mod, "_find_worker_pid", return_value=None):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="temporal-golem-server
", stderr=""
        )
        result = _is_running("temporal")
        assert result is not None
        assert result["backend"] == "temporal"
        assert result["containers"] == 1


def test_is_running_unknown_backend():
    """_is_running returns None for unknown backend."""
    result = _is_running("unknown")
    assert result is None


# ── cmd_status tests ────────────────────────────────────────────────────


def test_cmd_status_shows_all_backends(capsys):
    """cmd_status shows status for all backends."""
    with patch.object(_mod, "_is_running", return_value=None):
        cmd_status()
        captured = capsys.readouterr()
        assert "daemon" in captured.out
        assert "hatchet" in captured.out
        assert "temporal" in captured.out


def test_cmd_status_shows_running_backend(capsys):
    """cmd_status shows RUNNING for active backends."""
    def mock_is_running(backend):
        if backend == "daemon":
            return {"backend": "daemon", "pid": 12345}
        return None
    
    with patch.object(_mod, "_is_running", side_effect=mock_is_running):
        cmd_status()
        captured = capsys.readouterr()
        assert "RUNNING" in captured.out
        assert "stopped" in captured.out


# ── cmd_stop tests ───────────────────────────────────────────────────────


def test_cmd_stop_nothing_running(capsys):
    """cmd_stop handles when nothing is running."""
    with patch.object(_mod, "_is_running", return_value=None):
        cmd_stop("daemon")
        captured = capsys.readouterr()
        # Should not print anything when nothing running
        assert captured.out == ""


def test_cmd_stop_daemon():
    """cmd_stop stops daemon correctly."""
    with patch.object(_mod, "_is_running", return_value={"backend": "daemon", "pid": 9999}),          patch("subprocess.run") as mock_run,          patch("os.kill") as mock_kill,          patch("time.sleep"):
        cmd_stop("daemon")
        # Should call golem-daemon stop
        assert mock_run.called
        mock_kill.assert_called()


def test_cmd_stop_hatchet():
    """cmd_stop stops hatchet correctly."""
    with patch.object(_mod, "_is_running", return_value={
        "backend": "hatchet", "containers": 2, "worker_pid": 7777
    }),          patch("os.kill") as mock_kill,          patch.object(_mod, "_docker") as mock_docker,          patch("time.sleep"):
        mock_docker.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        cmd_stop("hatchet")
        # Should kill worker
        mock_kill.assert_called_with(7777, 15)  # SIGTERM
        # Should stop Docker compose
        mock_docker.assert_called()


def test_cmd_stop_temporal():
    """cmd_stop stops temporal correctly."""
    with patch.object(_mod, "_is_running", return_value={
        "backend": "temporal", "containers": 1, "worker_pid": 8888
    }),          patch("os.kill") as mock_kill,          patch.object(_mod, "_docker") as mock_docker,          patch("time.sleep"):
        mock_docker.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        cmd_stop("temporal")
        mock_kill.assert_called_with(8888, 15)  # SIGTERM
        mock_docker.assert_called()


def test_cmd_stop_all_backends():
    """cmd_stop with no arg stops all backends."""
    running = {
        "daemon": {"backend": "daemon", "pid": 1111},
        "hatchet": None,
        "temporal": {"backend": "temporal", "containers": 1, "worker_pid": 3333},
    }
    
    def mock_is_running(backend):
        return running.get(backend)
    
    with patch.object(_mod, "_is_running", side_effect=mock_is_running),          patch("subprocess.run") as mock_run,          patch("os.kill") as mock_kill,          patch.object(_mod, "_docker") as mock_docker,          patch("time.sleep"):
        mock_docker.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        cmd_stop(None)  # Stop all
        # Should have killed daemon and temporal worker
        assert mock_kill.call_count >= 2


# ── cmd_start tests ──────────────────────────────────────────────────────


def test_cmd_start_already_running(capsys):
    """cmd_start handles already running backend."""
    with patch.object(_mod, "_is_running", return_value={"backend": "daemon", "pid": 123}):
        cmd_start("daemon")
        captured = capsys.readouterr()
        assert "already running" in captured.out


def test_cmd_start_daemon():
    """cmd_start starts daemon correctly."""
    with patch.object(_mod, "_is_running", return_value=None),          patch("subprocess.Popen") as mock_popen,          patch.object(_mod, "_source_env", return_value={}):
        mock_popen.return_value = MagicMock(pid=54321)
        cmd_start("daemon")
        assert mock_popen.called
        # Check it was called with correct args
        call_args = mock_popen.call_args[0][0]
        assert "golem-daemon" in str(call_args)
        assert "start" in call_args


def test_cmd_start_hatchet():
    """cmd_start starts hatchet correctly."""
    mock_log = MagicMock()
    with patch.object(_mod, "_is_running", return_value=None),          patch("subprocess.Popen") as mock_popen,          patch.object(_mod, "_docker") as mock_docker,          patch.object(_mod, "_source_env", return_value={}),          patch("builtins.open", return_value=mock_log),          patch("time.sleep"):
        mock_docker.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        mock_popen.return_value = MagicMock(pid=65432)
        cmd_start("hatchet")
        # Should start Docker
        mock_docker.assert_called()
        # Should start worker
        assert mock_popen.called


def test_cmd_start_invalid_backend():
    """cmd_start raises error for invalid backend."""
    # Invalid backend name should be caught by caller (main)
    # cmd_start itself does not validate
    pass  # This is handled in main()


# ── cmd_switch tests ─────────────────────────────────────────────────────


def test_cmd_switch_stops_all_starts_backend():
    """cmd_switch stops all backends then starts the given one."""
    with patch.object(_mod, "cmd_stop") as mock_stop,          patch.object(_mod, "cmd_start") as mock_start,          patch("time.sleep"):
        cmd_switch("daemon")
        # Should stop all (None arg)
        mock_stop.assert_called_with(None)
        # Should start requested backend
        mock_start.assert_called_with("daemon")


# ── cmd_dispatch tests ───────────────────────────────────────────────────


def test_cmd_dispatch_no_backend_running():
    """cmd_dispatch exits when no backend running."""
    with patch.object(_mod, "_is_running", return_value=None),          pytest.raises(SystemExit):
        cmd_dispatch(None)


def test_cmd_dispatch_auto_detect_running_backend():
    """cmd_dispatch auto-detects running backend."""
    with patch.object(_mod, "_is_running", return_value={"backend": "daemon"}),          patch.object(_mod, "_source_env", return_value={}):
        # daemon just prints a message, does not subprocess
        cmd_dispatch(None)  # Should not raise


def test_cmd_dispatch_daemon_message(capsys):
    """cmd_dispatch for daemon prints automatic dispatch message."""
    with patch.object(_mod, "_is_running", return_value={"backend": "daemon"}),          patch.object(_mod, "_source_env", return_value={}):
        cmd_dispatch("daemon")
        captured = capsys.readouterr()
        assert "automatically" in captured.out


def test_cmd_dispatch_hatchet():
    """cmd_dispatch runs hatchet dispatch.py."""
    with patch.object(_mod, "_is_running", return_value={"backend": "hatchet"}),          patch.object(_mod, "_source_env", return_value={}),          patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        cmd_dispatch("hatchet")
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "dispatch.py" in str(call_args)


def test_cmd_dispatch_temporal():
    """cmd_dispatch runs temporal dispatch.py."""
    with patch.object(_mod, "_is_running", return_value={"backend": "temporal"}),          patch.object(_mod, "_source_env", return_value={}),          patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        cmd_dispatch("temporal")
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "dispatch.py" in str(call_args)


# ── main (CLI) tests ─────────────────────────────────────────────────────


def test_main_shows_help():
    """main shows help with -h or --help."""
    with patch("sys.argv", ["golem-orchestrator", "-h"]),          patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_called_with(0)


def test_main_shows_help_no_args():
    """main shows help with no args."""
    with patch("sys.argv", ["golem-orchestrator"]),          patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_called_with(0)


def test_main_status_command():
    """main calls cmd_status for status command."""
    with patch("sys.argv", ["golem-orchestrator", "status"]),          patch.object(_mod, "cmd_status") as mock_status:
        main()
        mock_status.assert_called_once()


def test_main_stop_command():
    """main calls cmd_stop for stop command."""
    with patch("sys.argv", ["golem-orchestrator", "stop"]),          patch.object(_mod, "cmd_stop") as mock_stop:
        main()
        mock_stop.assert_called_with(None)


def test_main_stop_specific_backend():
    """main calls cmd_stop with specific backend."""
    with patch("sys.argv", ["golem-orchestrator", "stop", "daemon"]),          patch.object(_mod, "cmd_stop") as mock_stop:
        main()
        mock_stop.assert_called_with("daemon")


def test_main_start_requires_backend():
    """main exits if start missing backend arg."""
    with patch("sys.argv", ["golem-orchestrator", "start"]),          pytest.raises(SystemExit):
        main()


def test_main_start_invalid_backend():
    """main exits if start given invalid backend."""
    with patch("sys.argv", ["golem-orchestrator", "start", "invalid"]),          pytest.raises(SystemExit):
        main()


def test_main_start_valid_backend():
    """main calls cmd_start with valid backend."""
    with patch("sys.argv", ["golem-orchestrator", "start", "daemon"]),          patch.object(_mod, "cmd_start") as mock_start:
        main()
        mock_start.assert_called_with("daemon")


def test_main_switch_requires_backend():
    """main exits if switch missing backend arg."""
    with patch("sys.argv", ["golem-orchestrator", "switch"]),          pytest.raises(SystemExit):
        main()


def test_main_switch_valid_backend():
    """main calls cmd_switch with valid backend."""
    with patch("sys.argv", ["golem-orchestrator", "switch", "temporal"]),          patch.object(_mod, "cmd_switch") as mock_switch:
        main()
        mock_switch.assert_called_with("temporal")


def test_main_dispatch_command():
    """main calls cmd_dispatch for dispatch command."""
    with patch("sys.argv", ["golem-orchestrator", "dispatch"]),          patch.object(_mod, "cmd_dispatch") as mock_dispatch:
        main()
        mock_dispatch.assert_called_with(None)


def test_main_dispatch_with_backend():
    """main calls cmd_dispatch with specific backend."""
    with patch("sys.argv", ["golem-orchestrator", "dispatch", "hatchet"]),          patch.object(_mod, "cmd_dispatch") as mock_dispatch:
        main()
        mock_dispatch.assert_called_with("hatchet")


def test_main_unknown_command():
    """main exits for unknown command."""
    with patch("sys.argv", ["golem-orchestrator", "unknown"]),          pytest.raises(SystemExit):
        main()
