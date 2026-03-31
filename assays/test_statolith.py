"""Tests for statolith.py — AI model benchmark aggregator."""

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import tomllib
import httpx

from metabolon.organelles.statolith import (
    AliasMap,
    Cache,
    ModelScore,
    SourceResult,
    _build_alias_map,
    _canonical_model_name,
    _extract_cell_value,
    _extract_metric,
    _extract_swebench_model_score,
    _get_float,
    _get_int,
    _is_image_or_video_model,
    _load_alias_toml,
    _map_command_error,
    _parse_arena_from_snapshot,
    _parse_arena_json_response,
    _parse_aider_scores,
    _parse_scored_cached,
    _parse_swebench_scores,
    _percentile,
    _rank_models,
    _std_dev,
    aggregate_results,
    classify_effort_level,
    apply_aa_effort_filter,
)


class TestClassifyEffortLevel:
    def test_max_effort(self):
        assert classify_effort_level("Model (max)") == "max"
        assert classify_effort_level("adaptive Model") == "max"

    def test_low_effort(self):
        assert classify_effort_level("Model low-effort") == "low"
        assert classify_effort_level("Model low effort") == "low"
        assert classify_effort_level("Model (low)") == "low"

    def test_standard_effort(self):
        assert classify_effort_level("Regular Model") == "standard"
        assert classify_effort_level("model") == "standard"
        assert classify_effort_level("") == "standard"
        assert classify_effort_level("MAX") == "standard"  # Only contains as substring
        assert classify_effort_level("LOW") == "standard"


class TestApplyAaEffortFilter:
    def test_no_filter_when_all(self):
        results = [
            SourceResult(
                source="artificial-analysis",
                scores=[
                    ModelScore(model="model1", source_model_name="Model (max)"),
                    ModelScore(model="model2", source_model_name="Model (low)"),
                    ModelScore(model="model3", source_model_name="Model"),
                ],
            )
        ]
        apply_aa_effort_filter(results, "all")
        assert len(results[0].scores) == 3

    def test_filter_max(self):
        results = [
            SourceResult(
                source="artificial-analysis",
                scores=[
                    ModelScore(model="model1", source_model_name="Model (max)"),
                    ModelScore(model="model2", source_model_name="Model (low)"),
                    ModelScore(model="model3", source_model_name="Model"),
                ],
            )
        ]
        apply_aa_effort_filter(results, "max")
        assert len(results[0].scores) == 1
        assert results[0].scores[0].model == "model1"

    def test_filter_low(self):
        results = [
            SourceResult(
                source="artificial-analysis",
                scores=[
                    ModelScore(model="model1", source_model_name="Model (max)"),
                    ModelScore(model="model2", source_model_name="Model (low)"),
                    ModelScore(model="model3", source_model_name="Model"),
                ],
            )
        ]
        apply_aa_effort_filter(results, "low")
        assert len(results[0].scores) == 1
        assert results[0].scores[0].model == "model2"

    def test_ignore_other_sources(self):
        results = [
            SourceResult(
                source="other-source",
                scores=[
                    ModelScore(model="model1", source_model_name="Model (max)"),
                    ModelScore(model="model2", source_model_name="Model (low)"),
                ],
            )
        ]
        apply_aa_effort_filter(results, "max")
        assert len(results[0].scores) == 2


class TestCache:
    def test_get_returns_none_when_not_exists(self):
        with patch("metabolon.organelles.statolith.CACHE_DIR", Path("/nonexistent")):
            cache = Cache()
            assert cache.get("source") is None

    def test_get_returns_cached_when_valid(self, tmp_path):
        now = datetime.now(UTC)
        cache = Cache()
        cache.dir = tmp_path

        entry = {
            "fetched_at": now.isoformat(),
            "ttl_hours": 24,
            "data": {"key": "value"},
        }
        (tmp_path / "test.json").write_text(json.dumps(entry))

        result = cache.get("test")
        assert result is not None
        assert result[1] == {"key": "value"}

    def test_get_returns_none_when_expired(self, tmp_path):
        expired = datetime.now(UTC) - timedelta(hours=48)
        cache = Cache()
        cache.dir = tmp_path

        entry = {
            "fetched_at": expired.isoformat(),
            "ttl_hours": 24,
            "data": {"key": "value"},
        }
        (tmp_path / "test.json").write_text(json.dumps(entry))

        result = cache.get("test")
        assert result is None

    def test_set_caches_data(self, tmp_path):
        cache = Cache()
        cache.dir = tmp_path

        cache.set("test", {"key": "value"})

        assert (tmp_path / "test.json").exists()
        data = json.loads((tmp_path / "test.json").read_text())
        assert data["data"] == {"key": "value"}
        assert "fetched_at" in data

    def test_clear_removes_all_json(self, tmp_path):
        cache = Cache()
        cache.dir = tmp_path
        (tmp_path / "test1.json").write_text("{}")
        (tmp_path / "test2.json").write_text("{}")
        (tmp_path / "test.txt").write_text("")

        cache.clear()

        assert not (tmp_path / "test1.json").exists()
        assert not (tmp_path / "test2.json").exists()
        assert (tmp_path / "test.txt").exists()


class TestAliasMap:
    def test_load_alias_toml_parses_correctly(self):
        toml_str = """
[gpt-4]
canonical = "gpt-4o"
aliases = ["gpt4", "gpt-4"]

[claude-3]
canonical = "claude-3-5-sonnet"
aliases = ["claude", "sonnet"]
"""
        to_canonical: dict[str, str] = {}
        _load_alias_toml(toml_str, to_canonical)

        assert to_canonical["gpt-4o"] == "gpt-4o"
        assert to_canonical["gpt4"] == "gpt-4o"
        assert to_canonical["gpt-4"] == "gpt-4o"
        assert to_canonical["claude-3-5-sonnet"] == "claude-3-5-sonnet"
        assert to_canonical["claude"] == "claude-3-5-sonnet"

    def test_load_alias_toml_handles_bad_toml(self):
        toml_str = "bad toml [[["
        to_canonical: dict[str, str] = {}
        _load_alias_toml(toml_str, to_canonical)
        assert to_canonical == {}

    def test_resolve_exact_match(self):
        alias_map = AliasMap(_map={
            "gpt-4o": "gpt-4o",
            "gpt4": "gpt-4o",
        })
        assert alias_map.resolve("gpt4") == "gpt-4o"
        assert alias_map.resolve("GPT4") == "gpt-4o"

    def test_resolve_prefix_match(self):
        alias_map = AliasMap(_map={
            "gpt-4o": "gpt-4o",
        })
        assert alias_map.resolve("GPT-4o (latest)") == "gpt-4o"
        assert alias_map.resolve("gpt-4o-123k") == "gpt-4o"

    def test_resolve_returns_original_when_no_match(self):
        alias_map = AliasMap(_map={})
        assert alias_map.resolve("unknown-model") == "unknown-model"

    def test_matches(self):
        alias_map = AliasMap(_map={
            "gpt-4o": "gpt-4o",
            "gpt4": "gpt-4o",
        })
        assert alias_map.matches("gpt4", "gpt-4o") is True
        assert alias_map.matches("unknown", "gpt-4o") is False


class TestExtractCellValue:
    def test_extract_between_quotes(self):
        assert _extract_cell_value('- cell "1234"') == "1234"
        assert _extract_cell_value('row "model name"') == "model name"

    def test_return_none_when_no_quotes(self):
        assert _extract_cell_value("no quotes here") is None

    def test_return_none_when_only_one_quote(self):
        assert _extract_cell_value('cell "only one') is None


class TestIsImageOrVideoModel:
    def test_recognizes_image_models(self):
        assert _is_image_or_video_model("flux-1-dev") is True
        assert _is_image_or_video_model("DALL-E 3") is True
        assert _is_image_or_video_model("midjourney v6") is True
        assert _is_image_or_video_model("stable-diffusion") is True
        assert _is_image_or_video_model("video generation") is True

    def test_returns_false_for_text_models(self):
        assert _is_image_or_video_model("gpt-4o") is False
        assert _is_image_or_video_model("claude-3-sonnet") is False
        assert _is_image_or_video_model("llama-3") is False


class TestParseScoredCached:
    def test_parses_correctly(self):
        data = {
            "scores": [
                {"source_model_name": "Model A", "elo_score": 1200},
                {"source_model_name": "Model B", "elo_score": 1100},
                {"source_model_name": "Model C", "elo_score": 1300},
            ]
        }
        result = _parse_scored_cached("arena", "elo_score", data, None, "ok")

        assert result.source == "arena"
        assert result.status == "ok"
        assert len(result.scores) == 3
        # Should be sorted descending
        assert result.scores[0].source_model_name == "Model C"
        assert result.scores[0].rank == 1
        assert result.scores[0].metrics["elo_score"] == 1300
        assert result.scores[2].rank == 3

    def test_skips_invalid_entries(self):
        data = {
            "scores": [
                {"source_model_name": "Model A"},  # no score
                {"source_model_name": "Model B", "elo_score": None},
                {},  # nothing
            ]
        }
        result = _parse_scored_cached("arena", "elo_score", data, None, "ok")
        assert len(result.scores) == 0


class TestParseArenaJsonResponse:
    def test_parses_correctly(self):
        data = {
            "2025-01": {
                "text": {
                    "overall": {
                        "gpt-4o": 1300,
                        "claude-3-5-sonnet": 1250,
                        "flux-1": 1000,  # image model, should be filtered out
                    }
                }
            }
        }
        result = _parse_arena_json_response(data)
        assert len(result) == 2
        names = {n for n, _ in result}
        assert "gpt-4o" in names
        assert "claude-3-5-sonnet" in names
        assert "flux-1" not in names

    def test_returns_empty_for_bad_data(self):
        assert _parse_arena_json_response({}) == []
        assert _parse_arena_json_response("not a dict") == []
        assert _parse_arena_json_response({"key": "value"}) == []


class TestParseSwebenchScores:
    def test_extracts_correctly(self):
        data = {
            "leaderboards": [
                {
                    "results": [
                        {"name": "Model A", "resolved": 0.35, "resolved_count": 35},
                        {"name": "Model B", "resolved": 0.42, "resolved_count": 42},
                    ]
                }
            ]
        }
        scores = _parse_swebench_scores(data)
        assert len(scores) == 2
        assert scores[0].source_model_name == "Model B"  # higher score first
        assert scores[0].rank == 1
        assert scores[0].metrics["resolved_rate"] == 0.42
        assert scores[0].metrics["resolved_count"] == 42

    def test_dedup_keeps_highest(self):
        data = {
            "leaderboards": [
                {"results": [
                    {"name": "Model A", "resolved": 0.30},
                    {"name": "Model A", "resolved": 0.35},
                    {"name": "Model A", "resolved": 0.25},
                ]}
            ]
        }
        scores = _parse_swebench_scores(data)
        assert len(scores) == 1
        assert scores[0].metrics["resolved_rate"] == 0.35

    def test_extract_swebench_returns_none_for_bad_entry(self):
        assert _extract_swebench_model_score({}) is None
        assert _extract_swebench_model_score({"name": "test"}) is not None


class TestParseAiderScores:
    def test_parses_correctly(self):
        data = [
            {"model": "Model A", "pass_rate_1": 65.5, "total_cost": 120.0},
            {"model": "Model B", "pass_rate_1": 72.3, "total_cost": 95.0},
            {"model": "Model C"},  # no pass rate - still added, just no metric
        ]
        scores = _parse_aider_scores(data)
        # Model C is still added, it just has an empty metrics dict
        assert len(scores) == 3
        # sorted by pass_rate descending
        assert scores[0].source_model_name == "Model B"
        assert scores[0].metrics["pass_rate_1"] == 72.3
        assert scores[0].rank == 1
        assert scores[2].source_model_name == "Model C"


class TestMathHelpers:
    def test_get_float(self):
        assert _get_float({"a": 1.5}, "a") == 1.5
        assert _get_float({"a": 1}, "a") == 1.0
        assert _get_float({}, "a") == 0.0

    def test_get_int(self):
        assert _get_int({"a": 5}, "a") == 5
        assert _get_int({"a": 5.9}, "a") == 5
        assert _get_int({}, "a") == 0

    def test_percentile(self):
        # formula: (total - rank) / (total - 1)
        assert _percentile(1, 10) == (10 - 1) / (10 - 1) == 1.0
        assert _percentile(5, 10) == pytest.approx((10 - 5) / 9, rel=1e-2)  # 5/9 ≈ 0.5555
        assert _percentile(1, 1) == 1.0

    def test_std_dev(self):
        values = [1.0, 2.0, 3.0]
        mean = 2.0
        variance = ((1-2)**2 + (2-2)**2 + (3-2)**2)/3
        variance = (1 + 0 + 1)/3
        std = math.sqrt(2/3)
        assert _std_dev(values) == pytest.approx(std)
        assert _std_dev([5.0]) == 0.0


class TestAggregateResults:
    def test_aggregates_correctly(self):
        results = [
            SourceResult(
                source="source1",
                scores=[
                    ModelScore(model="a", source_model_name="A", rank=1, metrics={}),
                    ModelScore(model="b", source_model_name="B", rank=2, metrics={}),
                    ModelScore(model="c", source_model_name="C", rank=3, metrics={}),
                ],
            ),
            SourceResult(
                source="source2",
                scores=[
                    ModelScore(model="a", source_model_name="A", rank=2, metrics={}),
                    ModelScore(model="b", source_model_name="B", rank=1, metrics={}),
                ],
            ),
        ]
        agg_result, excluded = aggregate_results(results, min_sources=2, show_excluded=True)

        assert len(agg_result.scores) == 2  # a and b have 2 sources
        assert len(excluded) == 1  # c has only 1
        assert agg_result.scores[0].model in ("a", "b")  # whichever has higher avg percentile

        # Check that c is excluded
        assert any(model == "c" for model, count in excluded)

    def test_returns_empty_when_few_sources(self):
        results = [
            SourceResult(
                source="source1",
                scores=[ModelScore(model="a", source_model_name="A", rank=1, metrics={})],
            )
        ]
        agg_result, excluded = aggregate_results(results, min_sources=2, show_excluded=True)
        assert len(agg_result.scores) == 0
        assert len(excluded) == 1


class TestExtractMetric:
    def test_extracts_direct(self):
        score = ModelScore(
            model="test",
            source_model_name="Test",
            metrics={"resolved_rate": 0.35},
        )
        assert _extract_metric(score, "resolved_rate") == 0.35

    def test_calculates_total_cost(self):
        score = ModelScore(
            model="test",
            source_model_name="Test",
            metrics={"prompt_per_1m": 0.5, "completion_per_1m": 1.5},
        )
        assert _extract_metric(score, "total_cost") == 2.0


class TestCanonicalModelName:
    def test_returns_canonical_from_model(self):
        aliases = AliasMap(_map={"gpt-4o": "gpt-4o", "gpt4": "gpt-4o"})
        score = ModelScore(model="gpt4", source_model_name="GPT 4")
        assert _canonical_model_name(aliases, score) == "gpt-4o"

    def test_returns_canonical_from_source_when_model_has_no_alias(self):
        # Source has alias that maps to correct canonical, model doesn't have alias
        aliases = AliasMap(_map={"gpt-4o": "gpt-4o", "gpt-4": "gpt-4o"})
        score = ModelScore(model="gpt4", source_model_name="GPT-4")
        # model doesn't have alias in map → check source
        # source "GPT-4" maps to "gpt-4o", and "gpt-4o" != source.lower() which is "gpt-4"
        # so it should return the canonical from source
        assert _canonical_model_name(aliases, score) == "gpt-4o"


class TestRankModels:
    def test_ranks_correctly_descending(self):
        spec = {
            "sources": [
                {"source": "swebench", "label": "SWE-bench", "metric": "resolved_rate", "sort": "desc"},
            ]
        }
        results = [
            SourceResult(
                source="swebench",
                scores=[
                    ModelScore(model="model-a", source_model_name="Model A", metrics={"resolved_rate": 0.40}),
                    ModelScore(model="model-b", source_model_name="Model B", metrics={"resolved_rate": 0.50}),
                    ModelScore(model="model-c", source_model_name="Model C", metrics={"resolved_rate": 0.30}),
                ],
            )
        ]
        aliases = AliasMap(_map={})
        ranked = _rank_models(spec, results, aliases, top=10)

        assert len(ranked) == 3
        assert ranked[0]["model"] == "model-b"
        assert ranked[0]["rank"] == 1
        assert ranked[0]["metrics"]["swebench"] == 0.50
        assert ranked[2]["model"] == "model-c"

    def test_applies_aliases(self):
        spec = {
            "sources": [
                {"source": "swebench", "label": "SWE-bench", "metric": "resolved_rate", "sort": "desc"},
            ]
        }
        results = [
            SourceResult(
                source="swebench",
                scores=[
                    ModelScore(model="gpt4", source_model_name="GPT 4", metrics={"resolved_rate": 0.40}),
                    ModelScore(model="gpt-4o", source_model_name="GPT-4o", metrics={"resolved_rate": 0.50}),
                ],
            )
        ]
        aliases = AliasMap(_map={"gpt4": "gpt-4o", "gpt-4o": "gpt-4o"})
        ranked = _rank_models(spec, results, aliases, top=10)

        # Should be merged to one entry with the highest score
        assert len(ranked) == 1
        assert ranked[0]["model"] == "gpt-4o"


class TestMapCommandError:
    def test_returns_unavailable_for_file_not_found(self):
        exc = FileNotFoundError("test")
        result = _map_command_error("arena", "test", exc)
        assert result.status == "unavailable"

    def test_returns_error_otherwise(self):
        exc = RuntimeError("something went wrong")
        result = _map_command_error("arena", "test", exc)
        assert result.status.startswith("error:")


class TestParseArenaFromSnapshot:
    def test_parses_simple_snapshot(self):
        # Need to properly match the parsing logic conditions:
        # - Line starts with '- row "'
        # - First table found when contains "1503" or starts with '- row "1 '
        text = '''- row "1 1503 GPT-4o"
  - cell "1"
  - cell "Model"
  - cell "Overall"
  - cell "1250.5"
  - link "GPT-4o"
- row "2 1503 Claude-3-5-Sonnet"
  - cell "2"
  - cell "Model"
  - cell "Overall"
  - cell "1230.0"
  - link "Claude-3-5-Sonnet"
'''
        result = _parse_arena_from_snapshot(text)
        assert len(result) == 2
        models = {n for n, _ in result}
        assert "GPT-4o" in models
        assert "Claude-3-5-Sonnet" in models

    def test_filters_image_models(self):
        text = '''- row "1 1503"
  - cell "1"
  - cell "Model"
  - cell "Overall"
  - cell "1200"
  - link "DALL-E-3"
- row "2 1503"
  - cell "2"
  - cell "Model"
  - cell "Overall"
  - cell "1250"
  - link "GPT-4o"
'''
        result = _parse_arena_from_snapshot(text)
        assert len(result) == 1
        found = [n for n, _ in result]
        assert "GPT-4o" in found
        assert "DALL-E-3" not in found


# Integration test with mocks for external dependencies
class TestFetchersWithMocks:
    def test_fetch_arena_uses_cache_when_available(self):
        from metabolon.organelles.statolith import _fetch_arena

        mock_cache = Mock()
        mock_cache.get.return_value = (datetime.now(UTC), {
            "scores": [{"source_model_name": "Model A", "elo_score": 1200}]
        })
        mock_client = Mock()

        result = _fetch_arena(mock_cache, mock_client)

        assert result.status == "cached"
        assert len(result.scores) == 1
        mock_cache.get.assert_called_once()

    def test_fetch_swebench_uses_cache_when_available(self):
        from metabolon.organelles.statolith import _fetch_swebench

        mock_cache = Mock()
        mock_cache.get.return_value = (datetime.now(UTC), {
            "leaderboards": [{"results": [{"name": "Model A", "resolved": 0.35}]}]
        })
        mock_client = Mock()

        result = _fetch_swebench(mock_cache, mock_client)

        assert result.status == "cached"
        assert len(result.scores) == 1

    def test_fetch_aider_uses_cache_when_available(self):
        from metabolon.organelles.statolith import _fetch_aider

        mock_cache = Mock()
        mock_cache.get.return_value = (datetime.now(UTC), [
            {"model": "Model A", "pass_rate_1": 65.0}
        ])
        mock_client = Mock()

        result = _fetch_aider(mock_cache, mock_client)

        assert result.status == "cached"
        assert len(result.scores) == 1

    def test_fetch_openrouter_handles_error(self):
        from metabolon.organelles.statolith import _fetch_openrouter

        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_client = Mock()
        mock_client.get.side_effect = httpx.TransportError("network error")

        result = _fetch_openrouter(mock_cache, mock_client)

        assert result.status.startswith("error:")
