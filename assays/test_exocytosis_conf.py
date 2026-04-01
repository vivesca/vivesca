from __future__ import annotations

"""Tests for exocytosis.conf — signal transduction parameters for garden post pipeline."""

import configparser
from pathlib import Path

import pytest

CONF_PATH = Path.home() / "germline" / "effectors" / "exocytosis.conf"


@pytest.fixture()
def conf():
    """Parse exocytosis.conf and return the ConfigParser object."""
    cp = configparser.ConfigParser()
    cp.read(str(CONF_PATH))
    return cp


# ── file existence and parsability ────────────────────────────────────


def test_file_exists():
    """exocytosis.conf exists on disk."""
    assert CONF_PATH.is_file()


def test_file_parses_as_ini(conf):
    """exocytosis.conf is valid INI with the expected sections."""
    expected = {"generate", "judge", "judge_criteria"}
    assert expected.issubset(set(conf.sections()))


# ── [generate] section ────────────────────────────────────────────────


def test_generate_section_has_max_tokens_generate(conf):
    """[generate] contains max_tokens_generate."""
    assert conf.has_option("generate", "max_tokens_generate")


def test_max_tokens_generate_within_bounds(conf):
    """max_tokens_generate is within stated bounds (200–4000)."""
    val = conf.getint("generate", "max_tokens_generate")
    assert 200 <= val <= 4000


def test_max_tokens_generate_is_integer(conf):
    """max_tokens_generate parses as an integer."""
    val = conf.getint("generate", "max_tokens_generate")
    assert isinstance(val, int)


# ── [judge] section ───────────────────────────────────────────────────


def test_judge_section_has_max_tokens_judge(conf):
    """[judge] contains max_tokens_judge."""
    assert conf.has_option("judge", "max_tokens_judge")


def test_max_tokens_judge_within_bounds(conf):
    """max_tokens_judge is within stated bounds (50–500)."""
    val = conf.getint("judge", "max_tokens_judge")
    assert 50 <= val <= 500


def test_judge_section_has_judge_retry_count(conf):
    """[judge] contains judge_retry_count."""
    assert conf.has_option("judge", "judge_retry_count")


def test_judge_retry_count_within_bounds(conf):
    """judge_retry_count is within stated bounds (0–5)."""
    val = conf.getint("judge", "judge_retry_count")
    assert 0 <= val <= 5


def test_judge_retry_count_is_integer(conf):
    """judge_retry_count parses as an integer."""
    val = conf.getint("judge", "judge_retry_count")
    assert isinstance(val, int)


# ── [judge_criteria] section ──────────────────────────────────────────


CRITERIA_KEYS = ["clear_thesis", "evidence", "hook", "conclusion", "concise"]
VALID_WEIGHTS = {"HIGH", "MED", "LOW"}


def test_judge_criteria_section_has_all_keys(conf):
    """[judge_criteria] contains every expected criterion."""
    for key in CRITERIA_KEYS:
        assert conf.has_option("judge_criteria", key), f"missing key: {key}"


@pytest.mark.parametrize("key", CRITERIA_KEYS)
def test_judge_criteria_values_are_valid(conf, key):
    """Each criterion weight is one of HIGH, MED, LOW."""
    val = conf.get("judge_criteria", key).strip().upper()
    assert val in VALID_WEIGHTS, f"{key}={val} not in {VALID_WEIGHTS}"


# ── no unexpected keys ────────────────────────────────────────────────


def test_generate_section_no_extra_keys(conf):
    """[generate] section has exactly the expected keys."""
    expected = {"max_tokens_generate"}
    actual = set(conf.options("generate")) - {"__name__"}
    assert actual == expected


def test_judge_section_no_extra_keys(conf):
    """[judge] section has exactly the expected keys."""
    expected = {"max_tokens_judge", "judge_retry_count"}
    actual = set(conf.options("judge")) - {"__name__"}
    assert actual == expected


def test_judge_criteria_section_no_extra_keys(conf):
    """[judge_criteria] section has exactly the expected criteria keys."""
    expected = set(CRITERIA_KEYS)
    actual = set(conf.options("judge_criteria")) - {"__name__"}
    assert actual == expected


# ── actual values snapshot (regression guard) ─────────────────────────


def test_generate_max_tokens_generate_default(conf):
    """max_tokens_generate default is 1000."""
    assert conf.getint("generate", "max_tokens_generate") == 1000


def test_judge_max_tokens_judge_default(conf):
    """max_tokens_judge default is 100."""
    assert conf.getint("judge", "max_tokens_judge") == 100


def test_judge_retry_count_default(conf):
    """judge_retry_count default is 1."""
    assert conf.getint("judge", "judge_retry_count") == 1


def test_judge_criteria_clear_thesis_is_high(conf):
    """clear_thesis weight is HIGH."""
    assert conf.get("judge_criteria", "clear_thesis").strip().upper() == "HIGH"


def test_judge_criteria_evidence_is_high(conf):
    """evidence weight is HIGH."""
    assert conf.get("judge_criteria", "evidence").strip().upper() == "HIGH"


def test_judge_criteria_hook_is_med(conf):
    """hook weight is MED."""
    assert conf.get("judge_criteria", "hook").strip().upper() == "MED"


def test_judge_criteria_conclusion_is_med(conf):
    """conclusion weight is MED."""
    assert conf.get("judge_criteria", "conclusion").strip().upper() == "MED"


def test_judge_criteria_concise_is_low(conf):
    """concise weight is LOW."""
    assert conf.get("judge_criteria", "concise").strip().upper() == "LOW"
