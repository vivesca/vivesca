from __future__ import annotations

"""Tests for effectors/coaching-stats."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

EFFECTOR = Path.home() / "germline" / "effectors" / "coaching-stats"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(EFFECTOR), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_coaching_md(tmp: Path) -> Path:
    p = tmp / "coaching.md"
    p.write_text(
        "## Header\n\n"
        "### Code patterns\n"
        "- **No hallucinated imports.** Only import what exists.\n"
        "- **Preserve return types.** Don't flatten.\n"
        "\n"
        "### Execution discipline\n"
        "- **Run ast.parse()** on every file.\n"
        "- **Write tests BEFORE implementation.**\n"
        "\n"
        "### Verification\n"
        "- **No placeholder markers.** Never leave TODO.\n"
    )
    return p


def _make_jsonl(tmp: Path) -> Path:
    p = tmp / "golem.jsonl"
    entries = [
        {
            "ts": "2026-03-31T12:00:00Z",
            "provider": "zhipu",
            "duration": 120,
            "exit": 0,
            "turns": 20,
            "prompt": "Write tests for effectors/foo",
            "tail": "All tests pass: uv run pytest -q 18 passed",
            "files_created": 3,
            "tests_passed": 18,
            "tests_failed": 0,
            "pytest_exit": 0,
        },
        {
            "ts": "2026-03-31T12:05:00Z",
            "provider": "volcano",
            "duration": 30,
            "exit": 1,
            "turns": 5,
            "prompt": "Fix import error in metabolon/bar",
            "tail": "ImportError: no module named baz",
            "files_created": 0,
            "tests_passed": 0,
            "tests_failed": 3,
            "pytest_exit": 1,
        },
        {
            "ts": "2026-03-31T12:10:00Z",
            "provider": "infini",
            "duration": 200,
            "exit": 0,
            "turns": 30,
            "prompt": "Read effectors/baz and fix SyntaxError",
            "tail": "Fixed SyntaxError via ast.parse check",
            "files_created": 1,
            "tests_passed": 5,
            "tests_failed": 0,
            "pytest_exit": 0,
        },
    ]
    p.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return p


def _make_daemon_log(tmp: Path) -> Path:
    p = tmp / "golem-daemon.log"
    p.write_text(
        "[2026-03-31 12:00:00] FAILED (exit=1): golem --provider zhipu Write tests for foo\n"
        "[2026-03-31 12:01:00] Completed OK: golem --provider volcano Fix bar\n"
        "[2026-03-31 12:02:00] FAILED (exit=127): golem --provider infini Research baz\n"
        "[2026-03-31 12:03:00] FAILED (exit=2): golem --provider zhipu Write tests for assays/\n"
    )
    return p


class TestParseCoaching:
    def test_parses_categories_and_bullets(self):
        with tempfile.TemporaryDirectory() as tmp:
            coaching = _make_coaching_md(Path(tmp))
            r = _run(
                [
                    "--coaching",
                    str(coaching),
                    "--jsonl",
                    "/dev/null",
                    "--daemon-log",
                    "/dev/null",
                    "--json",
                ]
            )
            assert r.returncode == 0, r.stderr
            data = json.loads(r.stdout)
            assert data["total_rules"] == 5
            cats = set(data["categories"].keys())
            assert "Code patterns" in cats
            assert "Execution discipline" in cats
            assert "Verification" in cats

    def test_empty_coaching_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "empty.md"
            p.write_text("")
            r = _run(
                [
                    "--coaching",
                    str(p),
                    "--jsonl",
                    "/dev/null",
                    "--daemon-log",
                    "/dev/null",
                    "--json",
                ]
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["total_rules"] == 0


class TestLoadJsonl:
    def test_loads_valid_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            jsonl = _make_jsonl(Path(tmp))
            r = _run(
                [
                    "--coaching",
                    "/dev/null",
                    "--jsonl",
                    str(jsonl),
                    "--daemon-log",
                    "/dev/null",
                    "--json",
                ]
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["total_jsonl_entries"] == 3

    def test_skips_malformed_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.jsonl"
            p.write_text(
                '{"ts":"ok","provider":"zhipu"}\nNOT JSON\n{"ts":"ok2","provider":"volcano"}\n'
            )
            r = _run(
                [
                    "--coaching",
                    "/dev/null",
                    "--jsonl",
                    str(p),
                    "--daemon-log",
                    "/dev/null",
                    "--json",
                ]
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["total_jsonl_entries"] == 2


class TestLoadDaemonFailures:
    def test_extracts_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = _make_daemon_log(Path(tmp))
            r = _run(
                [
                    "--coaching",
                    "/dev/null",
                    "--jsonl",
                    "/dev/null",
                    "--daemon-log",
                    str(log),
                    "--json",
                ]
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["total_daemon_failures"] == 3

    def test_empty_daemon_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "empty.log"
            p.write_text("")
            r = _run(
                [
                    "--coaching",
                    "/dev/null",
                    "--jsonl",
                    "/dev/null",
                    "--daemon-log",
                    str(p),
                    "--json",
                ]
            )
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["total_daemon_failures"] == 0


class TestAnalysis:
    def test_provider_breakdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            jsonl = _make_jsonl(tmpdir)
            r = _run(
                [
                    "--coaching",
                    "/dev/null",
                    "--jsonl",
                    str(jsonl),
                    "--daemon-log",
                    "/dev/null",
                    "--json",
                ]
            )
            data = json.loads(r.stdout)
            provs = data["provider_stats"]
            assert "zhipu" in provs
            assert "volcano" in provs
            assert "infini" in provs
            assert provs["volcano"]["failures"] == 1  # exit=1 and tests_failed=3
            assert provs["zhipu"]["runs"] == 1

    def test_signal_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            jsonl = _make_jsonl(tmpdir)
            r = _run(
                [
                    "--coaching",
                    "/dev/null",
                    "--jsonl",
                    str(jsonl),
                    "--daemon-log",
                    "/dev/null",
                    "--json",
                ]
            )
            data = json.loads(r.stdout)
            signals = {s["signal"]: s for s in data["signal_stats"]}
            # Entry with "import" in prompt/tail should show up in hallucinated-imports
            assert signals["hallucinated-imports"]["jsonl_mentions"] >= 1
            # Entry with "test" should show up in tdd
            assert signals["tdd"]["jsonl_mentions"] >= 1


class TestTextReport:
    def test_report_has_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            coaching = _make_coaching_md(tmpdir)
            jsonl = _make_jsonl(tmpdir)
            log = _make_daemon_log(tmpdir)
            r = _run(
                ["--coaching", str(coaching), "--jsonl", str(jsonl), "--daemon-log", str(log)]
            )
            assert r.returncode == 0
            output = r.stdout
            assert "COACHING EFFECTIVENESS REPORT" in output
            assert "SUMMARY" in output
            assert "RULES BY CATEGORY" in output
            assert "FAILURE SIGNAL DETECTION" in output
            assert "PROVIDER BREAKDOWN" in output
            assert "EFFECTIVENESS RANKING" in output
            assert "PER-RULE DETAIL" in output


class TestMissingFiles:
    def test_all_paths_missing(self):
        r = _run(
            [
                "--coaching",
                "/nonexistent/file.md",
                "--jsonl",
                "/nonexistent/file.jsonl",
                "--daemon-log",
                "/nonexistent/file.log",
                "--json",
            ]
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["total_rules"] == 0
        assert data["total_jsonl_entries"] == 0
        assert data["total_daemon_failures"] == 0
