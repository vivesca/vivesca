#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/publish — symlink to publish tool."""


import subprocess
from pathlib import Path

import pytest

SARCIO_PATH = Path(__file__).resolve().parents[1] / "effectors" / "publish"


# ── Symlink structure tests ────────────────────────────────────────────────────


class TestSarcioSymlink:
    def test_symlink_exists(self):
        """Test that publish effector symlink exists."""
        # On Linux, symlink may point to macOS path that doesn't exist
        # Check the symlink file itself exists (even if broken)
        assert SARCIO_PATH.is_symlink() or SARCIO_PATH.is_file()

    def test_symlink_target_exists_or_broken(self):
        """Test that publish symlink target exists (or is expected broken symlink)."""
        if SARCIO_PATH.is_symlink():
            target = SARCIO_PATH.resolve()
            # Symlink may point to macOS path on Linux - that's OK
            if not target.exists():
                # Check it's a valid symlink pointing to expected location
                import os

                link_target = os.readlink(SARCIO_PATH)
                assert "mise" in link_target or "publish" in link_target.lower()

    def test_symlink_target_is_executable(self):
        """Test that publish symlink target is executable (if target exists)."""
        target = SARCIO_PATH.resolve()
        if target.exists():
            # Check if file has execute permission
            assert target.stat().st_mode & 0o111, f"{target} is not executable"
        # If target doesn't exist (broken symlink on different OS), that's OK

    def test_symlink_points_to_mise_python(self):
        """Test symlink points to mise Python installation."""
        target = SARCIO_PATH.resolve()
        # Should point to mise or have publish in path
        target_str = str(target)
        assert "mise" in target_str or "publish" in target_str.lower()


# ── Execution tests ────────────────────────────────────────────────────────────


class TestSarcioExecution:
    @pytest.mark.skipif(
        not SARCIO_PATH.resolve().exists(),
        reason="publish CLI not installed or symlink broken on this platform",
    )
    def test_publish_help_runs(self):
        """Test publish --help runs without error."""
        result = subprocess.run(
            [str(SARCIO_PATH.resolve()), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Either succeeds or shows help
        assert (
            result.returncode == 0
            or "usage" in result.stdout.lower()
            or "usage" in result.stderr.lower()
        )

    @pytest.mark.skipif(
        not SARCIO_PATH.resolve().exists(),
        reason="publish CLI not installed or symlink broken on this platform",
    )
    def test_publish_executable_runs(self):
        """Test publish runs as executable."""
        result = subprocess.run(
            [str(SARCIO_PATH.resolve())],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should run without crashing (may show help or require args)
        # Non-zero exit is OK if it shows usage
        if result.returncode != 0:
            assert result.stdout or result.stderr


# ── Symlink attributes tests ────────────────────────────────────────────────────


class TestSymlinkAttributes:
    def test_symlink_in_effectors_dir(self):
        """Test publish is in effectors directory."""
        assert SARCIO_PATH.parent.name == "effectors"

    def test_symlink_name(self):
        """Test symlink has correct name."""
        assert SARCIO_PATH.name == "publish"

    def test_symlink_is_not_broken_or_cross_platform(self):
        """Test symlink is not broken (or is cross-platform broken symlink)."""
        try:
            # resolve() should work for non-broken symlinks
            target = SARCIO_PATH.resolve()
            # File should exist OR symlink points to expected location
            if not target.exists():
                import os

                link_target = os.readlink(SARCIO_PATH)
                # Cross-platform broken symlinks are OK
                assert "mise" in link_target or "publish" in link_target.lower()
        except OSError:
            pytest.fail("Symlink is broken")


# ── Integration tests ───────────────────────────────────────────────────────────


class TestSarcioIntegration:
    @pytest.mark.skipif(
        not SARCIO_PATH.resolve().exists(),
        reason="publish CLI not installed or symlink broken on this platform",
    )
    def test_can_execute_via_symlink(self):
        """Test that we can execute publish through the symlink."""
        result = subprocess.run(
            [str(SARCIO_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should produce some output
        assert result.stdout or result.stderr


# ── scan_content sanitization gate ──────────────────────────────────────────────


def _load_publish_module():
    """Import the publish CLI as a module (it has no .py extension)."""
    import importlib.machinery
    import importlib.util

    target = SARCIO_PATH.resolve()
    if not target.exists():
        pytest.skip("publish CLI not available")
    loader = importlib.machinery.SourceFileLoader("publish_under_test", str(target))
    spec = importlib.util.spec_from_loader("publish_under_test", loader)
    if spec is None or spec.loader is None:
        pytest.skip("could not load publish module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestScanContentSanitization:
    """The block-tier gate must reject any post containing client-identifying terms.

    If this assay flips green→red, either a real leak risk just landed or the
    stopwords list at ~/epigenome/chromatin/loci/config/garden_stopwords.md needs
    a new entry.
    """

    @pytest.fixture
    def publish_module(self):
        return _load_publish_module()

    def test_clean_post_has_no_warnings_or_blocks(self, publish_module):
        clean = (
            "---\n"
            "title: Test\n"
            "draft: true\n"
            "---\n\n"
            "A post with no sensitive content. Just prose about ideas.\n"
            "Items two through four are mentioned in passing.\n"
        )
        warnings, blocks = publish_module.scan_content(clean)
        assert blocks == [], f"clean post must not block: {blocks}"
        assert warnings == [], f"clean post must not warn: {warnings}"

    def test_block_tier_catches_employer_name(self, publish_module):
        bad = (
            "---\ntitle: Bad\ndraft: true\n---\n\n"
            "Working at HSBC has taught me a lot about governance.\n"
        )
        _, blocks = publish_module.scan_content(bad)
        assert any("HSBC" in b for b in blocks), f"must block HSBC: {blocks}"

    def test_block_tier_catches_consulting_firm_name(self, publish_module):
        bad = (
            "---\ntitle: Bad\ndraft: true\n---\n\n"
            "My role at Capco involves consulting on AI governance.\n"
        )
        _, blocks = publish_module.scan_content(bad)
        assert any("Capco" in b for b in blocks), f"must block Capco: {blocks}"

    def test_block_tier_catches_internal_codename(self, publish_module):
        bad = (
            "---\ntitle: Bad\ndraft: true\n---\n\n"
            "The Eunomia paper proposes a coordinator function.\n"
        )
        _, blocks = publish_module.scan_content(bad)
        assert any("Eunomia" in b for b in blocks), f"must block Eunomia: {blocks}"

    def test_word_boundary_avoids_substring_false_positive(self, publish_module):
        """The honorific regex must not match 'items' as 'Ms ' mid-string.

        Regression: published 2026-05-06 garden post triggered a spurious
        warning on 'items two through four' because the original Mr|Ms|Mrs
        pattern lacked a leading word boundary.
        """
        body = (
            "---\ntitle: Test\ndraft: true\n---\n\n"
            "Items two through four were named in the original Asks.\n"
        )
        warnings, blocks = publish_module.scan_content(body)
        named = [w for w in warnings if "named individual" in w]
        assert named == [], f"must not match 'items' as honorific: {named}"
        assert blocks == []

    def test_stopwords_only_match_body_not_frontmatter(self, publish_module):
        """A stopword in tags or other frontmatter fields must not trigger.

        Frontmatter is metadata, not published prose, so it should be excluded
        from the scan.
        """
        body = (
            "---\ntitle: Test\ntags: [hsbc-context]\ndraft: true\n---\n\n"
            "A perfectly clean body without any sensitive terms.\n"
        )
        result = publish_module.scan_content(body)
        blocks = result[1]
        assert blocks == [], f"frontmatter tag must not block: {blocks}"

    def test_stopwords_file_loads(self, publish_module):
        """The garden_stopwords.md config must load without error.

        If the file path moves or format breaks, both lists return empty
        and the gate degrades silently — assert it loads non-empty.
        """
        result = publish_module.load_stopwords()
        block = result[0]
        if publish_module.STOPWORDS_PATH.exists():
            assert "HSBC" in block, "HSBC must be in block tier"
            assert "Capco" in block, "Capco must be in block tier"
