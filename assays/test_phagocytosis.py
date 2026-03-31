#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/phagocytosis.py — Obsidian lastOpenFiles logging.

All filesystem calls are mocked.
"""


import io
import json

import pytest
from pathlib import Path
from unittest.mock import patch

PHAGO_PATH = Path(__file__).resolve().parents[1] / "effectors" / "phagocytosis.py"


# ── Load module via exec ────────────────────────────────────────────────────

@pytest.fixture()
def phago():
    """Load phagocytosis via exec into an isolated namespace."""
    ns: dict = {"__name__": "phagocytosis"}
    source = PHAGO_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("phago", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── Path constants ──────────────────────────────────────────────────────────


class TestPhagoPaths:
    def test_chromatin_path(self, phago):
        assert str(phago.CHROMATIN).endswith("epigenome/chromatin")

    def test_workspace_path(self, phago):
        assert phago.WORKSPACE == phago.CHROMATIN / ".obsidian" / "workspace.json"

    def test_log_file_path(self, phago):
        assert phago.LOG_FILE == phago.CHROMATIN / ".consumption-log.jsonl"


# ── read_last_open_files ───────────────────────────────────────────────────


class TestReadLastOpenFiles:
    def test_extracts_file_list(self, phago):
        data = json.dumps({"lastOpenFiles": ["/a.md", "/b.md", "/c.md"]})
        with patch("pathlib.Path.read_text", return_value=data):
            result = phago.read_last_open_files()
        assert result == ["/a.md", "/b.md", "/c.md"]

    def test_missing_key_returns_empty(self, phago):
        with patch("pathlib.Path.read_text", return_value="{}"):
            result = phago.read_last_open_files()
        assert result == []

    def test_single_file(self, phago):
        data = json.dumps({"lastOpenFiles": ["/only.md"]})
        with patch("pathlib.Path.read_text", return_value=data):
            result = phago.read_last_open_files()
        assert result == ["/only.md"]


# ── read_last_snapshot ─────────────────────────────────────────────────────


class TestReadLastSnapshot:
    def test_returns_none_when_no_file(self, phago):
        with patch("pathlib.Path.exists", return_value=False):
            result = phago.read_last_snapshot()
        assert result is None

    def test_returns_none_when_empty_file(self, phago):
        content = b""
        bio = io.BytesIO(content)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.open", return_value=bio):
                result = phago.read_last_snapshot()
        assert result is None

    def test_reads_last_line(self, phago):
        entry1 = json.dumps({"ts": 100, "files": ["x.md"]})
        entry2 = json.dumps({"ts": 200, "files": ["y.md", "z.md"]})
        content = f"{entry1}\n{entry2}\n".encode()
        bio = io.BytesIO(content)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.open", return_value=bio):
                result = phago.read_last_snapshot()
        assert result == ["y.md", "z.md"]

    def test_single_entry_file(self, phago):
        entry = json.dumps({"ts": 100, "files": ["solo.md"]})
        content = f"{entry}\n".encode()
        bio = io.BytesIO(content)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.open", return_value=bio):
                result = phago.read_last_snapshot()
        assert result == ["solo.md"]


# ── main() integration ─────────────────────────────────────────────────────


class TestPhagoMain:
    @pytest.fixture(autouse=True)
    def _isolate_argv(self):
        with patch("sys.argv", ["phagocytosis"]):
            yield

    def test_exits_when_workspace_missing(self, phago):
        with patch("pathlib.Path.exists", return_value=False):
            phago.main()  # should return silently, no error

    def test_exits_when_no_open_files(self, phago):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value='{"lastOpenFiles": []}'):
                phago.main()  # should return silently

    def test_skips_write_when_no_change(self, phago):
        files = ["/a.md", "/b.md"]
        entry = json.dumps({"ts": 100, "files": files})
        content = f"{entry}\n".encode()
        log_bio = io.BytesIO(content)

        written = []

        class AppendFile:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def write(self, data):
                written.append(data)

        def mock_open(self, *args, **kwargs):
            if self == phago.LOG_FILE:
                if args and "rb" in args[0]:
                    return log_bio
                if args and "a" in args[0]:
                    return AppendFile()
            raise FileNotFoundError(self)

        def mock_exists(self_path):
            return str(self_path) in (
                str(phago.WORKSPACE),
                str(phago.LOG_FILE),
            )

        with patch("pathlib.Path.exists", mock_exists):
            with patch(
                "pathlib.Path.read_text",
                return_value=json.dumps({"lastOpenFiles": files}),
            ):
                with patch("pathlib.Path.open", mock_open):
                    phago.main()
        assert written == [], "Should not write when files unchanged"

    def test_writes_entry_when_changed(self, phago):
        last_files = ["/a.md"]
        current_files = ["/b.md", "/c.md"]
        entry = json.dumps({"ts": 100, "files": last_files})
        content = f"{entry}\n".encode()
        log_bio = io.BytesIO(content)

        written = []

        class AppendFile:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def write(self, data):
                written.append(data)

        def mock_open(self, *args, **kwargs):
            if self == phago.LOG_FILE:
                if args and "rb" in args[0]:
                    return log_bio
                if args and "a" in args[0]:
                    return AppendFile()
            raise FileNotFoundError(self)

        def mock_exists(self_path):
            return str(self_path) in (
                str(phago.WORKSPACE),
                str(phago.LOG_FILE),
            )

        with patch("pathlib.Path.exists", mock_exists):
            with patch(
                "pathlib.Path.read_text",
                return_value=json.dumps({"lastOpenFiles": current_files}),
            ):
                with patch("pathlib.Path.open", mock_open):
                    with patch("time.time", return_value=99999.0):
                        phago.main()

        assert len(written) == 1
        data = json.loads(written[0].strip())
        assert data["ts"] == 99999
        assert data["files"] == current_files

    def test_writes_entry_when_no_previous_log(self, phago):
        current_files = ["/new1.md", "/new2.md"]
        written = []

        class AppendFile:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def write(self, data):
                written.append(data)

        def mock_open(self, *args, **kwargs):
            if self == phago.LOG_FILE and args and "a" in args[0]:
                return AppendFile()
            raise FileNotFoundError(self)

        def mock_exists(self_path):
            s = str(self_path)
            if s == str(phago.WORKSPACE):
                return True
            if s == str(phago.LOG_FILE):
                return False  # no previous log
            return False

        with patch("pathlib.Path.exists", mock_exists):
            with patch(
                "pathlib.Path.read_text",
                return_value=json.dumps({"lastOpenFiles": current_files}),
            ):
                with patch("pathlib.Path.open", mock_open):
                    with patch("time.time", return_value=42.0):
                        phago.main()

        assert len(written) == 1
        data = json.loads(written[0].strip())
        assert data["files"] == current_files
