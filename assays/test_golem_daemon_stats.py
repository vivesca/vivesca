from __future__ import annotations

"""Tests for golem-daemon cmd_stats — pass/fail/retry counts, avg duration by provider."""

import json
import textwrap
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_module(tmp_jsonl: Path, tmp_queue: Path) -> dict:
    """Load golem-daemon with JSONLFILE and QUEUE_FILE overridden."""
    source = Path(str(Path.home() / "germline/effectors/golem-daemon")).read_text()
    ns: dict = {"__name__": "golem_daemon"}
    exec(source, ns)
    # Patch module-level path constants
    ns["JSONLFILE"] = tmp_jsonl
    ns["QUEUE_FILE"] = tmp_queue
    return ns


def _write_jsonl(path: Path, records: list[dict]):
    """Append JSONL records to a file."""
    with open(path, "a") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _make_record(
    task_id: str = "t-abc123",
    provider: str = "zhipu",
    exit_code: int = 0,
    duration: int = 120,
    ts: str = "2026-04-01 10:00:00",
    cmd: str = "golem test",
    tail: str = "",
) -> dict:
    return {
        "ts": ts,
        "task_id": task_id,
        "provider": provider,
        "exit": exit_code,
        "duration": duration,
        "cmd": cmd,
        "tail": tail,
    }


def _run_stats(mod: dict) -> tuple[str, int]:
    """Run cmd_stats with captured stdout. Returns (output, returncode)."""
    buf = StringIO()
    with patch("sys.stdout", buf):
        rc = mod["cmd_stats"]()
    return buf.getvalue(), rc


# ── no history ────────────────────────────────────────────


class TestNoHistory:
    def test_no_jsonl_file(self, tmp_path: Path):
        mod = _load_module(tmp_path / "golem.jsonl", tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "No task history found" in out

    def test_empty_jsonl_file(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        jsonl.write_text("")
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "No task history found" in out


# ── overall counts ────────────────────────────────────────


class TestOverallCounts:
    def test_all_passed(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(exit_code=0), _make_record(exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 2 (passed: 2, failed: 0)" in out

    def test_all_failed(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(exit_code=1), _make_record(exit_code=2)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 2 (passed: 0, failed: 2)" in out

    def test_mixed(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [
            _make_record(exit_code=0),
            _make_record(exit_code=1),
            _make_record(exit_code=0),
        ])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 3 (passed: 2, failed: 1)" in out


# ── permanently failed (retries exhausted) ────────────────


class TestPermanentlyFailed:
    def test_retries_from_queue(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "queue.md"
        _write_jsonl(jsonl, [_make_record(exit_code=1)])
        queue.write_text("- [!] `golem test`\n## Done\n")
        mod = _load_module(jsonl, queue)
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 1" in out

    def test_no_permanently_failed(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "queue.md"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        queue.write_text("- [ ] `golem test`\n## Done\n")
        mod = _load_module(jsonl, queue)
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 0" in out

    def test_no_queue_file(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "nonexistent_queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 0" in out

    def test_multiple_permanently_failed(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "queue.md"
        _write_jsonl(jsonl, [_make_record(exit_code=1)])
        queue.write_text("- [!] `golem a`\n- [!] `golem b`\n- [!] `golem c`\n## Done\n")
        mod = _load_module(jsonl, queue)
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 3" in out


# ── today filter ──────────────────────────────────────────


class TestTodayFilter:
    def test_today_tasks(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        today_str = "2026-04-01"
        _write_jsonl(jsonl, [
            _make_record(exit_code=0, ts=f"{today_str} 09:00:00"),
            _make_record(exit_code=1, ts=f"{today_str} 10:00:00"),
            _make_record(exit_code=0, ts="2026-03-31 10:00:00"),
        ])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert f"Tasks today ({today_str}): 2 (passed: 1, failed: 1)" in out

    def test_no_today_tasks(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(ts="2025-12-25 10:00:00")])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        # Should show 0 tasks for today
        assert "Tasks today" in out
        assert "(passed: 0, failed: 0)" in out


# ── provider stats ────────────────────────────────────────


class TestProviderStats:
    def test_single_provider_avg_duration(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [
            _make_record(provider="zhipu", duration=60, exit_code=0),
            _make_record(provider="zhipu", duration=120, exit_code=1),
        ])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "zhipu" in out
        assert "2 tasks" in out
        assert "1 passed" in out
        assert "1 failed" in out
        # avg = (60+120)/2 = 90s = 1m30s
        assert "1m30s" in out

    def test_multiple_providers(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [
            _make_record(provider="zhipu", duration=60, exit_code=0),
            _make_record(provider="infini", duration=300, exit_code=0),
            _make_record(provider="volcano", duration=30, exit_code=1),
        ])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "zhipu" in out
        assert "infini" in out
        assert "volcano" in out
        # infini avg = 300s = 5m00s
        assert "5m00s" in out

    def test_zero_duration(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(provider="codex", duration=0, exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "0m00s" in out

    def test_provider_sorted_alphabetically(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [
            _make_record(provider="volcano", duration=60, exit_code=0),
            _make_record(provider="codex", duration=60, exit_code=0),
            _make_record(provider="gemini", duration=60, exit_code=0),
        ])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        lines = [l for l in out.splitlines() if l.strip().startswith("codex") or l.strip().startswith("gemini") or l.strip().startswith("volcano")]
        providers = [l.split()[0] for l in lines]
        assert providers == sorted(providers)


# ── rotated jsonl (.1 file) ───────────────────────────────


class TestRotatedJsonl:
    def test_reads_rotated_file(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        rotated = tmp_path / "golem.jsonl.1"
        _write_jsonl(rotated, [_make_record(exit_code=0, provider="zhipu")])
        _write_jsonl(jsonl, [_make_record(exit_code=1, provider="infini")])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 2 (passed: 1, failed: 1)" in out
        assert "zhipu" in out
        assert "infini" in out

    def test_only_rotated_file(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        rotated = tmp_path / "golem.jsonl.1"
        _write_jsonl(rotated, [_make_record(exit_code=0)])
        # jsonl itself does not exist
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 1" in out


# ── malformed lines ───────────────────────────────────────


class TestMalformedLines:
    def test_skips_bad_json(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        with open(jsonl, "a") as f:
            f.write("not json at all\n")
            f.write('{"broken\n')
        _write_jsonl(jsonl, [_make_record(exit_code=1)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 2 (passed: 1, failed: 1)" in out

    def test_empty_lines_skipped(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        with open(jsonl, "a") as f:
            f.write("\n\n")
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 1" in out


# ── return code ───────────────────────────────────────────


class TestReturnCode:
    def test_returns_zero_with_data(self, tmp_path: Path):
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record()])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        _, rc = _run_stats(mod)
        assert rc == 0

    def test_returns_zero_no_data(self, tmp_path: Path):
        mod = _load_module(tmp_path / "golem.jsonl", tmp_path / "queue.md")
        _, rc = _run_stats(mod)
        assert rc == 0


# ── missing fields in records ──────────────────────────────


class TestMissingFields:
    def test_missing_provider_defaults_unknown(self, tmp_path: Path):
        """Records without 'provider' key appear under 'unknown'."""
        jsonl = tmp_path / "golem.jsonl"
        rec = _make_record()
        del rec["provider"]
        _write_jsonl(jsonl, [rec])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "unknown" in out

    def test_missing_duration_defaults_zero(self, tmp_path: Path):
        """Records without 'duration' key default to 0."""
        jsonl = tmp_path / "golem.jsonl"
        rec = _make_record()
        del rec["duration"]
        _write_jsonl(jsonl, [rec])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "0m00s" in out

    def test_missing_exit_defaults_failed(self, tmp_path: Path):
        """Records without 'exit' key count as failed."""
        jsonl = tmp_path / "golem.jsonl"
        rec = _make_record()
        del rec["exit"]
        _write_jsonl(jsonl, [rec])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 1 (passed: 0, failed: 1)" in out

    def test_missing_ts_excluded_from_today(self, tmp_path: Path):
        """Records without 'ts' key are excluded from today count but included in total."""
        jsonl = tmp_path / "golem.jsonl"
        rec = _make_record(exit_code=0)
        del rec["ts"]
        _write_jsonl(jsonl, [rec])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 1 (passed: 1, failed: 0)" in out
        assert "(passed: 0, failed: 0)" in out  # today has 0


# ── large duration formatting ──────────────────────────────


class TestDurationFormatting:
    def test_hour_plus_duration(self, tmp_path: Path):
        """Duration over 60 minutes shows correct minutes."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(provider="zhipu", duration=3900, exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        # 3900s = 65m00s
        assert "65m00s" in out

    def test_exact_minute_duration(self, tmp_path: Path):
        """Duration that is exactly N minutes shows no extra seconds."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(provider="codex", duration=180, exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "3m00s" in out

    def test_single_second_duration(self, tmp_path: Path):
        """Duration of 1 second shows 0m01s."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(provider="gemini", duration=1, exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "0m01s" in out


# ── permanently failed edge cases ──────────────────────────


class TestPermanentlyFailedEdgeCases:
    def test_high_priority_not_counted_as_failed(self, tmp_path: Path):
        """[!!] tasks in queue are not counted as permanently failed."""
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "queue.md"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        queue.write_text("- [!!] `golem \"urgent pending\"\n## Done\n")
        mod = _load_module(jsonl, queue)
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 0" in out

    def test_mixed_failed_and_pending_in_queue(self, tmp_path: Path):
        """Only [!] lines count as permanently failed, not [ ] or [x]."""
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "queue.md"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        queue.write_text(
            "- [!] `golem \"perma fail\"`\n"
            "- [ ] `golem \"still pending\"`\n"
            "- [x] `golem \"done\"`\n"
            "## Done\n"
        )
        mod = _load_module(jsonl, queue)
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 1" in out

    def test_unreadable_queue_counts_zero(self, tmp_path: Path):
        """Unreadable queue file results in 0 permanently failed."""
        jsonl = tmp_path / "golem.jsonl"
        queue = tmp_path / "queue.md"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        queue.write_text("- [!] `golem \"failed\"`\n")
        queue.chmod(0o000)
        mod = _load_module(jsonl, queue)
        try:
            out, rc = _run_stats(mod)
        finally:
            queue.chmod(0o644)
        assert rc == 0
        assert "Permanently failed (retries exhausted): 0" in out


# ── unreadable JSONL ───────────────────────────────────────


class TestUnreadableJsonl:
    def test_unreadable_jsonl_file(self, tmp_path: Path):
        """cmd_stats handles unreadable JSONL file gracefully."""
        jsonl = tmp_path / "golem.jsonl"
        jsonl.write_text(json.dumps(_make_record()) + "\n")
        jsonl.chmod(0o000)
        mod = _load_module(jsonl, tmp_path / "queue.md")
        try:
            out, rc = _run_stats(mod)
        finally:
            jsonl.chmod(0o644)
        assert rc == 0
        assert "No task history found" in out

    def test_unreadable_rotated_jsonl(self, tmp_path: Path):
        """cmd_stats handles unreadable rotated JSONL file."""
        jsonl = tmp_path / "golem.jsonl"
        rotated = tmp_path / "golem.jsonl.1"
        rotated.write_text(json.dumps(_make_record()) + "\n")
        rotated.chmod(0o000)
        mod = _load_module(jsonl, tmp_path / "queue.md")
        try:
            out, rc = _run_stats(mod)
        finally:
            rotated.chmod(0o644)
        assert rc == 0
        assert "No task history found" in out


# ── main() dispatch ────────────────────────────────────────


class TestMainDispatch:
    def test_stats_command_dispatches(self, tmp_path: Path):
        """main() with 'stats' arg calls cmd_stats."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(exit_code=0)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        buf = StringIO()
        with patch("sys.argv", ["golem-daemon", "stats"]), patch("sys.stdout", buf):
            rc = mod["main"]()
        assert rc == 0
        assert "Total tasks: 1" in buf.getvalue()

    def test_unknown_command(self, tmp_path: Path):
        """main() with unknown command returns 1."""
        mod = _load_module(tmp_path / "golem.jsonl", tmp_path / "queue.md")
        buf = StringIO()
        with patch("sys.argv", ["golem-daemon", "bogus"]), patch("sys.stdout", buf):
            rc = mod["main"]()
        assert rc == 1
        assert "Unknown command: bogus" in buf.getvalue()


# ── single record ──────────────────────────────────────────


class TestSingleRecord:
    def test_single_pass(self, tmp_path: Path):
        """Single passing record shows correct stats."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(provider="infini", exit_code=0, duration=90)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 1 (passed: 1, failed: 0)" in out
        assert "infini" in out
        assert "1m30s" in out

    def test_single_fail(self, tmp_path: Path):
        """Single failing record shows correct stats."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record(provider="volcano", exit_code=1, duration=30)])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks: 1 (passed: 0, failed: 1)" in out
        assert "volcano" in out
        assert "0m30s" in out


# ── output format validation ───────────────────────────────


class TestOutputFormat:
    def test_output_has_header_sections(self, tmp_path: Path):
        """Output contains expected section headers."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [_make_record()])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        assert "Total tasks:" in out
        assert "Permanently failed" in out
        assert "Tasks today" in out
        assert "By provider:" in out

    def test_by_provider_aligned_columns(self, tmp_path: Path):
        """Provider lines have consistent column alignment."""
        jsonl = tmp_path / "golem.jsonl"
        _write_jsonl(jsonl, [
            _make_record(provider="codex", duration=60, exit_code=0),
            _make_record(provider="verylongname", duration=120, exit_code=0),
        ])
        mod = _load_module(jsonl, tmp_path / "queue.md")
        out, rc = _run_stats(mod)
        assert rc == 0
        lines = [l for l in out.splitlines() if l.strip().startswith("codex") or l.strip().startswith("verylongname")]
        assert len(lines) == 2
        # Both lines should contain "tasks", "passed", "failed", "avg"
        for line in lines:
            assert "tasks" in line
            assert "passed" in line
            assert "failed" in line
            assert "avg" in line
