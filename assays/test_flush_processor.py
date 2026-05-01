from __future__ import annotations

"""Tests for flush_processor.py — drains the memory-flush queue.

Covers: queue load/save round-trip, malformed line tolerance, dispatch_flush
skips when transcript missing, dry-run path, status transitions, and that the
processor only touches pending entries.

Inspiration:
    Manthan Gupta, "I Read Hermes Agent's Memory System, and It Fixes What
    OpenClaw Got Wrong" (2026-04). https://manthanguptaa.in/posts/hermes_memory/
    Note: ~/epigenome/chromatin/euchromatin/hermes-memory-architecture-2026-04.md
    Spec: ~/epigenome/chromatin/loci/plans/memory-flush-pre-compression.md
"""

import importlib.util
import json
import sys
import uuid
from pathlib import Path

import pytest

# ── module load (script style, not a package import) ──────────────────

SCRIPT = Path.home() / "germline/effectors/flush_processor.py"


@pytest.fixture(scope="session")
def fp():
    spec = importlib.util.spec_from_file_location("flush_processor", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["flush_processor"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def isolate_paths(tmp_path, monkeypatch, fp):
    """Redirect QUEUE/LOG to tmp so tests don't touch live state."""
    monkeypatch.setattr(fp, "QUEUE", tmp_path / "flush-queue.jsonl")
    monkeypatch.setattr(fp, "LOG", tmp_path / "flush-log.jsonl")
    return None


# ── queue I/O ─────────────────────────────────────────────────────────


def test_load_empty_queue_returns_empty_list(fp):
    assert fp.load_queue() == []


def test_save_then_load_round_trips(fp):
    entries = [
        {"session_id": "abc", "transcript_path": "/tmp/x", "status": "pending"},
        {"session_id": "def", "transcript_path": "/tmp/y", "status": "completed"},
    ]
    fp.save_queue(entries)
    assert fp.load_queue() == entries


def test_load_skips_malformed_lines(fp):
    fp.QUEUE.parent.mkdir(parents=True, exist_ok=True)
    fp.QUEUE.write_text(
        '{"session_id": "ok", "status": "pending"}\n'
        "not json at all\n"
        '{"session_id": "ok2", "status": "pending"}\n'
    )
    loaded = fp.load_queue()
    assert len(loaded) == 2
    assert {entry["session_id"] for entry in loaded} == {"ok", "ok2"}


# ── dispatch_flush behaviour ──────────────────────────────────────────


def test_dispatch_skips_when_transcript_missing(fp, tmp_path):
    entry = {
        "session_id": str(uuid.uuid4()),
        "transcript_path": str(tmp_path / "does-not-exist.jsonl"),
        "trigger": "manual",
    }
    outcome = fp.dispatch_flush(entry, dry=False)
    assert outcome["status"] == "skipped"
    assert "missing" in outcome["reason"]


def test_dispatch_dry_run_does_not_invoke_claude(fp, tmp_path, monkeypatch):
    transcript = tmp_path / "fake-transcript.jsonl"
    transcript.write_text('{"role":"user","content":"hi"}\n')

    def boom(*args, **kwargs):
        del args, kwargs
        raise AssertionError("subprocess must not be called in dry mode")

    monkeypatch.setattr(fp.subprocess, "run", boom)

    entry = {
        "session_id": "test",
        "transcript_path": str(transcript),
        "trigger": "manual",
    }
    outcome = fp.dispatch_flush(entry, dry=True)
    assert outcome["status"] == "dry-run"
    assert outcome["prompt_chars"] > 100


# ── process_queue end-to-end ──────────────────────────────────────────


def test_process_queue_only_touches_pending(fp, tmp_path):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("{}\n")

    fp.save_queue(
        [
            {
                "session_id": "p1",
                "transcript_path": str(transcript),
                "trigger": "auto",
                "status": "pending",
            },
            {
                "session_id": "done",
                "transcript_path": str(transcript),
                "trigger": "auto",
                "status": "completed",
            },
        ]
    )

    processed = fp.process_queue(once=False, dry=True)
    assert processed == 1

    after = fp.load_queue()
    statuses = {entry["session_id"]: entry["status"] for entry in after}
    assert statuses == {"p1": "dry-run", "done": "completed"}


def test_process_queue_writes_log(fp, tmp_path):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("{}\n")
    fp.save_queue(
        [
            {
                "session_id": "p1",
                "transcript_path": str(transcript),
                "trigger": "auto",
                "status": "pending",
            }
        ]
    )

    fp.process_queue(once=False, dry=True)

    assert fp.LOG.exists()
    log_lines = [json.loads(line) for line in fp.LOG.read_text().splitlines() if line.strip()]
    assert len(log_lines) == 1
    assert log_lines[0]["session_id"] == "p1"
    assert log_lines[0]["outcome"]["status"] == "dry-run"


def test_process_queue_returns_zero_when_empty(fp):
    assert fp.process_queue(once=False, dry=True) == 0


def test_process_queue_marks_failed_on_missing_claude(fp, tmp_path, monkeypatch):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("{}\n")
    fp.save_queue(
        [
            {
                "session_id": "nocl",
                "transcript_path": str(transcript),
                "trigger": "auto",
                "status": "pending",
            }
        ]
    )

    def no_claude(name):
        del name
        return None

    monkeypatch.setattr(fp.shutil, "which", no_claude)

    fp.process_queue(once=False, dry=False)

    after = fp.load_queue()
    assert after[0]["status"] == "failed"
    assert after[0]["last_error"]["status"] == "error"
    assert "claude binary" in after[0]["last_error"]["reason"]
