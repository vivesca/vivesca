"""Tests for effectors/ck — bash script tested via subprocess."""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "ck"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with optional custom environment and PATH."""
    env = os.environ.copy()
    # Remove any existing MOONSHOT_API_KEY to avoid picking up system value
    env.pop("MOONSHOT_API_KEY", None)
    # Remove existing ANTHROPIC vars
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_BASE_URL", None)
    env.pop("ANTHROPIC_MODEL", None)
    if path_dirs is not None:
        # Prepend custom path dirs, keep system PATH after
        env["PATH"] = os.pathsep.join(str(p) for p in path_dirs) + os.pathsep + env.get("PATH", "")
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10,
    )


def _make_mock_bin(tmp_path: Path, name: str, stdout: str = "", exit_code: int = 0) -> Path:
    """Create a mock executable script in tmp_path/bin/<name>."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\necho {stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(tmp_path: Path, name: str, record_file: Path, exit_code: int = 0) -> Path:
    """Create a mock bin that records all args to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


# ── error case tests ─────────────────────────────────────────────────────


class TestNoApiKey:
    def test_exits_with_error_when_no_key_found(self, tmp_path):
        """Script exits 1 with error when no API key found."""
        # Create mock claude so we don't fail on that check first
        _make_mock_bin(tmp_path, "claude")
        r = _run_script(path_dirs=[tmp_path / "bin"])
        assert r.returncode == 1
        assert "error: no Moonshot API key found" in r.stderr

    def test_uses_env_var_when_provided(self, tmp_path):
        """Script picks up MOONSHOT_API_KEY from environment."""
        record = tmp_path / "calls.log"
        _make_recording_bin(tmp_path, "claude", record)
        r = _run_script(
            path_dirs=[tmp_path / "bin"],
            env_extra={"MOONSHOT_API_KEY": "test_key_123"},
        )
        # It should find the key and execute claude
        assert (tmp_path / "bin" / "claude").exists()
        assert record.exists()
        # Exit code 0 because mock claude exits 0
        assert r.returncode == 0
        # Should have added --dangerously-skip-permissions
        assert "--dangerously-skip-permissions" in record.read_text()


class TestClaudeNotFound:
    def test_exits_with_error_when_claude_not_found(self, tmp_path):
        """Script exits 1 when claude binary not found."""
        # We have an API key but no claude - filter PATH to remove claude
        filtered_path_dirs = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            # Skip any directory that contains claude
            if not (Path(dir_path) / "claude").exists():
                filtered_path_dirs.append(Path(dir_path))
        # Add empty bin dir at the beginning
        bindir = tmp_path / "bin"
        bindir.mkdir()
        filtered_path_dirs.insert(0, bindir)
        r = _run_script(
            path_dirs=filtered_path_dirs,
            env_extra={"MOONSHOT_API_KEY": "test_key"},
        )
        assert r.returncode == 1
        assert "error: claude binary not found" in r.stderr


# ── environment variable tests ───────────────────────────────────────────


class TestEnvironmentVariables:
    def test_sets_correct_anthropic_env_vars(self, tmp_path):
        """Script exports correct ANTHROPIC_* environment variables to Claude."""
        # Create a mock claude that prints environment variables
        bindir = tmp_path / "bin"
        bindir.mkdir()
        mock_claude = bindir / "claude"
        mock_claude.write_text("""#!/bin/bash
echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
echo "ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
echo "ANTHROPIC_MODEL=$ANTHROPIC_MODEL"
echo "ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN:-UNSET}"
exit 0
""")
        mock_claude.chmod(mock_claude.stat().st_mode | stat.S_IEXEC)
        r = _run_script(
            path_dirs=[bindir],
            env_extra={"MOONSHOT_API_KEY": "test_key_456", "ANTHROPIC_AUTH_TOKEN": "original_token"},
        )
        assert r.returncode == 0
        output = r.stdout
        assert "ANTHROPIC_API_KEY=test_key_456" in output
        assert "ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic/" in output
        assert "ANTHROPIC_MODEL=kimi-k2.5" in output
        assert "ANTHROPIC_AUTH_TOKEN=UNSET" in output

    def test_creates_kimi_home_dir(self, tmp_path):
        """Script creates $HOME/kimi-home directory."""
        # Create mock claude that just exits
        _make_mock_bin(tmp_path, "claude")
        # Check directory creation
        kimi_home = tmp_path / "kimi-home"
        r = _run_script(
            path_dirs=[tmp_path / "bin"],
            env_extra={"MOONSHOT_API_KEY": "test_key", "HOME": str(tmp_path)},
        )
        assert kimi_home.exists()
        assert kimi_home.is_dir()


# ── claude resolution tests ─────────────────────────────────────────────


class TestClaudeResolution:
    def test_uses_claude_from_path(self, tmp_path):
        """Script uses claude found on PATH first."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "claude", record)
        r = _run_script(
            path_dirs=[bindir],
            env_extra={"MOONSHOT_API_KEY": "test_key"},
        )
        assert r.returncode == 0
        assert record.exists()

    def test_passes_additional_args_to_claude(self, tmp_path):
        """Script passes through any additional arguments to Claude."""
        record = tmp_path / "calls.log"
        _make_recording_bin(tmp_path, "claude", record)
        r = _run_script(
            args=["--model", "kimi-k3", "--help"],
            path_dirs=[tmp_path / "bin"],
            env_extra={"MOONSHOT_API_KEY": "test_key"},
        )
        assert r.returncode == 0
        calls = record.read_text()
        assert "--dangerously-skip-permissions" in calls
        assert "--model" in calls
        assert "kimi-k3" in calls
        assert "--help" in calls


# ── credential file tests (Linux only) ───────────────────────────────────


class TestCredentialFile:
    def test_reads_from_config_file_if_exists(self, tmp_path):
        """Reads API key from ~/.config/moonshot-api-key."""
        record = tmp_path / "calls.log"
        _make_recording_bin(tmp_path, "claude", record)
        # Create the credential file in our tmp home
        config_dir = tmp_path / ".config"
        config_dir.mkdir()
        (config_dir / "moonshot-api-key").write_text("file_based_key\n")
        r = _run_script(
            path_dirs=[tmp_path / "bin"],
            env_extra={"HOME": str(tmp_path)},
        )
        assert r.returncode == 0
        assert record.exists()
