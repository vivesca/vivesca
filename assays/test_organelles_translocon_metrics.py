from __future__ import annotations

"""Tests for metabolon.organelles.translocon_metrics — record, load, percentile,
stats_by_backend, and format_report with emphasis on edge cases."""


import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.translocon_metrics import (
    _load_entries,
    _percentile,
    format_report,
    record,
    stats_by_backend,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def tmp_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect METRICS_PATH to a temp file for every test."""
    fake = tmp_path / "metrics.jsonl"
    monkeypatch.setattr(
        "metabolon.organelles.translocon_metrics.METRICS_PATH", fake
    )
    return fake


def _entry(
    backend: str = "goose",
    duration: float = 10.0,
    success: bool = True,
    model: str = "GLM-4.7",
    prompt_length: int = 500,
    output_length: int = 200,
    mode: str = "explore",
) -> dict:
    return {
        "backend": backend,
        "model": model,
        "prompt_length": prompt_length,
        "output_length": output_length,
        "duration_s": duration,
        "success": success,
        "mode": mode,
    }


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_creates_parent_directory(self, tmp_path: Path, monkeypatch) -> None:
        """record() should mkdir -p the parent of METRICS_PATH."""
        deep = tmp_path / "a" / "b" / "c" / "metrics.jsonl"
        monkeypatch.setattr(
            "metabolon.organelles.translocon_metrics.METRICS_PATH", deep
        )
        record(**_entry())
        assert deep.exists()
        assert deep.parent.is_dir()

    def test_duration_rounded_to_3_decimals(self, tmp_metrics: Path) -> None:
        record(**_entry(duration=1.23456))
        entry = json.loads(tmp_metrics.read_text().strip())
        assert entry["duration_s"] == 1.235

    def test_default_mode_is_empty_string(self, tmp_metrics: Path) -> None:
        record(backend="x", model="m", prompt_length=1, output_length=1,
               duration_s=1.0, success=True)
        entry = json.loads(tmp_metrics.read_text().strip())
        assert entry["mode"] == ""

    def test_timestamp_is_isoformat(self, tmp_metrics: Path) -> None:
        record(**_entry())
        entry = json.loads(tmp_metrics.read_text().strip())
        ts = entry["timestamp"]
        # Should parse without error
        from datetime import datetime
        datetime.fromisoformat(ts)

    def test_append_does_not_overwrite(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="first"))
        record(**_entry(backend="second"))
        lines = tmp_metrics.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["backend"] == "first"
        assert json.loads(lines[1])["backend"] == "second"


# ---------------------------------------------------------------------------
# _load_entries()
# ---------------------------------------------------------------------------


class TestLoadEntries:
    def test_missing_file_returns_empty(self, tmp_path: Path, monkeypatch) -> None:
        gone = tmp_path / "nonexistent.jsonl"
        monkeypatch.setattr(
            "metabolon.organelles.translocon_metrics.METRICS_PATH", gone
        )
        assert _load_entries() == []

    def test_skips_blank_lines(self, tmp_metrics: Path) -> None:
        record(**_entry())
        # Manually append blank lines
        tmp_metrics.write_text(tmp_metrics.read_text() + "\n\n\n")
        assert len(_load_entries()) == 1

    def test_skips_malformed_json(self, tmp_metrics: Path) -> None:
        tmp_metrics.write_text("not json\n")
        assert _load_entries() == []

    def test_mix_valid_and_invalid(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="good"))
        tmp_metrics.write_text(tmp_metrics.read_text() + "bad\n")
        record(**_entry(backend="also-good"))
        entries = _load_entries()
        assert len(entries) == 2
        assert entries[0]["backend"] == "good"
        assert entries[1]["backend"] == "also-good"

    def test_days_filter_excludes_old_entries(
        self, tmp_metrics: Path
    ) -> None:
        """Inject an entry with an old timestamp; days=1 should exclude it."""
        from datetime import datetime

        old_entry = {
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat(
                timespec="seconds"
            ),
            "backend": "old",
            "model": "m",
            "prompt_length": 1,
            "output_length": 1,
            "duration_s": 5.0,
            "success": True,
        }
        tmp_metrics.write_text(json.dumps(old_entry) + "\n")
        record(**_entry(backend="fresh"))

        entries = _load_entries(days=1)
        backends = [e["backend"] for e in entries]
        assert "fresh" in backends
        assert "old" not in backends

    def test_days_none_includes_all(self, tmp_metrics: Path) -> None:
        from datetime import datetime

        old_entry = {
            "timestamp": (datetime.now() - timedelta(days=365)).isoformat(
                timespec="seconds"
            ),
            "backend": "ancient",
            "model": "m",
            "prompt_length": 1,
            "output_length": 1,
            "duration_s": 1.0,
            "success": True,
        }
        tmp_metrics.write_text(json.dumps(old_entry) + "\n")
        record(**_entry(backend="fresh"))
        entries = _load_entries(days=None)
        assert len(entries) == 2

    def test_unparseable_timestamp_included_even_with_filter(
        self, tmp_metrics: Path
    ) -> None:
        """Entries with bad timestamps are kept (not excluded by day filter)."""
        tmp_metrics.write_text(
            json.dumps({"timestamp": "not-a-date", "backend": "x"}) + "\n"
        )
        entries = _load_entries(days=1)
        assert len(entries) == 1


# ---------------------------------------------------------------------------
# _percentile()
# ---------------------------------------------------------------------------


class TestPercentile:
    def test_empty_returns_zero(self) -> None:
        assert _percentile([], 50) == 0.0

    def test_single_value_any_percentile(self) -> None:
        assert _percentile([42.0], 0) == 42.0
        assert _percentile([42.0], 50) == 42.0
        assert _percentile([42.0], 100) == 42.0

    def test_two_values_p50_interpolates(self) -> None:
        result = _percentile([10.0, 20.0], 50)
        assert result == 15.0

    def test_three_values_p50(self) -> None:
        result = _percentile([10.0, 20.0, 30.0], 50)
        assert result == 20.0

    def test_p0_returns_min(self) -> None:
        vals = [5.0, 10.0, 15.0, 20.0]
        assert _percentile(vals, 0) == 5.0

    def test_p100_returns_max(self) -> None:
        vals = [5.0, 10.0, 15.0, 20.0]
        assert _percentile(vals, 100) == 20.0

    def test_p95_interpolation(self) -> None:
        # 21 values: 0..20, p95 index = 0.95*20 = 19
        vals = [float(i) for i in range(21)]
        result = _percentile(vals, 95)
        assert result == 19.0

    def test_result_is_rounded_to_2_decimals(self) -> None:
        # 3 values: [1.0, 2.0, 3.0], p33 index = 0.33*2 = 0.66
        # lower=0, upper=1, frac=0.66 => 1.0 + 0.66*1.0 = 1.66
        result = _percentile([1.0, 2.0, 3.0], 33)
        # round(1.66, 2) == 1.66
        assert result == 1.66


# ---------------------------------------------------------------------------
# stats_by_backend()
# ---------------------------------------------------------------------------


class TestStatsByBackend:
    def test_empty_file(self) -> None:
        assert stats_by_backend() == {}

    def test_single_entry(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=10.0))
        result = stats_by_backend()
        assert result["goose"]["count"] == 1
        assert result["goose"]["success_count"] == 1
        assert result["goose"]["avg_duration"] == 10.0

    def test_failure_count(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", success=False))
        result = stats_by_backend()
        assert result["goose"]["success_count"] == 0

    def test_entries_with_missing_duration(self, tmp_metrics: Path) -> None:
        """Entry missing duration_s should be treated as 0."""
        tmp_metrics.write_text(
            json.dumps({"backend": "goose", "success": True}) + "\n"
        )
        result = stats_by_backend()
        assert result["goose"]["avg_duration"] == 0.0
        assert result["goose"]["p50_duration"] == 0.0

    def test_backends_sorted_alphabetically(self, tmp_metrics: Path) -> None:
        for name in ["zeta", "alpha", "mu"]:
            record(**_entry(backend=name, duration=1.0))
        result = stats_by_backend()
        assert list(result.keys()) == ["alpha", "mu", "zeta"]

    def test_days_filter_passed_through(self, tmp_metrics: Path) -> None:
        from datetime import datetime

        old = {
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat(
                timespec="seconds"
            ),
            "backend": "old",
            "model": "m",
            "prompt_length": 1,
            "output_length": 1,
            "duration_s": 99.0,
            "success": True,
        }
        tmp_metrics.write_text(json.dumps(old) + "\n")
        record(**_entry(backend="fresh", duration=5.0))

        result = stats_by_backend(days=1)
        assert "fresh" in result
        assert "old" not in result


# ---------------------------------------------------------------------------
# format_report()
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_empty_all_time(self) -> None:
        report = format_report()
        assert "No translocon metrics recorded (all time)." == report

    def test_empty_with_days(self) -> None:
        report = format_report(days=7)
        assert "last 7 days" in report

    def test_report_contains_backend_block(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=10.0, success=True))
        report = format_report()
        assert "goose:" in report
        assert "Dispatches:" in report

    def test_success_percentage_calculation(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=1.0, success=True))
        record(**_entry(backend="goose", duration=1.0, success=False))
        report = format_report()
        assert "50%" in report

    def test_summary_section_present(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=10.0))
        report = format_report()
        assert "Summary:" in report
        assert "Total dispatches: 1" in report
        assert "Primary backend: goose" in report

    def test_report_with_days_header(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=1.0))
        report = format_report(days=3)
        assert "last 3 days" in report

    def test_all_failures_shows_0_percent(self, tmp_metrics: Path) -> None:
        record(**_entry(backend="goose", duration=1.0, success=False))
        record(**_entry(backend="goose", duration=2.0, success=False))
        report = format_report()
        assert "0%" in report

    def test_multiple_backends_primary_backend(self, tmp_metrics: Path) -> None:
        for _ in range(5):
            record(**_entry(backend="alpha", duration=1.0))
        for _ in range(2):
            record(**_entry(backend="beta", duration=1.0))
        report = format_report()
        assert "Primary backend: alpha (5 dispatches)" in report
