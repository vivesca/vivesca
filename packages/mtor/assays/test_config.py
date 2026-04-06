"""Tests for mtor config loader."""

import textwrap
from pathlib import Path

from mtor.config import MtorConfig, ProviderConfig


def test_default_config():
    cfg = MtorConfig()
    assert cfg.coaching_file is None
    assert cfg.providers == {}
    assert cfg.log_file == Path("mtor.jsonl")


def test_load_from_toml(tmp_path: Path):
    toml_content = textwrap.dedent("""\
        [mtor]
        coaching_file = "coaching.md"
        default_provider = "test"

        [providers.test]
        url = "https://example.com/v1"
        model = "test-model"
        key_env = "TEST_API_KEY"
        concurrency = 2
        harness = "claude"
    """)
    cfg_path = tmp_path / "mtor.toml"
    cfg_path.write_text(toml_content)
    cfg = MtorConfig._from_file(cfg_path)
    assert cfg.coaching_file == Path("coaching.md")
    assert "test" in cfg.providers
    assert cfg.providers["test"].model == "test-model"
    assert cfg.providers["test"].concurrency == 2
    assert cfg.default_provider == "test"


def test_provider_api_key(monkeypatch):
    monkeypatch.setenv("MY_KEY", "secret123")
    prov = ProviderConfig(name="p", url="http://x", model="m", key_env="MY_KEY")
    assert prov.api_key == "secret123"


def test_provider_missing_key():
    prov = ProviderConfig(name="p", url="http://x", model="m", key_env="NONEXISTENT_KEY_XYZ")
    assert prov.api_key is None
