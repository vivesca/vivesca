#!/usr/bin/env python3
"""Tests for effectors/golem-cost — golem run cost estimator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _load_mod():
    """Load golem-cost module via exec."""
    source = Path("/home/terry/germline/effectors/golem-cost").read_text()
    ns: dict = {"__name__": "golem_cost"}
    exec(source, ns)
    return ns


_mod = _load_mod()
load_jsonl = _mod["load_jsonl"]
estimate_tokens = _mod["estimate_tokens"]
get_cost_per_m = _mod["get_cost_per_m"]
compute_run_cost = _mod["compute_run_cost"]
compute_summary = _mod["compute_summary"]
fmt_tokens = _mod["fmt_tokens"]
fmt_cost = _mod["fmt_cost"]
print_report = _mod["print_report"]
print_by_run = _mod["print_by_run"]
print_json_report = _mod["print_json_report"]
main = _mod["main"]
JSONL_PATH = _mod["JSONL_PATH"]
TOKENS_PER_TURN = _mod["TOKENS_PER_TURN"]


# ── estimate_tokens ──────────────────────────────────────────────────────


class TestEstimateTokens:
    def test_zero_turns(self):
        assert estimate_tokens(0) == 0

    def test_one_turn(self):
        assert estimate_tokens(1) == TOKENS_PER_TURN

    def test_many_turns(self):
        assert estimate_tokens(30) == 30 * TOKENS_PER_TURN

    def test_negative_turns(self):
        assert estimate_tokens(-1) == -TOKENS_PER_TURN


# ── get_cost_per_m ──────────────────────────────────────────────────────


class TestGetCostPerM:
    def test_known_provider(self):
        assert get_cost_per_m("zhipu") > 0

    def test_unknown_provider(self):
        default = get_cost_per_m("default")
        assert get_cost_per_m("nonexistent_xyz") == default

    def test_all_providers_have_cost(self):
        for p in ("zhipu", "infini", "volcano"):
            assert get_cost_per_m(p) > 0


# ── load_jsonl ──────────────────────────────────────────────────────────


class TestLoadJsonl:
    def test_missing_file(self, tmp_path):
        assert load_jsonl(tmp_path / "nope.jsonl") == []

    def test_empty_file(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text("")
        assert load_jsonl(p) == []

    def test_valid_records(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text(
            '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0,"turns":5}\n'
            '{"ts":"2026-01-02","provider":"volcano","duration":20,"exit":1,"turns":3}\n'
        )
        recs = load_jsonl(p)
        assert len(recs) == 2
        assert recs[0]["provider"] == "zhipu"
        assert recs[0]["turns"] == 5
        assert recs[1]["exit"] == 1

    def test_skips_bad_lines(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text('{"ok":true}\nBADLINE\n{"ok":false}\n')
        assert len(load_jsonl(p)) == 2

    def test_skips_blank_lines(self, tmp_path):
        p = tmp_path / "golem.jsonl"
        p.write_text('{"a":1}\n\n{"b":2}\n')
        assert len(load_jsonl(p)) == 2


# ── compute_run_cost ────────────────────────────────────────────────────


class TestComputeRunCost:
    def test_basic_run(self):
        record = {"provider": "zhipu", "turns": 10, "exit": 0, "duration": 60}
        result = compute_run_cost(record)
        assert result["provider"] == "zhipu"
        assert result["turns"] == 10
        assert result["tokens_est"] == 10 * TOKENS_PER_TURN
        assert result["exit"] == 0
        assert result["cost_usd"] > 0

    def test_zero_turns(self):
        record = {"provider": "volcano", "turns": 0, "exit": 0, "duration": 5}
        result = compute_run_cost(record)
        assert result["tokens_est"] == 0
        assert result["cost_usd"] == 0.0

    def test_missing_turns_field(self):
        record = {"provider": "infini", "exit": 0, "duration": 10}
        result = compute_run_cost(record)
        assert result["turns"] == 0
        assert result["tokens_est"] == 0

    def test_missing_provider(self):
        record = {"turns": 5, "exit": 0, "duration": 20}
        result = compute_run_cost(record)
        assert result["provider"] == "unknown"
        assert result["tokens_est"] == 5 * TOKENS_PER_TURN


# ── compute_summary ─────────────────────────────────────────────────────


class TestComputeSummary:
    def test_empty_records(self):
        s = compute_summary([])
        assert s["total_runs"] == 0
        assert s["total_tokens"] == 0
        assert s["total_cost"] == 0.0
        assert s["runs"] == []

    def test_single_record(self):
        recs = [{"provider": "zhipu", "turns": 20, "exit": 0, "duration": 100}]
        s = compute_summary(recs)
        assert s["total_runs"] == 1
        assert s["total_tokens"] == 20 * TOKENS_PER_TURN
        assert s["total_cost"] > 0
        assert "zhipu" in s["by_provider"]
        assert s["by_provider"]["zhipu"]["pass"] == 1
        assert s["by_provider"]["zhipu"]["fail"] == 0

    def test_multiple_providers(self):
        recs = [
            {"provider": "zhipu", "turns": 10, "exit": 0, "duration": 50},
            {"provider": "volcano", "turns": 30, "exit": 0, "duration": 200},
            {"provider": "zhipu", "turns": 5, "exit": 1, "duration": 30},
        ]
        s = compute_summary(recs)
        assert s["total_runs"] == 3
        assert s["total_tokens"] == (10 + 30 + 5) * TOKENS_PER_TURN
        assert s["by_provider"]["zhipu"]["pass"] == 1
        assert s["by_provider"]["zhipu"]["fail"] == 1
        assert s["by_provider"]["volcano"]["pass"] == 1

    def test_cost_is_sum(self):
        recs = [
            {"provider": "zhipu", "turns": 10, "exit": 0, "duration": 50},
            {"provider": "zhipu", "turns": 20, "exit": 0, "duration": 100},
        ]
        s = compute_summary(recs)
        expected = sum(
            r["turns"] * TOKENS_PER_TURN / 1_000_000 * get_cost_per_m("zhipu")
            for r in recs
        )
        assert abs(s["total_cost"] - expected) < 0.001


# ── fmt_tokens ──────────────────────────────────────────────────────────


class TestFmtTokens:
    def test_small_number(self):
        assert fmt_tokens(500) == "500"

    def test_thousands(self):
        assert fmt_tokens(15_000) == "15K"

    def test_millions(self):
        assert fmt_tokens(2_500_000) == "2.5M"

    def test_zero(self):
        assert fmt_tokens(0) == "0"


# ── fmt_cost ────────────────────────────────────────────────────────────


class TestFmtCost:
    def test_normal_cost(self):
        assert fmt_cost(1.50) == "$1.50"

    def test_small_cost(self):
        assert fmt_cost(0.005) == "$0.0050"

    def test_zero(self):
        assert fmt_cost(0.0) == "$0.0000"

    def test_large_cost(self):
        assert fmt_cost(100.0) == "$100.00"


# ── print_report ────────────────────────────────────────────────────────


class TestPrintReport:
    def test_basic_report(self, capsys):
        summary = compute_summary([
            {"provider": "zhipu", "turns": 25, "exit": 0, "duration": 120},
        ])
        print_report(summary, use_color=False)
        out = capsys.readouterr().out
        assert "Golem Cost Report" in out
        assert "zhipu" in out
        assert "100K" in out  # 25 * 4000 = 100000 = 100K

    def test_empty_report(self, capsys):
        summary = compute_summary([])
        print_report(summary, use_color=False)
        out = capsys.readouterr().out
        assert "Golem Cost Report" in out
        assert "Runs: 0" in out


# ── print_by_run ────────────────────────────────────────────────────────


class TestPrintByRun:
    def test_with_runs(self, capsys):
        summary = compute_summary([
            {"provider": "zhipu", "turns": 10, "exit": 0, "duration": 60,
             "prompt": "Build a thing"},
        ])
        print_by_run(summary, use_color=False)
        out = capsys.readouterr().out
        assert "Per-Run Detail" in out
        assert "Build a thing" in out

    def test_empty(self, capsys):
        summary = compute_summary([])
        print_by_run(summary, use_color=False)
        out = capsys.readouterr().out
        assert "No runs found" in out


# ── print_json_report ───────────────────────────────────────────────────


class TestPrintJsonReport:
    def test_json_output(self, capsys):
        summary = compute_summary([
            {"provider": "volcano", "turns": 15, "exit": 0, "duration": 90},
        ])
        print_json_report(summary)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["total_runs"] == 1
        assert data["total_tokens"] == 15 * TOKENS_PER_TURN
        assert "volcano" in data["by_provider"]


# ── main ────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_default(self, tmp_path, capsys):
        orig = _mod["JSONL_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"zhipu","turns":10,"exit":0,"duration":60,"prompt":"test"}\n'
            )
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig
        assert rc == 0
        out = capsys.readouterr().out
        assert "Golem Cost Report" in out

    def test_main_json(self, tmp_path, capsys):
        orig = _mod["JSONL_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            (tmp_path / "golem.jsonl").write_text(
                '{"ts":"2026-01-01","provider":"infini","turns":5,"exit":0,"duration":30}\n'
            )
            rc = main(["--json"])
        finally:
            _mod["JSONL_PATH"] = orig
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["total_runs"] == 1
        assert "infini" in data["by_provider"]

    def test_main_by_run(self, tmp_path, capsys):
        orig = _mod["JSONL_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            (tmp_path / "golem.jsonl").write_text(
                '{"provider":"volcano","turns":8,"exit":0,"duration":45,"prompt":"do stuff"}\n'
            )
            rc = main(["--by-run", "--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig
        assert rc == 0
        out = capsys.readouterr().out
        assert "Per-Run Detail" in out
        assert "do stuff" in out

    def test_main_empty_jsonl(self, tmp_path, capsys):
        orig = _mod["JSONL_PATH"]
        try:
            _mod["JSONL_PATH"] = tmp_path / "golem.jsonl"
            (tmp_path / "golem.jsonl").write_text("")
            rc = main(["--no-color"])
        finally:
            _mod["JSONL_PATH"] = orig
        assert rc == 0
        out = capsys.readouterr().out
        assert "Runs: 0" in out

    def test_help_flag(self, capsys):
        rc = main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "golem-cost" in out

    def test_script_exists(self):
        assert Path("/home/terry/germline/effectors/golem-cost").exists()

    def test_script_executable(self):
        p = Path("/home/terry/germline/effectors/golem-cost")
        assert p.stat().st_mode & 0o111
