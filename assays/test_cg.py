"""Tests for effectors/cg — GLM-5.1 Claude Code wrapper via ZhipuAI."""

from __future__ import annotations

import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

cg_path = Path.home() / "germline" / "effectors" / "cg"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_cg(args: list[str], env: dict[str, str] | None = None, timeout: int = 10) -> subprocess.CompletedProcess:
    """Run the cg effector as a subprocess and return the result."""
    run_env = dict(os.environ)
    if env is not None:
        run_env.update(env)
    return subprocess.run(
        ["bash", str(cg_path), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=run_env,
    )


def _make_fake_claude(tmp_path: Path, record_file: Path | None = None) -> Path:
    """Create a fake ``claude`` script that records env + args, then return its directory."""
    fake_dir = tmp_path / "bin"
    fake_dir.mkdir()
    fake_bin = fake_dir / "claude"
    record = record_file or (tmp_path / "claude_invocation.txt")
    fake_bin.write_text(
        textwrap.dedent(f"""\
            #!/bin/bash
            echo "ARGV: $@" >> {record}
            echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> {record}
            echo "ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL" >> {record}
            echo "ANTHROPIC_AUTH_TOKEN=$ANTHROPIC_AUTH_TOKEN" >> {record}
        """),
        encoding="utf-8",
    )
    fake_bin.chmod(fake_bin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return fake_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHelp:
    """--help and -h should print usage and exit 0."""

    def test_help_long_flag(self):
        r = _run_cg(["--help"])
        assert r.returncode == 0
        assert "cg — Claude Code via GLM-5.1" in r.stdout
        assert "ZHIPU_API_KEY" in r.stdout

    def test_help_short_flag(self):
        r = _run_cg(["-h"])
        assert r.returncode == 0
        assert "cg — Claude Code via GLM-5.1" in r.stdout

    def test_help_mentions_glm_model(self):
        r = _run_cg(["--help"])
        assert "glm-5.1" in r.stdout


class TestMissingApiKey:
    """Without ZHIPU_API_KEY the script must fail."""

    def test_exits_nonzero_without_key(self):
        r = _run_cg(["-p", "hello"], env={"ZHIPU_API_KEY": ""})
        assert r.returncode != 0

    def test_error_message_mentions_key(self):
        r = _run_cg(["-p", "hello"], env={"ZHIPU_API_KEY": ""})
        combined = r.stderr + r.stdout
        assert "ZHIPU_API_KEY" in combined


class TestEnvSetup:
    """When ZHIPU_API_KEY is set, the wrapper should configure the environment correctly."""

    def test_anthropic_api_key_set(self, tmp_path):
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            ["-p", "hello"],
            env={
                "ZHIPU_API_KEY": "test-zhipu-key-123",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        assert "ANTHROPIC_API_KEY=test-zhipu-key-123" in content

    def test_anthropic_base_url_set(self, tmp_path):
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            ["-p", "hello"],
            env={
                "ZHIPU_API_KEY": "test-key",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        assert "ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic" in content

    def test_anthropic_auth_token_unset(self, tmp_path):
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            ["-p", "hello"],
            env={
                "ZHIPU_API_KEY": "test-key",
                "ANTHROPIC_AUTH_TOKEN": "should-be-gone",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        # After unset, the variable should be empty
        assert "ANTHROPIC_AUTH_TOKEN=" in content
        assert "should-be-gone" not in content


class TestClaudeInvocation:
    """Verify the exec claude line passes correct model and flags."""

    def test_model_flag_passed(self, tmp_path):
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            ["-p", "write a test"],
            env={
                "ZHIPU_API_KEY": "test-key",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        assert "--model" in content
        assert "glm-5.1" in content

    def test_dangerously_skip_permissions_passed(self, tmp_path):
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            ["-p", "hello"],
            env={
                "ZHIPU_API_KEY": "test-key",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        assert "--dangerously-skip-permissions" in content

    def test_extra_args_forwarded(self, tmp_path):
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            ["-p", "explain this code", "--verbose"],
            env={
                "ZHIPU_API_KEY": "test-key",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        assert "ARGV: --dangerously-skip-permissions --model glm-5.1 -p explain this code --verbose" in content

    def test_no_args_starts_interactive(self, tmp_path):
        """With no extra args, still passes model and skip-permissions."""
        record = tmp_path / "invocation.txt"
        fake_dir = _make_fake_claude(tmp_path, record)
        r = _run_cg(
            [],
            env={
                "ZHIPU_API_KEY": "test-key",
                "PATH": str(fake_dir) + ":" + os.environ.get("PATH", ""),
            },
        )
        assert r.returncode == 0
        content = record.read_text()
        assert "glm-5.1" in content
        assert "--dangerously-skip-permissions" in content
