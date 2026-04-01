from __future__ import annotations

"""Tests for metabolon.organelles.statolith — AI model benchmark aggregator."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import httpx

import metabolon.organelles.statolith as statolith


@pytest.fixture
def temp_dirs(tmp_path):
    cache_dir = tmp_path / "cache"
    config_dir = tmp_path / "config"
    cache_dir.mkdir()
    config_dir.mkdir()
    with patch.object(statolith, "CACHE_DIR", cache_dir), \
         patch.object(statolith, "CONFIG_DIR", config_dir), \
         patch.object(statolith, "MONITOR_STATE_PATH", config_dir / "monitors.json"), \
         patch.object(statolith, "BUNDLED_MODELS_TOML_PATH", config_dir / "models.toml"):
        yield cache_dir, config_dir


# ============================================================================
# Cache
# ============================================================================

class TestCache:
    def test_set_and_get(self, temp_dirs):
        cache_dir, _ = temp_dirs
        cache = statolith.Cache(ttl_hours=1)
        data = {"key": "value"}
        cache.set("test_source", data)

        path = cache_dir / "test_source.json"
        assert path.exists()

        fetched_at, retrieved_data = cache.get("test_source")
        assert retrieved_data == data
        assert isinstance(fetched_at, datetime)

    def test_get_expired(self, temp_dirs):
        cache_dir, _ = temp_dirs
        cache = statolith.Cache(ttl_hours=1)
        data = {"key": "value"}
        
        # Manually write an expired entry
        fetched_at = datetime.now(UTC) - timedelta(hours=2)
        entry = {
            "fetched_at": fetched_at.isoformat(),
            "ttl_hours": 1,
            "data": data,
        }
        (cache_dir / "expired.json").write_text(json.dumps(entry))
        
        assert cache.get("expired") is None

    def test_clear(self, temp_dirs):
        cache_dir, _ = temp_dirs
        cache = statolith.Cache()
        cache.set("s1", {"a": 1})
        cache.set("s2", {"b": 2})
        assert len(list(cache_dir.glob("*.json"))) == 2
        
        cache.clear()
        assert len(list(cache_dir.glob("*.json"))) == 0


# ============================================================================
# AliasMap
# ============================================================================

class TestAliasMap:
    def test_resolve_canonical(self):
        am = statolith.AliasMap(_map={"gpt-4": "gpt-4-canonical"})
        assert am.resolve("gpt-4") == "gpt-4-canonical"
        assert am.resolve("GPT-4") == "gpt-4-canonical"

    def test_resolve_unknown(self):
        am = statolith.AliasMap(_map={})
        assert am.resolve("unknown-model") == "unknown-model"

    def test_resolve_prefix(self):
        am = statolith.AliasMap(_map={"claude-3-opus": "claude-3-opus-canonical"})
        # claude-3-opus (20240229) should match
        assert am.resolve("claude-3-opus (20240229)") == "claude-3-opus-canonical"
        # claude-3-opus-20240229 should match if it follows the digit rule
        assert am.resolve("claude-3-opus-20240229") == "claude-3-opus-canonical"

    def test_matches(self):
        am = statolith.AliasMap(_map={"gpt4": "gpt-4"})
        assert am.matches("gpt4", "gpt-4")
        assert am.matches("GPT4", "GPT-4")
        assert not am.matches("gpt3", "gpt-4")


# ============================================================================
# Fetchers
# ============================================================================

class TestFetchers:
    @patch("httpx.Client.get")
    def test_fetch_aider(self, mock_get, temp_dirs):
        mock_get.return_value = MagicMock(
            status_code=200,
            text="""
- model: gpt-4
  pass_rate_1: 80.0
  total_cost: 0.05
"""
        )
        cache = statolith.Cache()
        with httpx.Client() as client:
            result = statolith._fetch_aider(cache, client)
        
        assert result.source == "aider"
        assert result.status == "ok"
        assert len(result.scores) == 1
        assert result.scores[0].source_model_name == "gpt-4"
        assert result.scores[0].metrics["pass_rate_1"] == 80.0

    @patch("httpx.Client.get")
    def test_fetch_swebench(self, mock_get, temp_dirs):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "leaderboards": [
                    {
                        "results": [
                            {"name": "model1", "resolved": 15.5}
                        ]
                    }
                ]
            }
        )
        cache = statolith.Cache()
        with httpx.Client() as client:
            result = statolith._fetch_swebench(cache, client)
        
        assert result.source == "swebench"
        assert result.scores[0].source_model_name == "model1"
        assert result.scores[0].metrics["resolved_rate"] == 15.5

    @patch("httpx.Client.get")
    def test_fetch_openrouter(self, mock_get, temp_dirs):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "data": [
                    {
                        "id": "anthropic/claude-3-opus",
                        "pricing": {"prompt": "0.000015", "completion": "0.000075"}
                    }
                ]
            }
        )
        cache = statolith.Cache()
        with httpx.Client() as client:
            result = statolith._fetch_openrouter(cache, client)
        
        assert result.source == "openrouter"
        assert result.scores[0].metrics["prompt_per_1m"] == 15.0
        assert result.scores[0].metrics["completion_per_1m"] == 75.0


# ============================================================================
# Aggregation
# ============================================================================

class TestAggregation:
    def test_aggregate_results(self):
        s1 = statolith.SourceResult(
            source="s1",
            scores=[
                statolith.ModelScore(model="m1", source_model_name="m1", rank=1),
                statolith.ModelScore(model="m2", source_model_name="m2", rank=2),
            ]
        )
        s2 = statolith.SourceResult(
            source="s2",
            scores=[
                statolith.ModelScore(model="m1", source_model_name="m1", rank=1),
                statolith.ModelScore(model="m2", source_model_name="m2", rank=2),
            ]
        )
        
        agg, excluded = statolith.aggregate_results([s1, s2], min_sources=2, show_excluded=True)
        assert len(agg.scores) == 2
        assert agg.scores[0].model == "m1"
        assert agg.scores[0].metrics["avg_percentile"] == 1.0 # (1.0 + 1.0) / 2
        assert agg.scores[1].model == "m2"
        assert agg.scores[1].metrics["avg_percentile"] == 0.0 # (0.0 + 0.0) / 2
        assert not excluded

    def test_aggregate_min_sources(self):
        s1 = statolith.SourceResult(
            source="s1",
            scores=[statolith.ModelScore(model="m1", source_model_name="m1", rank=1)]
        )
        agg, excluded = statolith.aggregate_results([s1], min_sources=2, show_excluded=True)
        assert len(agg.scores) == 0
        assert len(excluded) == 1
        assert excluded[0][0] == "m1"


# ============================================================================
# Recommendation
# ============================================================================

class TestRecommendation:
    def test_rank_models(self):
        results = [
            statolith.SourceResult(
                source="swebench",
                scores=[
                    statolith.ModelScore(model="m1", source_model_name="m1", metrics={"resolved_rate": 20.0}),
                    statolith.ModelScore(model="m2", source_model_name="m2", metrics={"resolved_rate": 10.0}),
                ]
            )
        ]
        aliases = statolith.AliasMap(_map={})
        spec = statolith.TASK_SPECS["coding"]
        
        ranked = statolith._rank_models(spec, results, aliases, top=5)
        assert len(ranked) == 2
        assert ranked[0]["model"] == "m1"
        assert ranked[1]["model"] == "m2"


# ============================================================================
# Monitor
# ============================================================================

class TestMonitor:
    def test_cmd_monitor_add(self, temp_dirs):
        _, config_dir = temp_dirs
        aliases = statolith.AliasMap(_map={})
        statolith.cmd_monitor_add("gpt-4", aliases)
        
        state = json.loads((config_dir / "monitors.json").read_text())
        assert len(state["watched"]) == 1
        assert state["watched"][0]["model"] == "gpt-4"

    def test_cmd_monitor_remove(self, temp_dirs):
        _, config_dir = temp_dirs
        aliases = statolith.AliasMap(_map={})
        (config_dir / "monitors.json").write_text(json.dumps({
            "watched": [{"model": "gpt-4", "added_at": "2024-01-01", "last_seen": {}}]
        }))
        
        statolith.cmd_monitor_remove("gpt-4", aliases)
        state = json.loads((config_dir / "monitors.json").read_text())
        assert len(state["watched"]) == 0
