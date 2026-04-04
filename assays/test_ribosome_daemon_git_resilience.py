"""Tests for ribosome-daemon git failure resilience."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch


def _load_ribosome_daemon():
    """Load the ribosome-daemon module by exec-ing its Python body."""
    source = (Path.home() / "germline/effectors/ribosome-daemon").read_text()
    namespace: dict = {"__name__": "ribosome_daemon_git_resilience"}
    exec(source, namespace)
    return namespace


def test_startup_pull_logs_and_continues_on_git_failure():
    """startup_pull returns a failure string instead of raising on git pull error."""
    module = _load_ribosome_daemon()
    startup_pull = module["startup_pull"]
    logged: list[str] = []

    pull_result = MagicMock()
    pull_result.returncode = 1
    pull_result.stderr = "fatal: unable to access remote"

    with patch.dict(module, {"log": logged.append}):
        with patch("subprocess.run", return_value=pull_result) as mocked_run:
            result = startup_pull()

    assert result == "pull failed: fatal: unable to access remote"
    assert logged == [
        "startup pull failed (continuing with local state): fatal: unable to access remote"
    ]
    mocked_run.assert_called_once()


def test_startup_pull_logs_and_continues_on_timeout():
    """startup_pull handles git pull timeouts without crashing daemon startup."""
    module = _load_ribosome_daemon()
    startup_pull = module["startup_pull"]
    logged: list[str] = []

    with patch.dict(module, {"log": logged.append}):
        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git pull", timeout=120)
        ):
            result = startup_pull()

    assert result == "pull timed out"
    assert logged == ["startup pull timed out (continuing with local state)"]


def test_auto_commit_retries_push_with_backoff_until_success():
    """auto_commit sleeps 30s between failed pushes and returns commit hash on success."""
    module = _load_ribosome_daemon()
    auto_commit = module["auto_commit"]
    logged: list[str] = []

    add_result = MagicMock(returncode=0)
    diff_result = MagicMock(returncode=1)
    commit_result = MagicMock(returncode=0, stdout="[main abc1234] ribosome: daemon auto-commit\n")
    push_fail = MagicMock(returncode=1, stderr="network timeout")
    push_success = MagicMock(returncode=0, stderr="")

    with patch.dict(module, {"log": logged.append}):
        with patch(
            "subprocess.run",
            side_effect=[
                add_result,
                diff_result,
                commit_result,
                push_fail,
                push_fail,
                push_success,
            ],
        ) as mocked_run:
            with patch("time.sleep") as mocked_sleep:
                result = auto_commit()

    assert result == "abc1234"
    assert logged == [
        "git push failed (attempt 1/3): network timeout",
        "git push failed (attempt 2/3): network timeout",
    ]
    assert mocked_run.call_count == 6
    assert mocked_sleep.call_args_list == [call(30), call(30)]


def test_auto_commit_logs_after_exhausting_push_retries():
    """auto_commit keeps the local commit and does not raise after three failed pushes."""
    module = _load_ribosome_daemon()
    auto_commit = module["auto_commit"]
    logged: list[str] = []

    add_result = MagicMock(returncode=0)
    diff_result = MagicMock(returncode=1)
    commit_result = MagicMock(returncode=0, stdout="[main def5678] ribosome: daemon auto-commit\n")
    push_fail = MagicMock(returncode=1, stderr="network unreachable")

    with patch.dict(module, {"log": logged.append}):
        with patch(
            "subprocess.run",
            side_effect=[
                add_result,
                diff_result,
                commit_result,
                push_fail,
                push_fail,
                push_fail,
            ],
        ):
            with patch("time.sleep") as mocked_sleep:
                result = auto_commit()

    assert result == "def5678"
    assert logged == [
        "git push failed (attempt 1/3): network unreachable",
        "git push failed (attempt 2/3): network unreachable",
        "git push failed (attempt 3/3): network unreachable",
        "git push failed after 3 attempts for def5678, continuing with local state",
    ]
    assert mocked_sleep.call_args_list == [call(30), call(30)]
