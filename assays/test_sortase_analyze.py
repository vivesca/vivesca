"""Tests for sortase analyze command — log analysis subcommand."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from metabolon.sortase.cli import main
from metabolon.sortase.logger import analyze_logs


def _make_entry(
    timestamp: str = "2026-03-30T12:00:00",
    tool: str = "droid",
    success: bool = True,
    failure_reason: str | None = None,
    duration_s: float = 100.0,
    tasks: int = 1,
    files_changed: int = 2,
    plan: str = "test-plan.md",
) -> dict:
    return {
        "timestamp": timestamp,
        "tool": tool,
        "success": success,
        "failure_reason": failure_reason,
        "duration_s": duration_s,
        "tasks": tasks,
        "files_changed": files_changed,
        "plan": plan,
        "project": "test",
        "fallbacks": [],
        "tests_passed": 1 if success else 0,
    }


class TestAnalyzeLogs:
    """Unit tests for analyze_logs function."""

    def test_success_rate_by_backend(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [
            _make_entry(tool="droid", success=True),
            _make_entry(tool="droid", success=True),
            _make_entry(tool="droid", success=False, failure_reason="tests"),
            _make_entry(tool="gemini", success=True),
            _make_entry(tool="gemini", success=False, failure_reason="placeholder-scan"),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        result = analyze_logs(log_file)
        assert result["success_rate_by_backend"]["droid"] == round(2 / 3, 3)
        assert result["success_rate_by_backend"]["gemini"] == 0.5

    def test_success_rate_by_hour(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        # 2 successes at hour 8, 1 failure at hour 8, 1 success at hour 14
        entries = [
            _make_entry(timestamp="2026-03-30T08:10:00", success=True),
            _make_entry(timestamp="2026-03-30T08:30:00", success=True),
            _make_entry(timestamp="2026-03-30T08:45:00", success=False, failure_reason="tests"),
            _make_entry(timestamp="2026-03-30T14:00:00", success=True),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        result = analyze_logs(log_file)
        assert result["success_rate_by_hour"]["08"] == round(2 / 3, 3)
        assert result["success_rate_by_hour"]["14"] == 1.0

    def test_avg_duration_by_plan_complexity(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [
            _make_entry(files_changed=1, duration_s=50.0),
            _make_entry(files_changed=1, duration_s=70.0),
            _make_entry(files_changed=3, duration_s=200.0),
            _make_entry(files_changed=3, duration_s=300.0),
            _make_entry(files_changed=3, duration_s=250.0),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        result = analyze_logs(log_file)
        assert result["avg_duration_by_plan_complexity"][1] == 60.0
        assert result["avg_duration_by_plan_complexity"][3] == 250.0

    def test_common_failure_reasons(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [
            _make_entry(success=False, failure_reason="tests"),
            _make_entry(success=False, failure_reason="tests"),
            _make_entry(success=False, failure_reason="placeholder-scan"),
            _make_entry(success=True),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        result = analyze_logs(log_file)
        assert result["failure_reasons"]["tests"] == 2
        assert result["failure_reasons"]["placeholder-scan"] == 1

    def test_coaching_coverage_uses_relevant_note_timing(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        coaching_file = tmp_path / "coaching.md"
        coaching_file.write_text(
            "\n".join(
                [
                    "<!-- auto-detected 2026-03-29 09:00 -->",
                    "### Verification discipline",
                    "- Always run pytest before claiming done.",
                    "",
                    "<!-- auto-detected 2026-03-30 11:00 -->",
                    "### Placeholder cleanup",
                    "- Remove TODO, FIXME, and stub markers before finishing.",
                ]
            )
            + "\n"
        )

        entries = [
            _make_entry(timestamp="2026-03-30T12:00:00", success=False, failure_reason="tests"),
            _make_entry(timestamp="2026-03-30T13:00:00", success=False, failure_reason="placeholder-scan"),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        result = analyze_logs(log_file, coaching_path=coaching_file)
        assert result["coaching_coverage"] == 1.0
        assert result["coaching_gap"] == 0.0

    def test_coaching_coverage_mixed(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        coaching_file = tmp_path / "coaching.md"
        coaching_file.write_text(
            "\n".join(
                [
                    "<!-- auto-detected 2026-03-30 12:00 -->",
                    "### Verification discipline",
                    "- Pytest failures mean the work is not done.",
                    "",
                    "<!-- auto-detected 2026-03-30 15:00 -->",
                    "### Placeholder cleanup",
                    "- Never leave TODO or stub markers.",
                ]
            )
            + "\n"
        )

        entries = [
            _make_entry(timestamp="2026-03-30T10:00:00", success=False, failure_reason="tests"),
            _make_entry(timestamp="2026-03-30T14:00:00", success=False, failure_reason="placeholder-scan"),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        result = analyze_logs(log_file, coaching_path=coaching_file)
        assert result["coaching_coverage"] == 0.0
        assert result["coaching_gap"] == 1.0

    def test_coaching_coverage_ignores_irrelevant_notes(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        coaching_file = tmp_path / "coaching.md"
        coaching_file.write_text(
            "\n".join(
                [
                    "<!-- auto-detected 2026-03-29 08:00 -->",
                    "### Verification discipline",
                    "- Run pytest before claiming success.",
                ]
            )
            + "\n"
        )

        entries = [_make_entry(timestamp="2026-03-30T14:00:00", success=False, failure_reason="placeholder-scan")]
        log_file.write_text(json.dumps(entries[0]) + "\n")
        result = analyze_logs(log_file, coaching_path=coaching_file)
        assert result["coaching_coverage"] == 0.0
        assert result["coaching_gap"] == 1.0

    def test_coaching_coverage_no_failures(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [_make_entry(success=True)]
        log_file.write_text(json.dumps(entries[0]) + "\n")
        result = analyze_logs(log_file)
        assert result["coaching_coverage"] is None
        assert result["coaching_gap"] is None

    def test_coaching_coverage_no_coaching_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [_make_entry(success=False, failure_reason="tests")]
        log_file.write_text(json.dumps(entries[0]) + "\n")
        nonexistent = tmp_path / "no_such_file.md"
        result = analyze_logs(log_file, coaching_path=nonexistent)
        assert result["coaching_coverage"] == 0.0
        assert result["coaching_gap"] == 1.0

    def test_empty_log(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        log_file.write_text("")
        result = analyze_logs(log_file)
        assert result["success_rate_by_backend"] == {}
        assert result["success_rate_by_hour"] == {}
        assert result["avg_duration_by_plan_complexity"] == {}
        assert result["failure_reasons"] == {}
        assert result["coaching_coverage"] is None
        assert result["coaching_gap"] is None
        assert result["total_entries"] == 0


class TestAnalyzeCommand:
    """CLI integration tests for `sortase analyze`."""

    def test_analyze_basic_output(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [
            _make_entry(tool="droid", success=True, duration_s=100.0),
            _make_entry(tool="droid", success=False, failure_reason="tests", duration_s=50.0),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        coaching_file = tmp_path / "coaching.md"
        coaching_file.write_text("### Verification discipline\n- Run pytest before claiming done.\n")

        runner = CliRunner()
        with patch("metabolon.sortase.logger.DEFAULT_LOG_PATH", log_file):
            result = runner.invoke(main, ["analyze", "--log", str(log_file), "--coaching", str(coaching_file)])
        assert result.exit_code == 0
        assert "droid" in result.output
        assert "file count" in result.output
        assert "coverage gap" in result.output.lower()

    def test_analyze_json_output(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        entries = [
            _make_entry(tool="droid", success=True),
            _make_entry(tool="gemini", success=False, failure_reason="tests"),
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--log", str(log_file), "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "avg_duration_by_plan_complexity" in parsed
        assert "success_rate_by_backend" in parsed
        assert parsed["success_rate_by_backend"]["droid"] == 1.0
        assert parsed["success_rate_by_backend"]["gemini"] == 0.0

    def test_analyze_empty_log(self, tmp_path: Path) -> None:
        log_file = tmp_path / "log.jsonl"
        log_file.write_text("")
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--log", str(log_file)])
        assert result.exit_code == 0
        assert "No log entries" in result.output
