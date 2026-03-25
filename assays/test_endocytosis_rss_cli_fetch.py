from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import typer

from metabolon.organelles.endocytosis_rss.cli import _fetch_locked
from metabolon.organelles.endocytosis_rss.config import EndocytosisConfig


def _call_fetch_locked(cfg, no_archive: bool) -> None:
    """Wrap _fetch_locked to absorb the typer.Exit it always raises."""
    try:
        _fetch_locked(cfg, no_archive=no_archive)
    except typer.Exit:
        pass


@pytest.fixture
def mock_cfg(tmp_path):
    config_dir = tmp_path / "config"
    cache_dir = tmp_path / "cache"
    data_dir = tmp_path / "data"
    for d in [config_dir, cache_dir, data_dir]:
        d.mkdir(parents=True)
    
    cfg_data = {
        "web_sources": [
            {"name": "FallbackSource", "tier": 1, "rss": "https://dead.rss", "url": "https://live.web"}
        ]
    }
    
    return EndocytosisConfig(
        config_dir=config_dir,
        cache_dir=cache_dir,
        data_dir=data_dir,
        config_path=config_dir / "config.yaml",
        sources_path=config_dir / "sources.yaml",
        state_path=data_dir / "state.json",
        log_path=data_dir / "news.md",
        article_cache_dir=cache_dir / "articles",
        digest_output_dir=data_dir / "digests",
        digest_model="test-model",
        sources_data=cfg_data
    )


def test_fetch_fallback_and_zeros(monkeypatch, mock_cfg, capsys):
    # Mock fetch functions
    # 1. First call: internalize_rss returns None, internalize_web returns results
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.fetcher.internalize_rss", lambda _url, _since, **kwargs: None)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.fetcher.internalize_web", lambda _url, **kwargs: [{"title": "Web Article", "link": "https://live.web/1"}])

    # Mock other needed functions
    # Patch both the module attribute and the name bound in cli's namespace
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.state.refractory_elapsed", lambda *args, **kwargs: True)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.cli.refractory_elapsed", lambda *args, **kwargs: True)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.relevance.get_receptor_signal_ratio", lambda *args, **kwargs: 1.0)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.relevance.score_cargo", lambda *a, **kw: {"score": 5, "banking_angle": "N/A", "talking_point": "N/A"})
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.log.rotate_log", lambda *args: None)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.log.load_title_prefixes", lambda _p: set())
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.log.is_junk", lambda _t: False)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.log.format_markdown", lambda *args: "# News")
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.log.append_to_log", lambda *args: None)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.fetcher.archive_cargo", lambda *args: None)

    # Run once for fallback success
    _call_fetch_locked(mock_cfg, no_archive=True)

    stderr = capsys.readouterr().err
    assert "falling back to web" in stderr.lower()

    # 2. Mock internalize_web to return nothing to test zeros
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.fetcher.internalize_web", lambda _url, **kwargs: [])

    # Run 5 times to see the warning
    for i in range(5):
        _call_fetch_locked(mock_cfg, no_archive=True)
    
    stderr = capsys.readouterr().err
    assert "Warning: FallbackSource has 5 consecutive zero-article fetches" in stderr

    # Verify state file directly
    import json
    state = json.loads(mock_cfg.state_path.read_text())
    assert state["_zeros:FallbackSource"] == "5"
