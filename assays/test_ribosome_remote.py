"""Tests for remote overflow execution in ribosome-daemon."""

import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Load ribosome-daemon as a namespace (it's an executable script, not a module)
# ---------------------------------------------------------------------------
_DAEMON_PATH = Path(__file__).resolve().parent.parent / "effectors" / "ribosome-daemon"
_ns: dict = {}
exec(open(_DAEMON_PATH).read(), _ns)
# Force home to /home/terry for consistent test paths
_ns["Path"] = Path

remote_exec = _ns["remote_exec"]
_ssh_health_check = _ns["_ssh_health_check"]
_running_entry_node = _ns["_running_entry_node"]
mark_done = _ns["mark_done"]
QUEUE_FILE = _ns["QUEUE_FILE"]
QueueLock = _ns["QueueLock"]
REMOTE_WORKERS = _ns["REMOTE_WORKERS"]
MAX_LOCAL = _ns["MAX_LOCAL"]
SSH_CONNECT_TIMEOUT = _ns["SSH_CONNECT_TIMEOUT"]
SSH_REMOTE_EXIT_CONNECT_FAIL = _ns["SSH_REMOTE_EXIT_CONNECT_FAIL"]


# ---------------------------------------------------------------------------
# _running_entry_node
# ---------------------------------------------------------------------------
class TestRunningEntryNode:
    def test_soma_default_5_element(self):
        entry = (1, "cmd", "provider", "task_id", "dispatch")
        assert _running_entry_node(entry) == "soma"

    def test_soma_default_6_element(self):
        entry = (1, "cmd", "provider", "task_id", "dispatch", 1.0)
        assert _running_entry_node(entry) == "soma"

    def test_ganglion_7_element(self):
        entry = (1, "cmd", "provider", "task_id", "dispatch", 1.0, "ganglion")
        assert _running_entry_node(entry) == "ganglion"

    def test_arbitrary_node(self):
        entry = (1, "cmd", "provider", "task_id", "dispatch", 1.0, "other-node")
        assert _running_entry_node(entry) == "other-node"


# ---------------------------------------------------------------------------
# remote_exec
# ---------------------------------------------------------------------------
class TestRemoteExec:
    def test_success(self):
        """Remote exec returns (cmd, exit_code, tail, duration) on success."""
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        cmd = "ribosome [t-abc123] --provider zhipu 'do stuff'"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "all good"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result_cmd, exit_code, _tail, duration = remote_exec(cmd, worker)

        assert result_cmd == cmd
        assert exit_code == 0
        assert duration >= 0
        # Verify SSH command structure
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        assert ssh_cmd[0] == "ssh"
        assert ssh_cmd[-2] == "ubuntu@ganglion"
        assert "docker run --rm gemmule:latest bash -c" in ssh_cmd[-1]

    def test_ssh_failure_returns_125(self):
        """SSH connection failure returns SSH_REMOTE_EXIT_CONNECT_FAIL."""
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        cmd = "ribosome [t-def456] --provider zhipu 'test'"

        mock_result = MagicMock()
        mock_result.returncode = 255  # SSH error exit code
        mock_result.stdout = ""
        mock_result.stderr = "Connection refused"

        with patch("subprocess.run", return_value=mock_result):
            result_cmd, exit_code, _tail, _duration = remote_exec(cmd, worker)

        assert exit_code == SSH_REMOTE_EXIT_CONNECT_FAIL
        assert result_cmd == cmd

    def test_task_failure_normal_exit_code(self):
        """Task failure (non-zero exit, not SSH) returns the real exit code."""
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        cmd = "ribosome [t-ghi789] --provider zhipu 'test'"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "some error output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            _, exit_code, tail, _ = remote_exec(cmd, worker)

        assert exit_code == 1
        assert "error" in tail.lower()

    def test_timeout(self):
        """Timeout returns exit code 124."""
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        cmd = "ribosome [t-timeout] --provider zhipu 'slow'"

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 1860)):
            _, exit_code, tail, _ = remote_exec(cmd, worker)

        assert exit_code == 124
        assert "timeout" in tail.lower()

    def test_exception_returns_125(self):
        """Unexpected exception returns SSH_REMOTE_EXIT_CONNECT_FAIL."""
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        cmd = "ribosome [t-exc] --provider zhipu 'test'"

        with patch("subprocess.run", side_effect=OSError("broken")):
            _, exit_code, _, _ = remote_exec(cmd, worker)

        assert exit_code == SSH_REMOTE_EXIT_CONNECT_FAIL


# ---------------------------------------------------------------------------
# _ssh_health_check
# ---------------------------------------------------------------------------
class TestSSHHealthCheck:
    def test_healthy(self):
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            assert _ssh_health_check(worker) is True

    def test_unreachable(self):
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}
        mock_result = MagicMock()
        mock_result.returncode = 255

        with patch("subprocess.run", return_value=mock_result):
            assert _ssh_health_check(worker) is False

    def test_timeout(self):
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 7)):
            assert _ssh_health_check(worker) is False

    def test_exception(self):
        worker = {"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}

        with patch("subprocess.run", side_effect=OSError("nope")):
            assert _ssh_health_check(worker) is False


# ---------------------------------------------------------------------------
# mark_done with node provenance
# ---------------------------------------------------------------------------
class TestMarkDoneNode:
    def test_soma_tag_appended(self, tmp_path):
        """mark_done with node='soma' appends [soma] to result line."""
        qf = tmp_path / "translation-queue.md"
        qf.write_text(
            textwrap.dedent("""\
            ## Queue
            - [ ] `ribosome [t-abc123] --provider zhipu 'test'`
            ## Done
        """)
        )
        _ns["QUEUE_FILE"] = qf

        mark_done(1, "exit=0", task_id="t-abc123", node="soma")

        content = qf.read_text()
        assert "[soma]" in content
        assert "[ganglion]" not in content

    def test_ganglion_tag_appended(self, tmp_path):
        """mark_done with node='ganglion' appends [ganglion] to result line."""
        qf = tmp_path / "translation-queue.md"
        qf.write_text(
            textwrap.dedent("""\
            ## Queue
            - [ ] `ribosome [t-def456] --provider zhipu 'test'`
            ## Done
        """)
        )
        _ns["QUEUE_FILE"] = qf

        mark_done(1, "exit=0", task_id="t-def456", node="ganglion")

        content = qf.read_text()
        assert "[ganglion]" in content
        assert "- [x]" in content

    def test_default_node_is_soma(self, tmp_path):
        """mark_done without node parameter defaults to 'soma'."""
        qf = tmp_path / "translation-queue.md"
        qf.write_text(
            textwrap.dedent("""\
            ## Queue
            - [ ] `ribosome [t-ghi789] --provider zhipu 'test'`
            ## Done
        """)
        )
        _ns["QUEUE_FILE"] = qf

        mark_done(1, "exit=0", task_id="t-ghi789")

        content = qf.read_text()
        assert "[soma]" in content


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    def test_remote_workers_structure(self):
        assert len(REMOTE_WORKERS) >= 1
        w = REMOTE_WORKERS[0]
        assert w["host"] == "ganglion"
        assert w["user"] == "ubuntu"
        assert w["max_concurrent"] == 2

    def test_max_local(self):
        assert MAX_LOCAL == 4

    def test_ssh_connect_timeout(self):
        assert SSH_CONNECT_TIMEOUT == 5

    def test_ssh_remote_exit_connect_fail(self):
        assert SSH_REMOTE_EXIT_CONNECT_FAIL == 125


# ---------------------------------------------------------------------------
# _update_running_file with node
# ---------------------------------------------------------------------------
class TestUpdateRunningFileWithNode:
    def test_includes_node_field(self, tmp_path):
        rf = tmp_path / "ribosome-running.json"
        _ns["RUNNING_FILE"] = rf

        running = {
            MagicMock(): (1, "cmd1", "zhipu", "t-aaa", "zhipu", 1.0, "soma"),
            MagicMock(): (2, "cmd2", "zhipu", "t-bbb", "zhipu", 1.0, "ganglion"),
        }

        _ns["_update_running_file"](running)

        tasks = json.loads(rf.read_text())
        assert len(tasks) == 2
        nodes = {t["node"] for t in tasks}
        assert "soma" in nodes
        assert "ganglion" in nodes

    def test_old_format_defaults_soma(self, tmp_path):
        rf = tmp_path / "ribosome-running.json"
        _ns["RUNNING_FILE"] = rf

        running = {
            MagicMock(): (1, "cmd1", "zhipu", "t-aaa", "zhipu"),
        }

        _ns["_update_running_file"](running)

        tasks = json.loads(rf.read_text())
        assert tasks[0]["node"] == "soma"


# Cleanup: restore QUEUE_FILE and RUNNING_FILE
@pytest.fixture(autouse=True)
def _restore_globals():
    original_qf = _ns["QUEUE_FILE"]
    original_rf = _ns["RUNNING_FILE"]
    yield
    _ns["QUEUE_FILE"] = original_qf
    _ns["RUNNING_FILE"] = original_rf
