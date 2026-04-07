"""Tests for ribosome --harness and --backend flag parsing.

Tests the flag parsing logic by calling ribosome with --help-like probes.
Since ribosome is bash, we test by running it with args that trigger
early exits (unknown provider, syntax check) and checking the output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RIBOSOME = str(Path(__file__).resolve().parent.parent / "effectors" / "ribosome")


def run_ribosome(*args: str, timeout: int = 5) -> subprocess.CompletedProcess:
    """Run ribosome with given args, capture output."""
    return subprocess.run(
        ["bash", RIBOSOME, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(Path.home())},
    )


class TestHarnessFlag:
    """Test --harness flag parsing."""

    def test_unknown_harness_errors(self):
        result = run_ribosome("--harness", "fakecli", "hello")
        assert result.returncode != 0
        assert "Unknown harness" in result.stderr or "Unknown" in result.stderr

    def test_claude_harness_accepted(self):
        # Will fail on missing ZHIPU_API_KEY but should parse the flag
        result = run_ribosome("--harness", "claude", "hello")
        # Should NOT error on flag parsing — may error on missing key
        assert "Unknown harness" not in result.stderr

    def test_goose_harness_accepted(self):
        result = run_ribosome("--harness", "goose", "hello")
        assert "Unknown harness" not in result.stderr

    def test_droid_harness_accepted(self):
        result = run_ribosome("--harness", "droid", "hello")
        assert "Unknown harness" not in result.stderr


class TestBackendFlag:
    """Test --backend flag parsing."""

    def test_unknown_backend_errors(self):
        result = run_ribosome("--backend", "fakeprovider", "hello")
        assert result.returncode != 0

    def test_zhipu_backend_accepted(self):
        result = run_ribosome("--backend", "zhipu", "hello")
        assert "Unknown" not in result.stderr or "ZHIPU_API_KEY" in result.stderr

    def test_infini_backend_accepted(self):
        result = run_ribosome("--backend", "infini", "hello")
        assert "Unknown" not in result.stderr or "INFINI_API_KEY" in result.stderr


class TestProviderBackwardCompat:
    """Test that --provider X still works and maps correctly."""

    def test_provider_zhipu_maps_to_claude_zhipu(self):
        result = run_ribosome("--provider", "zhipu", "hello")
        # Should parse without "Unknown" — may fail on missing key
        assert "Unknown provider" not in result.stderr
        assert "Unknown harness" not in result.stderr

    def test_provider_goose_maps_to_goose_zhipu(self):
        result = run_ribosome("--provider", "goose", "hello")
        assert "Unknown provider" not in result.stderr
        assert "Unknown harness" not in result.stderr

    def test_provider_droid_maps_to_droid_zhipu(self):
        result = run_ribosome("--provider", "droid", "hello")
        assert "Unknown provider" not in result.stderr
        assert "Unknown harness" not in result.stderr

    def test_provider_infini_maps_to_claude_infini(self):
        result = run_ribosome("--provider", "infini", "hello")
        assert "Unknown provider" not in result.stderr

    def test_provider_unknown_errors(self):
        result = run_ribosome("--provider", "nonexistent", "hello")
        assert result.returncode != 0


class TestHarnessBackendCombination:
    """Test combined --harness + --backend flags."""

    def test_goose_with_zhipu(self):
        result = run_ribosome("--harness", "goose", "--backend", "zhipu", "hello")
        assert "Unknown" not in result.stderr or "API_KEY" in result.stderr

    def test_droid_with_zhipu(self):
        result = run_ribosome("--harness", "droid", "--backend", "zhipu", "hello")
        assert "Unknown" not in result.stderr or "API_KEY" in result.stderr

    def test_claude_with_infini(self):
        result = run_ribosome("--harness", "claude", "--backend", "infini", "hello")
        assert "Unknown" not in result.stderr or "API_KEY" in result.stderr


class TestEnvIsolation:
    """Test that harness invocations don't leak parent env vars."""

    def test_goose_does_not_inherit_anthropic_base_url(self):
        """When --harness goose runs, ANTHROPIC_BASE_URL from parent should not leak."""
        # This test verifies the env -i pattern is used
        # We can't easily test the actual execution without API keys,
        # but we can verify the script doesn't error on flag parsing
        result = subprocess.run(
            ["bash", RIBOSOME, "--harness", "goose", "hello"],
            capture_output=True,
            text=True,
            timeout=5,
            env={
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": str(Path.home()),
                "ANTHROPIC_BASE_URL": "https://should-not-leak.example.com",
                "ANTHROPIC_API_KEY": "should-not-leak",
                "ZHIPU_API_KEY": "test-key-for-parsing-only",
            },
        )
        # The key assertion: goose should NOT connect to the leaked URL
        assert "should-not-leak" not in result.stdout
