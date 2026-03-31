"""Tests for metabolon/organelles/endocytosis_rss/config.py"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
import yaml

from metabolon.organelles.endocytosis_rss import config as rss_config


class TestExpandPath:
    """Tests for _expand_path function."""

    def test_expands_home(self) -> None:
        result = rss_config._expand_path("~/test")
        assert "~" not in str(result)
        assert str(result).endswith("test")

    def test_resolves_path(self) -> None:
        result = rss_config._expand_path("/usr/local")
        assert result.is_absolute()


class TestEnvPath:
    """Tests for _env_path function."""

    def test_uses_env_variable(self) -> None:
        with mock.patch.dict(os.environ, {"TEST_VAR": "/custom/path"}):
            result = rss_config._env_path("TEST_VAR", Path("/default"))
            assert str(result) == "/custom/path"

    def test_uses_default_if_not_set(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = rss_config._env_path("NONEXISTENT_VAR", Path("/default"))
            assert "default" in str(result)


class TestXdgBase:
    """Tests for _xdg_base function."""

    def test_uses_xdg_env(self) -> None:
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            result = rss_config._xdg_base("XDG_CONFIG_HOME", ".config")
            assert str(result) == "/custom/config"

    def test_uses_fallback(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = rss_config._xdg_base("XDG_CONFIG_HOME", ".config")
            assert ".config" in str(result)


class TestExpandEnvVars:
    """Tests for _expand_env_vars function."""

    def test_expands_env_vars(self) -> None:
        with mock.patch.dict(os.environ, {"MY_VAR": "expanded"}):
            result = rss_config._expand_env_vars("prefix_${MY_VAR}_suffix")
            assert result == "prefix_expanded_suffix"

    def test_returns_unchanged_if_no_vars(self) -> None:
        result = rss_config._expand_env_vars("plain text")
        assert result == "plain text"


class TestLoadYaml:
    """Tests for _load_yaml function."""

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text("key: value\n", encoding="utf-8")
        result = rss_config._load_yaml(yaml_path)
        assert result == {"key": "value"}

    def test_returns_empty_for_nonexistent(self, tmp_path: Path) -> None:
        result = rss_config._load_yaml(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_invalid_yaml_raises_exception(self, tmp_path: Path) -> None:
        """Invalid YAML raises a ScannerError (not caught by _load_yaml)."""
        import yaml
        yaml_path = tmp_path / "invalid.yaml"
        yaml_path.write_text("::: invalid yaml :::", encoding="utf-8")
        # _load_yaml lets YAML exceptions propagate (catches OSError only)
        with pytest.raises(yaml.scanner.ScannerError):
            rss_config._load_yaml(yaml_path)

    def test_returns_empty_for_non_dict(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "list.yaml"
        yaml_path.write_text("- item1\n- item2\n", encoding="utf-8")
        result = rss_config._load_yaml(yaml_path)
        assert result == {}

    def test_expands_env_vars(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "test.yaml"
        with mock.patch.dict(os.environ, {"MY_VAR": "expanded"}):
            yaml_path.write_text("path: ${MY_VAR}/subdir\n", encoding="utf-8")
            result = rss_config._load_yaml(yaml_path)
            assert result["path"] == "expanded/subdir"


class TestDefaultSourcesPath:
    """Tests for default_sources_path function."""

    def test_returns_path_object(self) -> None:
        result = rss_config.default_sources_path()
        assert isinstance(result, Path)

    def test_path_exists(self) -> None:
        result = rss_config.default_sources_path()
        assert result.exists()


class TestDefaultSourcesText:
    """Tests for default_sources_text function."""

    def test_returns_string(self) -> None:
        result = rss_config.default_sources_text()
        assert isinstance(result, str)

    def test_is_valid_yaml(self) -> None:
        result = rss_config.default_sources_text()
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, dict)


class TestEndocytosisConfig:
    """Tests for EndocytosisConfig dataclass."""

    def test_sources_property_extracts_list(self, tmp_path: Path) -> None:
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            sources_data={
                "section1": [{"name": "source1"}, {"name": "source2"}],
                "section2": [{"name": "source3"}],
            },
        )
        sources = cfg.sources
        assert len(sources) == 3

    def test_sources_ignores_non_lists(self, tmp_path: Path) -> None:
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            sources_data={
                "section1": "not a list",
                "section2": [{"name": "source1"}],
            },
        )
        sources = cfg.sources
        assert len(sources) == 1

    def test_sources_empty_if_no_sources_data(self, tmp_path: Path) -> None:
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            sources_data={},
        )
        assert cfg.sources == []

    def test_resolve_bird_returns_none_if_not_found(self, tmp_path: Path) -> None:
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            bird_path="/nonexistent/path/to/bird",
        )
        result = cfg.resolve_bird()
        assert result is None

    def test_resolve_bird_returns_path_if_exists(self, tmp_path: Path) -> None:
        bird_path = tmp_path / "bird"
        bird_path.touch()
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            bird_path=str(bird_path),
        )
        result = cfg.resolve_bird()
        assert result == str(bird_path)

    def test_resolve_tg_notify_returns_none_if_not_found(self, tmp_path: Path) -> None:
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            tg_notify_path="/nonexistent/path/to/tg-notify.sh",
        )
        result = cfg.resolve_tg_notify()
        assert result is None

    def test_resolve_tg_notify_returns_path_if_exists(self, tmp_path: Path) -> None:
        tg_path = tmp_path / "tg-notify.sh"
        tg_path.touch()
        cfg = rss_config.EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            tg_notify_path=str(tg_path),
        )
        result = cfg.resolve_tg_notify()
        assert result == str(tg_path)


class TestRestoreConfig:
    """Tests for restore_config function."""

    def test_returns_endocytosis_config(self, tmp_path: Path) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "XDG_CACHE_HOME": str(tmp_path / "cache"),
                "XDG_DATA_HOME": str(tmp_path / "data"),
            },
        ):
            cfg = rss_config.restore_config()
            assert isinstance(cfg, rss_config.EndocytosisConfig)

    def test_uses_env_overrides(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "custom_config"
        cache_dir = tmp_path / "custom_cache"
        data_dir = tmp_path / "custom_data"

        with mock.patch.dict(
            os.environ,
            {
                "ENDOCYTOSIS_CONFIG_DIR": str(config_dir),
                "ENDOCYTOSIS_CACHE_DIR": str(cache_dir),
                "ENDOCYTOSIS_DATA_DIR": str(data_dir),
            },
        ):
            cfg = rss_config.restore_config()
            assert cfg.config_dir == config_dir
            assert cfg.cache_dir == cache_dir
            assert cfg.data_dir == data_dir

    def test_loads_config_yaml(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        config_yaml = config_dir / "config.yaml"
        config_yaml.write_text("digest_model: custom_model\n", encoding="utf-8")

        with mock.patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": str(tmp_path / "xdg_config"),
                "XDG_CACHE_HOME": str(tmp_path / "cache"),
                "XDG_DATA_HOME": str(tmp_path / "data"),
                "ENDOCYTOSIS_CONFIG_DIR": str(config_dir),
            },
        ):
            cfg = rss_config.restore_config()
            assert cfg.digest_model == "custom_model"

    def test_loads_sources_yaml(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        sources_yaml = config_dir / "sources.yaml"
        sources_yaml.write_text(
            "rss_feeds:\n  - name: test\n    url: https://example.com\n",
            encoding="utf-8",
        )

        with mock.patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": str(tmp_path / "xdg_config"),
                "XDG_CACHE_HOME": str(tmp_path / "cache"),
                "XDG_DATA_HOME": str(tmp_path / "data"),
                "ENDOCYTOSIS_CONFIG_DIR": str(config_dir),
            },
        ):
            cfg = rss_config.restore_config()
            assert "rss_feeds" in cfg.sources_data
