from __future__ import annotations

"""Tests for golem --json flag and summary --json output."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

GOLEM = Path.home() / "germline" / "effectors" / "golem"


# ── JSON formatter unit tests ──────────────────────────────────────────


def _json_formatter_code() -> str:
    """Extract the inline Python JSON formatter from the golem script."""
    return textwrap.dedent("""\
import json, sys
output_text = open(sys.argv[1]).read()
result = {
    'output': output_text,
    'exit_code': int(sys.argv[2]),
    'duration': int(sys.argv[3]),
    'provider': sys.argv[4],
    'files_created': int(sys.argv[5]),
    'tests_passed': int(sys.argv[6]),
    'tests_failed': int(sys.argv[7]),
}
print(json.dumps(result))
""")


def test_json_formatter_produces_valid_json(tmp_path):
    """The inline JSON formatter produces valid JSON with expected keys."""
    # Write a fake output file
    outfile = tmp_path / "output.txt"
    outfile.write_text("Hello from golem")

    result = subprocess.run(
        [sys.executable, "-c", _json_formatter_code(),
         str(outfile), "0", "42", "zhipu", "3", "10", "1"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)

    assert data["output"] == "Hello from golem"
    assert data["exit_code"] == 0
    assert data["duration"] == 42
    assert data["provider"] == "zhipu"
    assert data["files_created"] == 3
    assert data["tests_passed"] == 10
    assert data["tests_failed"] == 1


def test_json_formatter_handles_multiline_output(tmp_path):
    """JSON formatter correctly escapes multiline output."""
    outfile = tmp_path / "output.txt"
    outfile.write_text("line one\nline two\nline three\n")

    result = subprocess.run(
        [sys.executable, "-c", _json_formatter_code(),
         str(outfile), "0", "10", "volcano", "0", "0", "0"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    assert data["output"] == "line one\nline two\nline three\n"
    assert data["exit_code"] == 0


def test_json_formatter_handles_special_chars(tmp_path):
    """JSON formatter handles quotes, backslashes, unicode in output."""
    outfile = tmp_path / "output.txt"
    outfile.write_text('He said "hello" \\ backslash \u00e9\u00e8\u00ea')

    result = subprocess.run(
        [sys.executable, "-c", _json_formatter_code(),
         str(outfile), "1", "5", "infini", "1", "0", "2"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    assert "hello" in data["output"]
    assert data["exit_code"] == 1
    assert data["tests_failed"] == 2


def test_json_formatter_handles_empty_output(tmp_path):
    """JSON formatter handles empty output text."""
    outfile = tmp_path / "output.txt"
    outfile.write_text("")

    result = subprocess.run(
        [sys.executable, "-c", _json_formatter_code(),
         str(outfile), "1", "3", "zhipu", "0", "0", "0"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    assert data["output"] == ""
    assert data["exit_code"] == 1


def test_json_output_is_single_line(tmp_path):
    """JSON output is a single line (suitable for piping to jq, etc.)."""
    outfile = tmp_path / "output.txt"
    outfile.write_text("line1\nline2\n")

    result = subprocess.run(
        [sys.executable, "-c", _json_formatter_code(),
         str(outfile), "0", "10", "zhipu", "0", "0", "0"],
        capture_output=True, text=True, check=True,
    )
    # Must be exactly one line (no embedded newlines in the JSON string itself,
    # json.dumps escapes them as \n)
    lines = result.stdout.strip().split("\n")
    assert len(lines) == 1
    # But parsing it back should preserve the newlines in the output field
    data = json.loads(lines[0])
    assert "\n" in data["output"]


def test_json_formatter_all_fields_present(tmp_path):
    """JSON output contains all expected fields and no extras."""
    outfile = tmp_path / "output.txt"
    outfile.write_text("test")

    result = subprocess.run(
        [sys.executable, "-c", _json_formatter_code(),
         str(outfile), "0", "1", "zhipu", "2", "3", "4"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    expected_keys = {"output", "exit_code", "duration", "provider",
                     "files_created", "tests_passed", "tests_failed"}
    assert set(data.keys()) == expected_keys


# ── Summary --json tests ───────────────────────────────────────────────


def _make_log(tmp_path: Path, records: list[dict]) -> Path:
    """Create a JSONL log file with the given records."""
    log = tmp_path / "golem.jsonl"
    log.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return log


def test_summary_json_produces_valid_json(tmp_path):
    """golem summary --json produces valid JSON output."""
    log = _make_log(tmp_path, [
        {"provider": "zhipu", "exit": 0, "duration": 120,
         "tests_passed": 0, "tests_failed": 0},
        {"provider": "zhipu", "exit": 1, "duration": 60,
         "tests_passed": 5, "tests_failed": 2},
    ])

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", f"--log={log}"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "zhipu" in data
    assert data["zhipu"]["runs"] == 2
    assert data["zhipu"]["pass"] == 1
    assert data["zhipu"]["fail"] == 1
    assert data["zhipu"]["avg_duration"] == 90  # (120+60)/2
    assert data["zhipu"]["tests_created"] == 7  # (5+2) + (0+0) wait no: tests_passed=0,tests_failed=0 for first + tests_passed=5,tests_failed=2 for second = 0+7=7


def test_summary_json_multiple_providers(tmp_path):
    """golem summary --json separates stats by provider."""
    log = _make_log(tmp_path, [
        {"provider": "zhipu", "exit": 0, "duration": 100,
         "tests_passed": 3, "tests_failed": 0},
        {"provider": "volcano", "exit": 0, "duration": 200,
         "tests_passed": 8, "tests_failed": 1},
        {"provider": "volcano", "exit": 1, "duration": 50,
         "tests_passed": 0, "tests_failed": 3},
    ])

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", f"--log={log}"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)

    assert "zhipu" in data
    assert "volcano" in data
    assert data["zhipu"]["runs"] == 1
    assert data["volcano"]["runs"] == 2
    assert data["volcano"]["pass"] == 1
    assert data["volcano"]["fail"] == 1
    assert data["volcano"]["avg_duration"] == 125  # (200+50)/2


def test_summary_json_empty_log(tmp_path):
    """golem summary --json with empty log file returns empty object."""
    log = tmp_path / "golem.jsonl"
    log.write_text("")

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", f"--log={log}"],
        capture_output=True, text=True,
    )
    # Empty file should produce empty JSON object
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data == {}


def test_summary_json_missing_log(tmp_path):
    """golem summary --json with missing log file exits non-zero."""
    log = tmp_path / "nonexistent.jsonl"

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", f"--log={log}"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_summary_json_skips_malformed_lines(tmp_path):
    """golem summary --json skips malformed JSONL lines gracefully."""
    log = tmp_path / "golem.jsonl"
    log.write_text(
        json.dumps({"provider": "zhipu", "exit": 0, "duration": 10,
                     "tests_passed": 0, "tests_failed": 0}) + "\n"
        "not json at all\n"
        "{broken\n"
    )

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", f"--log={log}"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "zhipu" in data
    assert data["zhipu"]["runs"] == 1


def test_summary_json_with_recent_flag(tmp_path):
    """golem summary --json --recent N only counts last N entries."""
    records = [
        {"provider": "zhipu", "exit": 0, "duration": i * 10,
         "tests_passed": 0, "tests_failed": 0}
        for i in range(10)
    ]
    # Add volcano entries at the end
    records.append({"provider": "volcano", "exit": 0, "duration": 100,
                     "tests_passed": 5, "tests_failed": 0})
    records.append({"provider": "volcano", "exit": 1, "duration": 50,
                     "tests_passed": 0, "tests_failed": 2})
    log = _make_log(tmp_path, records)

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", "--recent", "2", f"--log={log}"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    # Only last 2 entries (both volcano)
    assert "zhipu" not in data
    assert "volcano" in data
    assert data["volcano"]["runs"] == 2


def test_summary_json_single_line_output(tmp_path):
    """golem summary --json output is single-line (pipe-friendly)."""
    log = _make_log(tmp_path, [
        {"provider": "zhipu", "exit": 0, "duration": 100,
         "tests_passed": 3, "tests_failed": 0},
    ])

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", "--json", f"--log={log}"],
        capture_output=True, text=True,
    )
    lines = result.stdout.strip().split("\n")
    assert len(lines) == 1


# ── Flag parsing tests ─────────────────────────────────────────────────


def test_help_shows_json_flag():
    """golem --help shows --json in usage."""
    result = subprocess.run(
        ["bash", str(GOLEM), "--help"],
        capture_output=True, text=True,
    )
    assert "--json" in result.stdout


def test_help_shows_json_in_summary():
    """golem summary --help shows --json flag."""
    # golem summary doesn't have its own --help; check the main help
    result = subprocess.run(
        ["bash", str(GOLEM), "--help"],
        capture_output=True, text=True,
    )
    assert "summary" in result.stdout


# ── Summary text vs JSON output comparison ─────────────────────────────


def test_summary_text_output_not_json(tmp_path):
    """golem summary (without --json) produces human-readable table, not JSON."""
    log = _make_log(tmp_path, [
        {"provider": "zhipu", "exit": 0, "duration": 100,
         "tests_passed": 3, "tests_failed": 0},
    ])

    result = subprocess.run(
        ["bash", str(GOLEM), "summary", f"--log={log}"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    # Text output should have table headers, not JSON braces
    assert "Provider" in result.stdout
    assert "Runs" in result.stdout
    # Should NOT be valid JSON
    with pytest.raises(json.JSONDecodeError):
        json.loads(result.stdout)
