"""Tests for morphogen hook (InstructionsLoaded logger)."""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "synaptic"))


# ── main ─────────────────────────────────────────────────────


def test_main_writes_entry(tmp_path: Path) -> None:
    """Valid JSON on stdin writes a tab-separated log line."""
    log_file = tmp_path / "context-audit.log"
    stdin_data = json.dumps({
        "file_path": "/some/path.md",
        "memory_type": "skill",
        "load_reason": "auto",
    })
    with patch("sys.stdin", StringIO(stdin_data)):
        # Import fresh so main() picks up patched LOG
        import importlib
        import morphogen
        with patch.object(morphogen, "LOG", log_file):
            morphogen.main()

    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    parts = lines[0].split("\t")
    assert len(parts) == 4
    assert parts[1] == "skill"
    assert parts[2] == "auto"
    assert parts[3] == "/some/path.md"


def test_main_handles_invalid_json(tmp_path: Path) -> None:
    """Invalid JSON on stdin = silent return, no crash."""
    log_file = tmp_path / "context-audit.log"
    with patch("sys.stdin", StringIO("not json at all")):
        import morphogen
        with patch.object(morphogen, "LOG", log_file):
            morphogen.main()
    assert not log_file.exists()


def test_main_missing_fields(tmp_path: Path) -> None:
    """JSON with missing fields uses 'unknown' defaults."""
    log_file = tmp_path / "context-audit.log"
    stdin_data = json.dumps({})
    with patch("sys.stdin", StringIO(stdin_data)):
        import morphogen
        with patch.object(morphogen, "LOG", log_file):
            morphogen.main()

    line = log_file.read_text().strip()
    parts = line.split("\t")
    assert parts[1] == "unknown"
    assert parts[2] == "unknown"
    assert parts[3] == "unknown"


def test_main_appends_multiple(tmp_path: Path) -> None:
    """Multiple calls append lines."""
    log_file = tmp_path / "context-audit.log"
    import morphogen
    for label in ("first", "second", "third"):
        stdin_data = json.dumps({"file_path": label, "memory_type": "t", "load_reason": "r"})
        with patch("sys.stdin", StringIO(stdin_data)):
            with patch.object(morphogen, "LOG", log_file):
                morphogen.main()
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 3
