from __future__ import annotations

"""Tests for effectors/soma-pull — repo pull scheduler with log rotation."""

import subprocess
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "soma-pull"


def _load_module():
    """Load soma-pull by exec-ing its source into a ModuleType."""
    source = EFFECTOR_PATH.read_text()
    mod = types.ModuleType("soma_pull")
    mod.__file__ = str(EFFECTOR_PATH)
    exec(source, mod.__dict__)
    return mod


_mod = _load_module()
pull = _mod.pull
REPOS = _mod.REPOS
LOG = _mod.LOG


# ── pull() tests ──────────────────────────────────────────────────────


def test_pull_not_a_git_repo(tmp_path):
    """pull reports failure when .git directory is missing."""
    repo = tmp_path / "notarepo"
    repo.mkdir()
    msg, ok = pull(repo)
    assert not ok
    assert "not a git repo" in msg


def test_pull_already_up_to_date(tmp_path):
    """pull reports success with 'ok' when repo is already current."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / ".git").mkdir()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        msg, ok = pull(repo)
    mock_run.assert_called_once_with(
        ["git", "pull", "--ff-only", "--quiet"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert ok
    assert "ok" in msg


def test_pull_updates_detected(tmp_path):
    """pull reports 'updated' when changes are pulled."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / ".git").mkdir()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Fast-forward\n abc1234..def5678  main -> main\n"
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result):
        msg, ok = pull(repo)
    assert ok
    assert "updated" in msg


def test_pull_git_failure(tmp_path):
    """pull reports failure when git returns non-zero exit code."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / ".git").mkdir()
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "fatal: not possible to fast-forward"
    with patch("subprocess.run", return_value=mock_result):
        msg, ok = pull(repo)
    assert not ok
    assert "FAIL" in msg


def test_pull_timeout(tmp_path):
    """pull reports TIMEOUT when git exceeds the time limit."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / ".git").mkdir()
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
        msg, ok = pull(repo)
    assert not ok
    assert "TIMEOUT" in msg


def test_pull_unexpected_exception(tmp_path):
    """pull reports ERROR on unexpected exceptions."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / ".git").mkdir()
    with patch("subprocess.run", side_effect=OSError("permission denied")):
        msg, ok = pull(repo)
    assert not ok
    assert "ERROR" in msg


def test_pull_stderr_truncated(tmp_path):
    """pull truncates stderr to 100 chars in failure message."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / ".git").mkdir()
    long_err = "x" * 200
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = long_err
    with patch("subprocess.run", return_value=mock_result):
        msg, ok = pull(repo)
    assert not ok
    # The message should contain the repo name and trimmed stderr
    assert len(msg) < len(long_err)


# ── main() tests ──────────────────────────────────────────────────────


def test_main_success_writes_log(tmp_path):
    """main writes a timestamped log line when all repos succeed."""
    log_path = tmp_path / "soma-pull.log"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""
    with (
        patch.object(_mod, "REPOS", [tmp_path / "r1"]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        # Create the fake repo
        (tmp_path / "r1").mkdir()
        (tmp_path / "r1" / ".git").mkdir()
        _mod.main()

    assert log_path.exists()
    content = log_path.read_text()
    assert "r1" in content
    assert "ok" in content


def test_main_failure_exits_nonzero(tmp_path):
    """main exits with code 1 when any repo fails."""
    log_path = tmp_path / "soma-pull.log"
    repo = tmp_path / "badrepo"
    repo.mkdir()
    # No .git => failure
    with (
        patch.object(_mod, "REPOS", [repo]),
        patch.object(_mod, "LOG", log_path),
    ):
        with pytest.raises(SystemExit) as exc_info:
            _mod.main()
    assert exc_info.value.code == 1


def test_main_log_rotation(tmp_path):
    """main trims the log to 250 lines when it exceeds 500 lines."""
    log_path = tmp_path / "soma-pull.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Pre-fill 510 lines
    initial_lines = [f"2025-01-01 00:{i:02d}:00 line {i}" for i in range(510)]
    log_path.write_text("\n".join(initial_lines) + "\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""

    repo = tmp_path / "r1"
    repo.mkdir()
    (repo / ".git").mkdir()

    with (
        patch.object(_mod, "REPOS", [repo]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        _mod.main()

    final_lines = log_path.read_text().splitlines()
    # Should be 250 old kept + 1 new = 251
    assert len(final_lines) == 251


def test_main_no_rotation_when_under_limit(tmp_path):
    """main does not trim the log when line count is under 500."""
    log_path = tmp_path / "soma-pull.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    initial_lines = [f"2025-01-01 00:{i:02d}:00 line {i}" for i in range(10)]
    log_path.write_text("\n".join(initial_lines) + "\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""

    repo = tmp_path / "r1"
    repo.mkdir()
    (repo / ".git").mkdir()

    with (
        patch.object(_mod, "REPOS", [repo]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        _mod.main()

    final_lines = log_path.read_text().splitlines()
    # 10 original + 1 new = 11
    assert len(final_lines) == 11


def test_main_creates_log_directory(tmp_path):
    """main creates the log parent directory if it does not exist."""
    log_path = tmp_path / "deep" / "nested" / "soma-pull.log"
    repo = tmp_path / "r1"
    repo.mkdir()
    (repo / ".git").mkdir()

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""

    with (
        patch.object(_mod, "REPOS", [repo]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        _mod.main()

    assert log_path.exists()
    assert log_path.parent.is_dir()


def test_main_log_line_format(tmp_path):
    """main log lines start with a [timestamp] bracket."""
    log_path = tmp_path / "soma-pull.log"
    repo = tmp_path / "r1"
    repo.mkdir()
    (repo / ".git").mkdir()

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""

    with (
        patch.object(_mod, "REPOS", [repo]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        _mod.main()

    line = log_path.read_text().strip()
    assert line.startswith("[")
    assert "] " in line


def test_main_multiple_repos_in_log_line(tmp_path):
    """main joins multiple repo statuses with | in a single log line."""
    log_path = tmp_path / "soma-pull.log"
    r1 = tmp_path / "alpha"
    r2 = tmp_path / "beta"
    r1.mkdir()
    r2.mkdir()
    (r1 / ".git").mkdir()
    (r2 / ".git").mkdir()

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""

    with (
        patch.object(_mod, "REPOS", [r1, r2]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        _mod.main()

    line = log_path.read_text().strip()
    assert "alpha" in line
    assert "beta" in line
    assert " | " in line


def test_main_mixed_success_failure(tmp_path):
    """main exits 1 when at least one repo fails, but logs all results."""
    log_path = tmp_path / "soma-pull.log"
    good = tmp_path / "good"
    bad = tmp_path / "bad"
    good.mkdir()
    bad.mkdir()
    (good / ".git").mkdir()
    # bad has no .git

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Already up to date."
    mock_result.stderr = ""

    with (
        patch.object(_mod, "REPOS", [good, bad]),
        patch.object(_mod, "LOG", log_path),
        patch("subprocess.run", return_value=mock_result),
    ):
        with pytest.raises(SystemExit) as exc_info:
            _mod.main()

    assert exc_info.value.code == 1
    line = log_path.read_text().strip()
    assert "good" in line
    assert "bad" in line


# ── REPOS / LOG constants ─────────────────────────────────────────────


def test_repos_are_paths():
    """REPOS entries are Path objects pointing under home."""
    for r in REPOS:
        assert isinstance(r, Path)
        assert str(r).startswith(str(Path.home()))


def test_log_is_under_home():
    """LOG path is under the user's home directory."""
    assert isinstance(LOG, Path)
    assert str(LOG).startswith(str(Path.home()))


def test_repos_list_nonempty():
    """REPOS contains at least one entry."""
    assert len(REPOS) > 0
