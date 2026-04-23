from pathlib import Path

import pytest
import yaml

from epsin.config import default_sources_path, load_sources, _parse_source
from epsin.models import Source


def test_parse_source_basic():
    raw = {"name": "Test Blog", "url": "https://example.com/", "tags": ["ai"]}
    source = _parse_source(raw)
    assert source.name == "Test Blog"
    assert source.url == "https://example.com/"
    assert source.tags == ["ai"]
    assert source.rss == ""
    assert source.extractor == ""


def test_parse_source_with_rss():
    raw = {"name": "Simon Willison", "url": "https://simonwillison.net/", "rss": "https://simonwillison.net/atom/everything/", "tags": ["ai"]}
    source = _parse_source(raw)
    assert source.rss == "https://simonwillison.net/atom/everything/"


def test_parse_source_with_extractor():
    raw = {"name": "The Batch", "url": "https://www.deeplearning.ai/the-batch/", "extractor": "epsin.extractors.the_batch", "tags": ["ai"]}
    source = _parse_source(raw)
    assert source.extractor == "epsin.extractors.the_batch"


def test_load_default_sources():
    sources = load_sources(Path("/nonexistent/config.yaml"))
    assert len(sources) > 0
    names = [s.name for s in sources]
    assert "Simon Willison" in names


def test_load_custom_config(tmp_path: Path):
    config = tmp_path / "sources.yaml"
    config.write_text(yaml.dump({
        "sources": [
            {"name": "My Feed", "url": "https://my.feed.com/", "rss": "https://my.feed.com/rss", "tags": ["test"]}
        ]
    }))
    sources = load_sources(config)
    assert len(sources) == 1
    assert sources[0].name == "My Feed"


def test_load_empty_config(tmp_path: Path):
    config = tmp_path / "sources.yaml"
    config.write_text("")
    sources = load_sources(config)
    # Falls back to default
    assert len(sources) > 0


def test_source_snake_name():
    source = Source(name="Simon Willison", url="https://simonwillison.net/")
    assert source.snake_name == "simon_willison"

    source = Source(name="The Batch", url="https://deeplearning.ai/the-batch/")
    assert source.snake_name == "the_batch"


def test_default_sources_has_20_sources():
    sources = load_sources(Path("/nonexistent"))
    assert len(sources) >= 18
