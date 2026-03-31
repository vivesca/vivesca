#!/usr/bin/env python3
from __future__ import annotations
"""Tests for cg effector — GLM-5.1 Claude Code wrapper via ZhipuAI."""


import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

CG_PATH = Path.home() / "germline" / "effectors" / "cg"


@pytest.fixture
def fake_claude(tmp_path):
    """Create a fake claude binary that records invocation details."""
    fake = tmp_path / "claude"
    fake.write_text(
        '#!/bin/bash\n'
        'echo "ARGV: $@"\n'
        'echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}"\n'
        'echo "ANTHROPIC_BASE_URL: ${ANTHROPIC_BASE_URL}"\n'
        'echo "ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:-<unset>}"\n'
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake


def _run_cg(*args, env_extra=None, path_dirs=None):
    """Run the cg effector as a subprocess and return CompletedProcess."""
    env = os.environ.copy()
    # Strip any inherited keys that would interfere
    env.pop("ZHIPU_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_BASE_URL", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    if env_extra:
        env.update(env_extra)
    if path_dirs:
        env["PATH"] = str(path_dirs) + ":" + env.get("PATH", "/usr/bin:/bin")
    return subprocess.run(
        [str(CG_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ---------------------------------------------------------------------------
# --help / -h
# ---------------------------------------------------------------------------

class TestHelp:
    def test_help_flag_exits_zero(self):
        r = _run_cg("--help")
        assert r.returncode == 0

    def test_help_output_contains_usage(self):
        r = _run_cg("--help")
        assert "Usage:" in r.stdout

    def test_help_output_contains_description(self):
        r = _run_cg("--help")
        assert "GLM-5.1" in r.stdout
        assert "ZhipuAI" in r.stdout

    def test_help_shows_env_requirement(self):
        r = _run_cg("--help")
        assert "ZHIPU_API_KEY" in r.stdout

    def test_short_h_flag(self):
        r = _run_cg("-h")
        assert r.returncode == 0
        assert "Usage:" in r.stdout


# ---------------------------------------------------------------------------
# Missing ZHIPU_API_KEY
# ---------------------------------------------------------------------------

class TestMissingKey:
    def test_missing_key_exits_nonzero(self):
        r = _run_cg("-p", "test")
        assert r.returncode != 0

    def test_missing_key_error_message(self):
        r = _run_cg("-p", "test")
        combined = r.stderr + r.stdout
        assert "ZHIPU_API_KEY" in combined


# ---------------------------------------------------------------------------
# Correct invocation with fake claude
# ---------------------------------------------------------------------------

class TestInvocation:
    def test_sets_anthropic_api_key(self, fake_claude, tmp_path):
        r = _run_cg(
            "-p", "hello",
            env_extra={"ZHIPU_API_KEY": "test-key-123"},
            path_dirs=str(tmp_path),
        )
        # fake_claude should have been exec'd; original claude won't exist
        # but our fake is on PATH so the script should find it
        # Note: exec replaces the process, so returncode comes from fake_claude
        assert "ANTHROPIC_API_KEY: test-key-123" in r.stdout

    def test_sets_anthropic_base_url(self, fake_claude, tmp_path):
        r = _run_cg(
            "-p", "hello",
            env_extra={"ZHIPU_API_KEY": "k"},
            path_dirs=str(tmp_path),
        )
        assert "ANTHROPIC_BASE_URL: https://open.bigmodel.cn/api/anthropic" in r.stdout

    def test_unsets_anthropic_auth_token(self, fake_claude, tmp_path):
        r = _run_cg(
            "-p", "hello",
            env_extra={
                "ZHIPU_API_KEY": "k",
                "ANTHROPIC_AUTH_TOKEN": "should-be-gone",
            },
            path_dirs=str(tmp_path),
        )
        assert "ANTHROPIC_AUTH_TOKEN: <unset>" in r.stdout

    def test_passes_model_flag(self, fake_claude, tmp_path):
        r = _run_cg(
            "-p", "hello",
            env_extra={"ZHIPU_API_KEY": "k"},
            path_dirs=str(tmp_path),
        )
        assert "--model" in r.stdout
        assert "glm-5.1" in r.stdout

    def test_passes_dangerously_skip_permissions(self, fake_claude, tmp_path):
        r = _run_cg(
            "-p", "hello",
            env_extra={"ZHIPU_API_KEY": "k"},
            path_dirs=str(tmp_path),
        )
        assert "--dangerously-skip-permissions" in r.stdout

    def test_passes_extra_args(self, fake_claude, tmp_path):
        r = _run_cg(
            "-p", "hello world",
            env_extra={"ZHIPU_API_KEY": "k"},
            path_dirs=str(tmp_path),
        )
        assert "-p" in r.stdout
        assert "hello world" in r.stdout

    def test_passes_multiple_args(self, fake_claude, tmp_path):
        r = _run_cg(
            "--verbose", "-p", "test prompt",
            env_extra={"ZHIPU_API_KEY": "k"},
            path_dirs=str(tmp_path),
        )
        assert "--verbose" in r.stdout
        assert "test prompt" in r.stdout
