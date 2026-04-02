from __future__ import annotations

"""Tests for effectors/exocytosis.conf — garden post pipeline signal parameters."""

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


# ── File-level ──────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert CONF_PATH.exists(), f"{CONF_PATH} not found"

    def test_file_non_empty(self):
        assert CONF_PATH.stat().st_size > 0, "exocytosis.conf is empty"

    def test_file_valid_ini(self, conf):
        assert len(conf.sections()) > 0, "No sections parsed"


# ── Sections ────────────────────────────────────────────────────────────


class TestSections:
    EXPECTED = {"generate", "judge", "judge_criteria"}

    def test_all_sections_present(self, conf):
        missing = self.EXPECTED - set(conf.sections())
        assert not missing, f"Missing sections: {missing}"

    def test_no_extra_sections(self, conf):
        extra = set(conf.sections()) - self.EXPECTED
        assert not extra, f"Unexpected sections: {extra}"


# ── [generate] ──────────────────────────────────────────────────────────


class TestGenerateSection:
    def test_max_tokens_generate_exists(self, conf):
        assert conf.has_option("generate", "max_tokens_generate")

    def test_max_tokens_generate_is_int(self, conf):
        assert isinstance(conf.getint("generate", "max_tokens_generate"), int)

    @pytest.mark.parametrize("lo,hi", [(200, 4000)])
    def test_max_tokens_generate_in_bounds(self, conf, lo, hi):
        val = conf.getint("generate", "max_tokens_generate")
        assert lo <= val <= hi, f"max_tokens_generate={val} outside [{lo},{hi}]"


# ── [judge] ─────────────────────────────────────────────────────────────


class TestJudgeSection:
    def test_max_tokens_judge_exists(self, conf):
        assert conf.has_option("judge", "max_tokens_judge")

    def test_max_tokens_judge_is_int(self, conf):
        assert isinstance(conf.getint("judge", "max_tokens_judge"), int)

    @pytest.mark.parametrize("lo,hi", [(50, 500)])
    def test_max_tokens_judge_in_bounds(self, conf, lo, hi):
        val = conf.getint("judge", "max_tokens_judge")
        assert lo <= val <= hi, f"max_tokens_judge={val} outside [{lo},{hi}]"

    def test_judge_retry_count_exists(self, conf):
        assert conf.has_option("judge", "judge_retry_count")

    def test_judge_retry_count_is_int(self, conf):
        assert isinstance(conf.getint("judge", "judge_retry_count"), int)

    @pytest.mark.parametrize("lo,hi", [(0, 5)])
    def test_judge_retry_count_in_bounds(self, conf, lo, hi):
        val = conf.getint("judge", "judge_retry_count")
        assert lo <= val <= hi, f"judge_retry_count={val} outside [{lo},{hi}]"


# ── [judge_criteria] ────────────────────────────────────────────────────


class TestJudgeCriteriaSection:
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
        val = conf.get("judge_criteria", key).strip()
        assert val == "HIGH", f"Expected {key}=HIGH, got {val}"

    def test_concise_is_low(self, conf):
        val = conf.get("judge_criteria", "concise").strip()
        assert val == "LOW", f"Expected concise=LOW, got {val}"


# ── Structural ──────────────────────────────────────────────────────────


class TestStructure:
    def test_file_starts_with_comment(self):
        lines = CONF_PATH.read_text().splitlines()
        first = next((l for l in lines if l.strip()), "")
        assert first.startswith("#"), "File should start with a comment"

    def test_bounds_documented(self):
        text = CONF_PATH.read_text()
        assert "bounds:" in text or "bounds :" in text, (
            "Numeric values should document their bounds in comments"
        )
