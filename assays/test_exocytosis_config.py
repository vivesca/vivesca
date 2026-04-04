from __future__ import annotations

"""Tests for effectors/exocytosis.conf — garden post pipeline config."""

import configparser
from pathlib import Path

CONF_PATH = Path(__file__).parent.parent / "effectors" / "exocytosis.conf"


def test_config_exists():
    """Config file exists at expected path."""
    assert CONF_PATH.exists()
    assert CONF_PATH.is_file()


def test_config_has_expected_sections():
    """Config has all required sections."""
    conf = configparser.ConfigParser()
    conf.read(CONF_PATH)
    assert "generate" in conf.sections()
    assert "censor" in conf.sections()
    assert "censor_criteria" in conf.sections()


def test_generate_section_has_max_tokens():
    """Generate section has max_tokens_generate within bounds."""
    conf = configparser.ConfigParser()
    conf.read(CONF_PATH)
    max_tokens = conf.getint("generate", "max_tokens_generate")
    assert 200 <= max_tokens <= 4000


def test_censor_section_has_expected_keys():
    """Censor section has max_tokens_censor and censor_retry_count."""
    conf = configparser.ConfigParser()
    conf.read(CONF_PATH)
    max_tokens = conf.getint("censor", "max_tokens_censor")
    retry_count = conf.getint("censor", "censor_retry_count")
    assert 50 <= max_tokens <= 500
    assert 0 <= retry_count <= 5


def test_censor_criteria_has_expected_values():
    """Censor criteria are all HIGH, MED, or LOW."""
    conf = configparser.ConfigParser()
    conf.read(CONF_PATH)
    criteria = conf["censor_criteria"]
    allowed_values = {"HIGH", "MED", "LOW"}
    for key in ("clear_thesis", "evidence", "hook", "conclusion", "concise"):
        assert key in criteria
        assert criteria[key].upper() in allowed_values
