from __future__ import annotations

"""Tests for exocytosis.conf — signal transduction parameters for garden post pipeline."""

import configparser
from pathlib import Path

import pytest


CONF_PATH = Path.home() / "germline" / "effectors" / "exocytosis.conf"


@pytest.fixture
def conf():
    """Parse exocytosis.conf and return the ConfigParser object."""
    cp = configparser.ConfigParser()
    cp.read(str(CONF_PATH))
    return cp


# ── File-level tests ────────────────────────────────────────────────────


class TestFileExists:
    """Verify the config file is present and non-empty."""

    def test_file_exists(self):
        assert CONF_PATH.exists(), f"{CONF_PATH} not found"

    def test_file_non_empty(self):
        assert CONF_PATH.stat().st_size > 0, "exocytosis.conf is empty"

    def test_file_valid_ini(self, conf):
        """File parses without error (checked implicitly by fixture) and has sections."""
        assert len(conf.sections()) > 0


# ── Section existence tests ─────────────────────────────────────────────


class TestSections:
    """Verify all expected sections are present."""

    EXPECTED = {"generate", "judge", "judge_criteria"}

    def test_all_sections_present(self, conf):
        missing = self.EXPECTED - set(conf.sections())
        assert not missing, f"Missing sections: {missing}"

    def test_no_extra_sections(self, conf):
        extra = set(conf.sections()) - self.EXPECTED
        assert not extra, f"Unexpected sections: {extra}"


# ── [generate] section tests ────────────────────────────────────────────


class TestGenerateSection:
    """Validate [generate] section keys and value bounds."""

    def test_max_tokens_generate_exists(self, conf):
        assert conf.has_option("generate", "max_tokens_generate")

    def test_max_tokens_generate_is_int(self, conf):
        val = conf.getint("generate", "max_tokens_generate")
        assert isinstance(val, int)

    @pytest.mark.parametrize("lo,hi", [(200, 4000)])
    def test_max_tokens_generate_within_bounds(self, conf, lo, hi):
        val = conf.getint("generate", "max_tokens_generate")
        assert lo <= val <= hi, f"max_tokens_generate={val} not in [{lo}, {hi}]"


# ── [judge] section tests ───────────────────────────────────────────────


class TestJudgeSection:
    """Validate [judge] section keys and value bounds."""

    def test_max_tokens_judge_exists(self, conf):
        assert conf.has_option("judge", "max_tokens_judge")

    def test_max_tokens_judge_is_int(self, conf):
        val = conf.getint("judge", "max_tokens_judge")
        assert isinstance(val, int)

    @pytest.mark.parametrize("lo,hi", [(50, 500)])
    def test_max_tokens_judge_within_bounds(self, conf, lo, hi):
        val = conf.getint("judge", "max_tokens_judge")
        assert lo <= val <= hi, f"max_tokens_judge={val} not in [{lo}, {hi}]"

    def test_judge_retry_count_exists(self, conf):
        assert conf.has_option("judge", "judge_retry_count")

    def test_judge_retry_count_is_int(self, conf):
        val = conf.getint("judge", "judge_retry_count")
        assert isinstance(val, int)

    @pytest.mark.parametrize("lo,hi", [(0, 5)])
    def test_judge_retry_count_within_bounds(self, conf, lo, hi):
        val = conf.getint("judge", "judge_retry_count")
        assert lo <= val <= hi, f"judge_retry_count={val} not in [{lo}, {hi}]"


# ── [judge_criteria] section tests ──────────────────────────────────────


class TestJudgeCriteriaSection:
    """Validate [judge_criteria] weight values (HIGH/MED/LOW)."""

    EXPECTED_KEYS = {"clear_thesis", "evidence", "hook", "conclusion", "concise"}
    VALID_WEIGHTS = {"HIGH", "MED", "LOW"}

    def test_all_criteria_keys_present(self, conf):
        actual = set(conf.options("judge_criteria"))
        missing = self.EXPECTED_KEYS - actual
        assert not missing, f"Missing criteria keys: {missing}"

    def test_no_extra_criteria_keys(self, conf):
        actual = set(conf.options("judge_criteria"))
        extra = actual - self.EXPECTED_KEYS
        assert not extra, f"Unexpected criteria keys: {extra}"

    def test_all_weights_valid(self, conf):
        for key in conf.options("judge_criteria"):
            val = conf.get("judge_criteria", key).strip()
            assert val in self.VALID_WEIGHTS, (
                f"judge_criteria.{key}={val!r} not in {self.VALID_WEIGHTS}"
            )

    @pytest.mark.parametrize("key", ["clear_thesis", "evidence"])
    def test_core_criteria_are_high(self, conf, key):
        """Core criteria (clear_thesis, evidence) should be weighted HIGH."""
        val = conf.get("judge_criteria", key).strip()
        assert val == "HIGH", f"Expected {key}=HIGH, got {val}"

    def test_concise_is_lowest_weight(self, conf):
        """'concise' should have the lowest weight (LOW)."""
        val = conf.get("judge_criteria", "concise").strip()
        assert val == "LOW", f"Expected concise=LOW, got {val}"


# ── Structural / whitespace tests ───────────────────────────────────────


class TestStructure:
    """Verify config file structure: comments, no trailing whitespace issues."""

    def test_file_starts_with_comment(self):
        """First non-blank line should be a comment describing the file."""
        lines = CONF_PATH.read_text().splitlines()
        first = next((l for l in lines if l.strip()), "")
        assert first.startswith("#"), "File should start with a comment"

    def test_bounds_documented_as_comments(self):
        """Each numeric bound should appear as a comment near its key."""
        text = CONF_PATH.read_text()
        assert "bounds:" in text or "bounds :" in text, (
            "Numeric values should document their bounds in comments"
        )
