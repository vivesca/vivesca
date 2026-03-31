"""Tests for effectors/cg — GLM-5.1 Claude Code wrapper."""
from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

CG_PATH = Path.home() / "germline" / "effectors" / "cg"


def _mock_claude_script(tmpdir: Path) -> Path:
    """Create a fake claude that records invocation details to a file."""
    fake = tmpdir / "claude"
    record = tmpdir / "invocation.txt"
    fake.write_text(
        "#!/bin/bash\n"
        f"echo \"$@\" > {record}\n"
        "env > " + str(tmpdir / "envdump.txt") + "\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake


# ── Help flag tests ──────────────────────────────────────────────────


def test_help_flag_prints_usage_and_exits_zero():
    result = subprocess.run(
        ["bash", str(CG_PATH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "cg — Claude Code via GLM-5.1" in result.stdout
    assert "Usage" in result.stdout


def test_help_short_flag():
    result = subprocess.run(
        ["bash", str(CG_PATH), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "cg — Claude Code via GLM-5.1" in result.stdout


# ── Missing API key ──────────────────────────────────────────────────


def test_missing_zhipu_key_exits_nonzero():
    env = os.environ.copy()
    env.pop("ZHIPU_API_KEY", None)
    result = subprocess.run(
        ["bash", str(CG_PATH), "-p", "hello"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0
    assert "ZHIPU_API_KEY not set" in result.stderr


# ── Environment propagation via mock claude ──────────────────────────


def test_sets_anthropic_api_key_from_zhipu_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        fake_claude = _mock_claude_script(tmp)

        env = os.environ.copy()
        env["ZHIPU_API_KEY"] = "test-key-12345"
        env["PATH"] = str(tmp) + ":" + env.get("PATH", "")
        # Ensure no leftover key
        env.pop("ANTHROPIC_AUTH_TOKEN", None)

        result = subprocess.run(
            ["bash", str(CG_PATH), "-p", "test"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0

        envdump = (tmp / "envdump.txt").read_text()
        assert "ANTHROPIC_API_KEY=test-key-12345" in envdump


def test_sets_anthropic_base_url():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        _mock_claude_script(tmp)

        env = os.environ.copy()
        env["ZHIPU_API_KEY"] = "test-key-12345"
        env["PATH"] = str(tmp) + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(CG_PATH), "-p", "test"],
            capture_output=True,
            text=True,
            env=env,
        )

        envdump = (tmp / "envdump.txt").read_text()
        assert "ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic" in envdump


def test_unsets_anthropic_auth_token():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        _mock_claude_script(tmp)

        env = os.environ.copy()
        env["ZHIPU_API_KEY"] = "test-key-12345"
        env["ANTHROPIC_AUTH_TOKEN"] = "should-be-removed"
        env["PATH"] = str(tmp) + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(CG_PATH), "-p", "test"],
            capture_output=True,
            text=True,
            env=env,
        )

        envdump = (tmp / "envdump.txt").read_text()
        # The token must NOT appear in the env passed to claude
        assert "ANTHROPIC_AUTH_TOKEN" not in envdump


# ── Argument passthrough ─────────────────────────────────────────────


def test_passes_model_and_flags_to_claude():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        _mock_claude_script(tmp)

        env = os.environ.copy()
        env["ZHIPU_API_KEY"] = "test-key-12345"
        env["PATH"] = str(tmp) + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(CG_PATH), "-p", "do the thing"],
            capture_output=True,
            text=True,
            env=env,
        )

        invocation = (tmp / "invocation.txt").read_text().strip()
        assert "--dangerously-skip-permissions" in invocation
        assert "--model" in invocation
        assert "glm-5.1" in invocation
        assert "-p" in invocation
        assert "do the thing" in invocation


def test_passes_additional_args():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        _mock_claude_script(tmp)

        env = os.environ.copy()
        env["ZHIPU_API_KEY"] = "test-key-12345"
        env["PATH"] = str(tmp) + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(CG_PATH), "--max-turns", "10", "-p", "hello"],
            capture_output=True,
            text=True,
            env=env,
        )

        invocation = (tmp / "invocation.txt").read_text().strip()
        assert "--max-turns" in invocation
        assert "10" in invocation
