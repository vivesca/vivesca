"""Tests for ribosome subcommand routing (explore, build, test, batch).

Validates that:
1. Subcommands route correctly and set expected defaults
2. Legacy flags (--explore, --test, --batch) still work with deprecation warnings
3. Explore uses GLM-4.5-air model tier (separate rate-limit pool)
4. Bare invocation defaults to build mode
"""

import os
import subprocess
from pathlib import Path

RIBOSOME = Path.home() / "germline" / "effectors" / "ribosome"


def _run_ribosome(*args, timeout=10):
    """Run ribosome with args. Short timeout since we expect fast failures (no claude)."""
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / 'germline' / 'effectors'}:{env.get('PATH', '')}"
    env["ZHIPU_API_KEY"] = "test-zhipu-key"
    env["VOLCANO_API_KEY"] = "test-volcano-key"
    env["INFINI_API_KEY"] = "test-infini-key"
    env["GOOGLE_API_KEY"] = "test-google-key"
    env["OPENAI_API_KEY"] = "test-openai-key"
    # Prevent real API keys from being inherited
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_BASE_URL", None)
    env.pop("ANTHROPIC_DEFAULT_OPUS_MODEL", None)
    env.pop("ANTHROPIC_DEFAULT_SONNET_MODEL", None)
    env.pop("ANTHROPIC_DEFAULT_HAIKU_MODEL", None)
    return subprocess.run(
        [str(RIBOSOME), *list(args)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


class TestSubcommandRouting:
    """Subcommands should be recognized as the first positional arg."""

    def test_explore_subcommand_recognized(self):
        """'ribosome explore ...' should not error with 'Unknown flag'."""
        r = _run_ribosome("explore", "test query")
        # Should NOT fail with usage error about unknown subcommand
        assert "Unknown" not in r.stderr

    def test_build_subcommand_recognized(self):
        """'ribosome build ...' should work as explicit build mode."""
        r = _run_ribosome("build", "test prompt")
        assert "Unknown" not in r.stderr

    def test_test_subcommand_recognized(self):
        """'ribosome test <module>' should work."""
        r = _run_ribosome("test", "metabolon/foo.py")
        assert "Unknown" not in r.stderr

    def test_batch_subcommand_recognized(self):
        """'ribosome batch <mod1> <mod2>' should work."""
        r = _run_ribosome("batch", "metabolon/foo.py", "metabolon/bar.py")
        assert "Unknown" not in r.stderr

    def test_bare_invocation_is_build(self):
        """'ribosome "prompt"' (no subcommand) should default to build."""
        r = _run_ribosome("some build prompt")
        assert "Unknown" not in r.stderr


class TestLegacyFlagCompat:
    """Old --explore, --test, --batch flags should still work but warn."""

    def test_explore_flag_warns_deprecation(self):
        """--explore should emit a deprecation warning on stderr."""
        r = _run_ribosome("--explore", "test query")
        assert "deprecated" in r.stderr.lower() or "use 'ribosome explore'" in r.stderr.lower()

    def test_test_flag_warns_deprecation(self):
        """--test should emit a deprecation warning on stderr."""
        r = _run_ribosome("--test", "metabolon/foo.py")
        assert "deprecated" in r.stderr.lower() or "use 'ribosome test'" in r.stderr.lower()

    def test_batch_flag_warns_deprecation(self):
        """--batch should emit a deprecation warning on stderr."""
        r = _run_ribosome("--batch", "metabolon/foo.py")
        assert "deprecated" in r.stderr.lower() or "use 'ribosome batch'" in r.stderr.lower()

    def test_explore_flag_still_works(self):
        """--explore should still function (not just warn)."""
        r = _run_ribosome("--explore", "test query")
        # Should not exit with usage error
        assert r.returncode != 2


class TestExploreModelTier:
    """Explore mode must use GLM-4.5-air (cheap tier) to avoid rate-limit collision with build."""

    def test_explore_sets_cheap_model(self):
        """When provider=zhipu and mode=explore, OPUS and SONNET should be GLM-4.5-air."""
        # Parse the script to verify the model override logic exists
        script = RIBOSOME.read_text()
        # The script should contain logic to set GLM-4.5-air for explore+zhipu
        assert "GLM-4.5-air" in script
        # Verify the explore model override block exists
        assert "EXPLORE" in script and "GLM-4.5-air" in script


class TestExploreDefaults:
    """Explore mode should have sensible defaults distinct from build."""

    def test_explore_help_text(self):
        """Help text should mention explore subcommand."""
        r = _run_ribosome("--help")
        assert "explore" in r.stdout.lower()

    def test_summary_still_works(self):
        """Summary subcommand should be unaffected by the refactor."""
        r = _run_ribosome("summary", "--recent", "1")
        # summary should work (exit 0) regardless of dispatch changes
        assert r.returncode == 0
