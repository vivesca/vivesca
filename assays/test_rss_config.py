"""Tests for metabolon.organelles.endocytosis_rss.config."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.endocytosis_rss.config import (
    EndocytosisConfig,
    _expand_env_vars,
    _expand_path,
    _env_path,
    _load_yaml,
    _xdg_base,
    default_sources_path,
    restore_config,
)


# ---------------------------------------------------------------------------
# _expand_path
# ---------------------------------------------------------------------------

class TestExpandPath:
    def test_resolves_relative_to_absolute(self, tmp_path):
        target = tmp_path / "sub"
        target.mkdir()
        result = _expand_path(tmp_path / "sub" / ".." / "sub")
        assert result == target.resolve()

    def test_expands_home_tilde(self):
        result = _expand_path("~/some/dir")
        assert str(result).startswith(str(Path.home()))
        assert "~" not in str(result)


# ---------------------------------------------------------------------------
# _env_path
# ---------------------------------------------------------------------------

class TestEnvPath:
    def test_uses_env_when_set(self, tmp_path):
        target = tmp_path / "from_env"
        target.mkdir()
        with patch.dict(os.environ, {"MY_DIR": str(target)}):
            result = _env_path("MY_DIR", Path("/default"))
        assert result == target.resolve()

    def test_falls_back_to_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NONEXISTENT_VAR_12345", None)
            result = _env_path("NONEXISTENT_VAR_12345", Path("/default/path"))
        assert result == Path("/default/path").resolve()


# ---------------------------------------------------------------------------
# _xdg_base
# ---------------------------------------------------------------------------

class TestXdgBase:
    def test_returns_env_override(self):
        custom = Path.home() / "custom_xdg"
        with patch.dict(os.environ, {"XDG_CUSTOM_HOME": str(custom)}):
            result = _xdg_base("XDG_CUSTOM_HOME", ".default_xdg")
        assert result == custom.resolve()

    def test_falls_back_to_home_suffix(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("XDG_FAKE_HOME_99999", None)
            result = _xdg_base("XDG_FAKE_HOME_99999", ".fallback_dir")
        assert result == (Path.home() / ".fallback_dir").resolve()


# ---------------------------------------------------------------------------
# _expand_env_vars
# ---------------------------------------------------------------------------

class TestExpandEnvVars:
    def test_expands_dollar_brace(self):
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            assert _expand_env_vars("${MY_VAR}/world") == "hello/world"

    def test_no_change_when_no_vars(self):
        assert _expand_env_vars("plain text") == "plain text"


# ---------------------------------------------------------------------------
# _load_yaml
# ---------------------------------------------------------------------------

class TestLoadYaml:
    def test_returns_empty_for_missing_file(self, tmp_path):
        assert _load_yaml(tmp_path / "nonexistent.yaml") == {}

    def test_loads_valid_yaml(self, tmp_path):
        p = tmp_path / "test.yaml"
        p.write_text("key: value\nlist:\n  - a\n  - b\n")
        result = _load_yaml(p)
        assert result == {"key": "value", "list": ["a", "b"]}

    def test_expands_env_vars_in_yaml(self, tmp_path):
        p = tmp_path / "env.yaml"
        p.write_text("path: ${TEST_RSS_CONFIG_X}/sub")
        with patch.dict(os.environ, {"TEST_RSS_CONFIG_X": "/opt"}):
            result = _load_yaml(p)
        assert result == {"path": "/opt/sub"}

    def test_returns_empty_for_non_dict_content(self, tmp_path):
        p = tmp_path / "scalar.yaml"
        p.write_text("- just\n- a\n- list\n")
        # YAML list is not a dict → should return {}
        assert _load_yaml(p) == {}

    def test_returns_empty_for_empty_file(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("")
        assert _load_yaml(p) == {}


# ---------------------------------------------------------------------------
# EndocytosisConfig.sources property
# ---------------------------------------------------------------------------

class TestEndocytosisConfigSources:
    def _make_config(self, sources_data):
        return EndocytosisConfig(
            config_dir=Path("/tmp/c"),
            cache_dir=Path("/tmp/cache"),
            data_dir=Path("/tmp/data"),
            config_path=Path("/tmp/c/config.yaml"),
            sources_path=Path("/tmp/c/sources.yaml"),
            state_path=Path("/tmp/cache/state.json"),
            log_path=Path("/tmp/data/news.md"),
            cargo_path=Path("/tmp/cache/cargo.jsonl"),
            article_cache_dir=Path("/tmp/cache/articles"),
            digest_output_dir=Path("/tmp/data/digests"),
            digest_model="glm",
            sources_data=sources_data,
        )

    def test_flattens_sections(self):
        data = {
            "tech": [{"url": "a"}, {"url": "b"}],
            "science": [{"url": "c"}],
        }
        cfg = self._make_config(data)
        assert len(cfg.sources) == 3
        assert [s["url"] for s in cfg.sources] == ["a", "b", "c"]

    def test_skips_non_dict_items(self):
        data = {"misc": [{"url": "x"}, "bad_string", 42]}
        cfg = self._make_config(data)
        assert len(cfg.sources) == 1

    def test_empty_data(self):
        cfg = self._make_config({})
        assert cfg.sources == []


# ---------------------------------------------------------------------------
# EndocytosisConfig.resolve_bird / resolve_tg_notify
# ---------------------------------------------------------------------------

class TestResolveTools:
    def _base_kwargs(self):
        return dict(
            config_dir=Path("/tmp/c"),
            cache_dir=Path("/tmp/cache"),
            data_dir=Path("/tmp/data"),
            config_path=Path("/tmp/c/config.yaml"),
            sources_path=Path("/tmp/c/sources.yaml"),
            state_path=Path("/tmp/cache/state.json"),
            log_path=Path("/tmp/data/news.md"),
            cargo_path=Path("/tmp/cache/cargo.jsonl"),
            article_cache_dir=Path("/tmp/cache/articles"),
            digest_output_dir=Path("/tmp/data/digests"),
            digest_model="glm",
        )

    def test_resolve_bird_returns_none_when_no_override_and_not_on_path(self):
        cfg = EndocytosisConfig(**self._base_kwargs())
        with patch("metabolon.organelles.endocytosis_rss.config.shutil.which", return_value=None):
            assert cfg.resolve_bird() is None

    def test_resolve_bird_returns_override_if_file_exists(self, tmp_path):
        script = tmp_path / "bird"
        script.write_text("#!/bin/sh")
        cfg = EndocytosisConfig(bird_path=str(script), **self._base_kwargs())
        assert cfg.resolve_bird() == str(script)

    def test_resolve_bird_returns_none_if_override_missing(self, tmp_path):
        cfg = EndocytosisConfig(bird_path=str(tmp_path / "nonexistent"), **self._base_kwargs())
        assert cfg.resolve_bird() is None

    def test_resolve_tg_notify_finds_on_path(self):
        cfg = EndocytosisConfig(**self._base_kwargs())
        with patch("metabolon.organelles.endocytosis_rss.config.shutil.which", return_value="/usr/local/bin/tg-notify.sh"):
            assert cfg.resolve_tg_notify() == "/usr/local/bin/tg-notify.sh"

    def test_resolve_tg_notify_finds_home_scripts_fallback(self, tmp_path):
        cfg = EndocytosisConfig(**self._base_kwargs())
        fallback = tmp_path / "scripts" / "tg-notify.sh"
        fallback.parent.mkdir(parents=True)
        fallback.write_text("#!/bin/sh")
        with patch("metabolon.organelles.endocytosis_rss.config.shutil.which", return_value=None), \
             patch("metabolon.organelles.endocytosis_rss.config.Path.home", return_value=tmp_path):
            assert cfg.resolve_tg_notify() == str(fallback)


# ---------------------------------------------------------------------------
# restore_config
# ---------------------------------------------------------------------------

class TestRestoreConfig:
    def test_returns_endocytosis_config(self):
        with patch.dict(os.environ, {
            "XDG_CONFIG_HOME": "/tmp/xdg_conf",
            "XDG_CACHE_HOME": "/tmp/xdg_cache",
            "XDG_DATA_HOME": "/tmp/xdg_data",
        }):
            cfg = restore_config()
        assert isinstance(cfg, EndocytosisConfig)
        assert cfg.config_dir == Path("/tmp/xdg_conf/endocytosis").resolve()
        assert cfg.cache_dir == Path("/tmp/xdg_cache/endocytosis").resolve()
        assert cfg.data_dir == Path("/tmp/xdg_data/endocytosis").resolve()
        assert cfg.digest_model == "glm"

    def test_uses_env_override_dirs(self):
        with patch.dict(os.environ, {
            "ENDOCYTOSIS_CONFIG_DIR": "/tmp/my_conf",
            "ENDOCYTOSIS_CACHE_DIR": "/tmp/my_cache",
            "ENDOCYTOSIS_DATA_DIR": "/tmp/my_data",
        }, clear=False):
            # Ensure XDG vars don't interfere
            for v in ["XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"]:
                os.environ.pop(v, None)
            cfg = restore_config()
        assert cfg.config_dir == Path("/tmp/my_conf").resolve()
        assert cfg.cache_dir == Path("/tmp/my_cache").resolve()
        assert cfg.data_dir == Path("/tmp/my_data").resolve()

    def test_loads_sources_from_config(self, tmp_path):
        sources = tmp_path / "sources.yaml"
        sources.write_text("feeds:\n  - url: http://example.com/rss\n")
        with patch.dict(os.environ, {"ENDOCYTOSIS_CONFIG_DIR": str(tmp_path)}, clear=False):
            for v in ["XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"]:
                os.environ.pop(v, None)
            cfg = restore_config()
        assert len(cfg.sources) == 1
        assert cfg.sources[0]["url"] == "http://example.com/rss"
