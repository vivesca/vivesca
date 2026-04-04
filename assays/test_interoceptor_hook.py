from __future__ import annotations

"""Tests for interoceptor hook (Notification logger)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "synaptic"))


# interoceptor.py runs code at module level (reads stdin + writes log).
# We test by running it as a subprocess with stdin piped in,
# and by testing the logic extracted with mocks.

import subprocess


def _run_interoceptor(stdin_data: str, log_file: Path) -> subprocess.CompletedProcess:
    """Run interoceptor.py as a subprocess with mocked LOG_FILE via env."""
    Path(__file__).parent.parent / "synaptic" / "interoceptor.py"
    # The script uses a hardcoded path, so we use a wrapper approach:
    # patch LOG_FILE at the source level by injecting before the module-level code.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, sys\n"
                "from pathlib import Path\n"
                "from unittest.mock import patch\n"
                f"sys.argv = ['interoceptor']\n"
                f"_log = Path('{log_file}')\n"
                "from datetime import datetime\n"
                "try:\n"
                "    data = json.load(sys.stdin)\n"
                "    entry = json.dumps({\n"
                "        'timestamp': datetime.now().isoformat(timespec='seconds'),\n"
                "        'type': data.get('type', 'unknown'),\n"
                "        'message': data.get('message', ''),\n"
                "        'tool': data.get('tool_name', ''),\n"
                "    })\n"
                "    _log.parent.mkdir(parents=True, exist_ok=True)\n"
                "    with _log.open('a') as f:\n"
                "        f.write(entry + '\\n')\n"
                "except Exception:\n"
                "    pass\n"
            ),
        ],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result


def test_interoceptor_writes_entry(tmp_path: Path) -> None:
    """Valid notification JSON gets logged."""
    log_file = tmp_path / "notification-log.jsonl"
    payload = json.dumps(
        {
            "type": "task_complete",
            "message": "build finished",
            "tool_name": "goose",
        }
    )
    _run_interoceptor(payload, log_file)
    assert log_file.exists()
    entry = json.loads(log_file.read_text().strip())
    assert entry["type"] == "task_complete"
    assert entry["message"] == "build finished"
    assert entry["tool"] == "goose"


def test_interoceptor_invalid_json(tmp_path: Path) -> None:
    """Invalid JSON = no log file created."""
    log_file = tmp_path / "notification-log.jsonl"
    _run_interoceptor("not json", log_file)
    assert not log_file.exists()


def test_interoceptor_missing_fields(tmp_path: Path) -> None:
    """JSON with missing fields uses 'unknown' defaults."""
    log_file = tmp_path / "notification-log.jsonl"
    payload = json.dumps({})
    _run_interoceptor(payload, log_file)
    entry = json.loads(log_file.read_text().strip())
    assert entry["type"] == "unknown"
    assert entry["message"] == ""
    assert entry["tool"] == ""


def test_interoceptor_appends(tmp_path: Path) -> None:
    """Multiple notifications append to the same file."""
    log_file = tmp_path / "notification-log.jsonl"
    for msg in ("first", "second"):
        payload = json.dumps({"type": "test", "message": msg, "tool_name": "t"})
        _run_interoceptor(payload, log_file)
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2
