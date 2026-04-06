import json
from pathlib import Path
from mtor.log import LogEntry, read_log, filter_stalls, filter_reflections, summary_stats

def _write_log(path, entries):
    with open(path, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")

def test_read_log(tmp_path):
    log_file = tmp_path / "test.jsonl"
    _write_log(log_file, [
        {"ts": "t1", "provider": "p", "duration": 120, "exit": 0, "files_created": 3, "stall": "none", "reflection": "", "tail": "done"},
        {"ts": "t2", "provider": "p", "duration": 300, "exit": 1, "files_created": 0, "stall": "built-nothing", "reflection": "", "tail": "failed"},
    ])
    entries = read_log(log_file)
    assert len(entries) == 2
    assert entries[0].succeeded
    assert not entries[1].succeeded

def test_filter_stalls(tmp_path):
    log_file = tmp_path / "test.jsonl"
    _write_log(log_file, [
        {"ts": "t1", "provider": "p", "duration": 10, "exit": 0, "files_created": 1, "stall": "none", "reflection": "", "tail": ""},
        {"ts": "t2", "provider": "p", "duration": 300, "exit": 1, "files_created": 0, "stall": "monologue", "reflection": "", "tail": ""},
    ])
    assert len(filter_stalls(read_log(log_file))) == 1

def test_summary_stats():
    entries = [LogEntry("t1", "p", 100, 0, 2, "", "none", ""), LogEntry("t2", "p", 200, 1, 0, "", "built-nothing", ""), LogEntry("t3", "p", 150, 0, 1, "learned", "none", "")]
    stats = summary_stats(entries)
    assert stats["total"] == 3 and stats["success"] == 2 and stats["stalled"] == 1

def test_empty_log():
    assert summary_stats([])["total"] == 0
