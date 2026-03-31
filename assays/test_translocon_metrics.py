"""Tests for translocon_metrics — record, stats, formatting."""

from __future__ import annotations

import json
import math
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.translocon_metrics import (
    METRICS_PATH,
    format_report,
    record,
    stats_by_backend,
)


@pytest.fixture(autouse=True)
def tmp_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect METRICS_PATH to a temp file for every test."""
    fake = tmp_path / "metrics.jsonl"
    monkeypatch.setattr("metabolon.organelles.translocon_metrics.METRICS_PATH", fake)
    return fake


def _entry(backend: str = "goose", duration: float = 10.0, success: bool = True,
           model: str = "GLM-4.7", prompt_length: int = 500, output_length: int = 200,
           mode: str = "explore") -> dict:
    return {
        "backend": backend,
        "model": model,
        "prompt_length": prompt_length,
        "output_length": output_length,
        "duration_s": duration,
        "success": success,
        "mode": mode,
    }


class TestRecord:
    def test_record_appends_entry(self, tmp_metrics: Path) -> None:
        record(**_entry())
        assert tmp_metrics.exists()
        lines = tmp_metrics.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["backend"] == "goose"
        assert entry["model"] == "GLM-4.7"
        assert entry["prompt_length"] == 500
        assert entry["output_length"] == 200
        assert entry["duration_s"] == 10.0
        assert entry["success"] is True
        assert "timestamp" in entry

    def test_record_multiple_entries(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=5.0))
        record(**_entry(backend="droid", duration=15.0, success=False))
        record(**_entry(backend="direct", duration=3.0))
        lines = tmp_metrics.read_text().strip().splitlines()
        assert len(lines) == 3
        backends = [json.loads(line)["backend"] for line in lines]
        assert backends == ["goose", "droid", "direct"]


class TestStatsByBackend:
    def test_empty_returns_empty(self) -> None:
        assert stats_by_backend() == {}

    def test_single_backend_stats(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=10.0))
        record(**_entry(backend="goose", duration=20.0))
        record(**_entry(backend="goose", duration=30.0, success=False))
        result = stats_by_backend()
        assert "goose" in result
        stats = result["goose"]
        assert stats["count"] == 3
        assert stats["success_count"] == 2
        assert stats["avg_duration"] == 20.0
        assert stats["p50_duration"] == 20.0

    def test_multiple_backends_grouped(self, tmp_metrics: Path) -> None:
        for dur in [5, 10, 15]:
            record(**_entry(backend="goose", duration=float(dur)))
        for dur in [20, 40]:
            record(**_entry(backend="droid", duration=float(dur)))
        result = stats_by_backend()
        assert set(result.keys()) == {"droid", "goose"}
        assert result["goose"]["count"] == 3
        assert result["droid"]["count"] == 2
        assert result["droid"]["avg_duration"] == 30.0


class TestFormatReport:
    def test_empty_report(self) -> None:
        report = format_report()
        assert "No translocon metrics recorded" in report

    def test_report_includes_backends(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=10.0))
        record(**_entry(backend="droid", duration=25.0, success=False))
        report = format_report()
        assert "goose:" in report
        assert "droid:" in report
        assert "Avg duration" in report
        assert "P50" in report
        assert "P95" in report


    def test_format_report_includes_summary(self, tmp_metrics: Path) -> None:
        """format_report output includes a Summary section."""
        record(**_entry(backend="goose", duration=50.0, success=True))
        record(**_entry(backend="goose", duration=30.0, success=False))
        report = format_report()
        assert "Summary" in report
        assert "Success rate" in report
        assert "Total dispatches: 2" in report
        assert "50%" in report
        assert "Primary backend: goose" in report


class TestPercentileEdgeCases:
    def test_p95_single_value(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=42.0))
        result = stats_by_backend()
        assert result["goose"]["p95_duration"] == 42.0

    def test_p95_two_values(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=10.0))
        record(**_entry(backend="goose", duration=20.0))
        result = stats_by_backend()
        p95 = result["goose"]["p95_duration"]
        assert 10.0 <= p95 <= 20.0
