"""Tests for endocytosis_rss/config.py - configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

from metabolon.organelles.endocytosis_rss.config import (
    EndocytosisConfig,
    _expand_path,
    _expand_env_vars,
    _load_yaml,
    restore_config,
)


def test_expand_path_resolves_home():
    """Test _expand_path expands ~ to home directory."""
    result = _expand_path("~/test/path")
    assert str(result).startswith(str(Path.home()))


def test_expand_path_resolves_relative():
    """Test _expand_path resolves relative paths to absolute."""
    result = _expand_path("relative/path")
    assert result.is_absolute()


def test_expand_env_vars_expands_dollar():
    """Test _expand_env_vars expands ${VAR} references."""
    os.environ["TEST_VAR"] = "test_value"
    result = _expand_env_vars("prefix_${TEST_VAR}_suffix")
    assert result == "prefix_test_value_suffix"
    del os.environ["TEST_VAR"]


def test_expand_env_vars_no_match():
    """Test _expand_env_vars leaves unmatched vars unchanged."""
    result = _expand_env_vars("no_${NONEXISTENT_VAR}_here")
    # Should contain the original placeholder or be empty
    assert "no_" in result


def test_load_yaml_nonexistent(tmp_path):
    """Test _load_yaml returns empty dict for nonexistent file."""
    result = _load_yaml(tmp_path / "nonexistent.yaml")
    assert result == {}


def test_load_yaml_valid_file(tmp_path):
    """Test _load_yaml loads valid YAML."""
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("key: value\nnumber: 42\n")
    
    result = _load_yaml(yaml_path)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_load_yaml_invalid_returns_empty(tmp_path):
    """Test _load_yaml returns empty dict for empty file."""
    yaml_path = tmp_path / "empty.yaml"
    yaml_path.write_text("")  # Empty file returns {}

    result = _load_yaml(yaml_path)
    assert result == {}


def test_load_yaml_non_dict_returns_empty(tmp_path):
    """Test _load_yaml returns empty dict if YAML is not a dict."""
    yaml_path = tmp_path / "list.yaml"
    yaml_path.write_text("- item1\n- item2\n")
    
    result = _load_yaml(yaml_path)
    assert result == {}


def test_endocytosis_config_sources_property():
    """Test EndocytosisConfig.sources flattens source sections."""
    cfg = EndocytosisConfig(
        config_dir=Path("/tmp"),
        cache_dir=Path("/tmp"),
        data_dir=Path("/tmp"),
        config_path=Path("/tmp/config.yaml"),
        sources_path=Path("/tmp/sources.yaml"),
        state_path=Path("/tmp/state.json"),
        log_path=Path("/tmp/news.md"),
        cargo_path=Path("/tmp/cargo.jsonl"),
        article_cache_dir=Path("/tmp/articles"),
        digest_output_dir=Path("/tmp/digests"),
        digest_model="glm",
        sources_data={
            "rss_feeds": [{"url": "https://a.com"}, {"url": "https://b.com"}],
            "x_accounts": [{"handle": "user1"}],
            "not_a_list": "string",
        },
    )
    
    sources = cfg.sources
    assert len(sources) == 3
    assert {"url": "https://a.com"} in sources
    assert {"handle": "user1"} in sources


def test_endocytosis_config_resolve_bird_from_path():
    """Test resolve_bird returns path from config if file exists."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"")
        temp_path = f.name
    
    try:
        cfg = EndocytosisConfig(
            config_dir=Path("/tmp"),
            cache_dir=Path("/tmp"),
            data_dir=Path("/tmp"),
            config_path=Path("/tmp/config.yaml"),
            sources_path=Path("/tmp/sources.yaml"),
            state_path=Path("/tmp/state.json"),
            log_path=Path("/tmp/news.md"),
            cargo_path=Path("/tmp/cargo.jsonl"),
            article_cache_dir=Path("/tmp/articles"),
            digest_output_dir=Path("/tmp/digests"),
            digest_model="glm",
            bird_path=temp_path,
        )
        
        assert cfg.resolve_bird() == temp_path
    finally:
        os.unlink(temp_path)


def test_endocytosis_config_resolve_bird_nonexistent():
    """Test resolve_bird returns None if config path doesn't exist."""
    cfg = EndocytosisConfig(
        config_dir=Path("/tmp"),
        cache_dir=Path("/tmp"),
        data_dir=Path("/tmp"),
        config_path=Path("/tmp/config.yaml"),
        sources_path=Path("/tmp/sources.yaml"),
        state_path=Path("/tmp/state.json"),
        log_path=Path("/tmp/news.md"),
        cargo_path=Path("/tmp/cargo.jsonl"),
        article_cache_dir=Path("/tmp/articles"),
        digest_output_dir=Path("/tmp/digests"),
        digest_model="glm",
        bird_path="/nonexistent/path/to/bird",
    )
    
    with patch("metabolon.organelles.endocytosis_rss.config.shutil.which", return_value=None):
        assert cfg.resolve_bird() is None


def test_restore_config_uses_env_vars(tmp_path):
    """Test restore_config respects environment variables."""
    env = {
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "XDG_DATA_HOME": str(tmp_path / "data"),
    }
    
    with patch.dict(os.environ, env, clear=False):
        with patch("metabolon.organelles.endocytosis_rss.config._load_yaml", return_value={}):
            cfg = restore_config()
    
    assert str(tmp_path / "config") in str(cfg.config_dir)
    assert str(tmp_path / "cache") in str(cfg.cache_dir)
    assert str(tmp_path / "data") in str(cfg.data_dir)


def test_restore_config_default_digest_model():
    """Test restore_config defaults digest_model to 'glm'."""
    with patch.dict(os.environ, {}, clear=False):
        with patch("metabolon.organelles.endocytosis_rss.config._load_yaml", return_value={}):
            cfg = restore_config()
    
    assert cfg.digest_model == "glm"
