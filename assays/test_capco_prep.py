from __future__ import annotations

"""Tests for effectors/capco-prep — CAPCO readiness checklist.

Capco-prep is a script — loaded via exec(), never imported.
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

CAPCO_PREP_PATH = Path(__file__).resolve().parents[1] / "effectors" / "capco-prep"


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest.fixture()
def cp(tmp_path):
    """Load capco-prep via exec, redirecting CAPCO_DIR to tmp_path."""
    capco_dir = tmp_path / "capco"
    capco_dir.mkdir()

    ns: dict = {
        "__name__": "test_capco_prep",
        "__file__": str(CAPCO_PREP_PATH),
    }
    source = CAPCO_PREP_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    ns["CAPCO_DIR"] = capco_dir
    return ns


def _file(capco_dir: Path, name: str, content: str = "", age_days: int = 0) -> Path:
    """Create a file in capco_dir with optional age."""
    path = capco_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if age_days > 0:
        old_time = time.time() - age_days * 86400
        os.utime(path, (old_time, old_time))
    return path


# ── File basics ────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert CAPCO_PREP_PATH.exists()

    def test_shebang(self):
        first = CAPCO_PREP_PATH.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        content = CAPCO_PREP_PATH.read_text()
        assert '"""' in content
        assert "Capco" in content or "CAPCO" in content


# ── Constants ─────────────────────────────────────────────────────────────


class TestConstants:
    def test_stale_days(self, cp):
        assert cp["STALE_DAYS"] == 90

    def test_supported_extensions(self, cp):
        exts = cp["SUPPORTED_EXTENSIONS"]
        assert ".pdf" in exts
        assert ".docx" in exts
        assert ".md" in exts
        assert ".csv" in exts
        assert ".xlsx" in exts

    def test_capco_dir_set(self, cp, tmp_path):
        assert cp["CAPCO_DIR"] == tmp_path / "capco"


# ── get_file_info ─────────────────────────────────────────────────────────


class TestGetFileInfo:
    def test_basic_file(self, cp, tmp_path):
        f = _file(tmp_path / "capco", "test.md", "x" * 2048)
        info = cp["get_file_info"](f)
        assert info["name"] == "test.md"
        assert info["size_kb"] > 0
        assert info["is_stale"] is False
        assert info["days_since_modified"] == 0

    def test_stale_file(self, cp, tmp_path):
        f = _file(tmp_path / "capco", "old.pdf", "x", age_days=100)
        info = cp["get_file_info"](f)
        assert info["is_stale"] is True
        assert info["days_since_modified"] >= 90

    def test_fresh_file(self, cp, tmp_path):
        f = _file(tmp_path / "capco", "new.docx", "content")
        info = cp["get_file_info"](f)
        assert info["is_stale"] is False

    def test_size_calculation(self, cp, tmp_path):
        f = _file(tmp_path / "capco", "sized.txt", "x" * 2048)
        info = cp["get_file_info"](f)
        assert info["size_kb"] >= 1.9


# ── list_capco_docs ───────────────────────────────────────────────────────


class TestListCapcoDocs:
    def test_empty_dir(self, cp, capsys):
        docs = cp["list_capco_docs"]()
        assert docs == []

    def test_nonexistent_dir(self, cp, tmp_path, capsys):
        cp["CAPCO_DIR"] = tmp_path / "nonexistent"
        docs = cp["list_capco_docs"]()
        assert docs == []
        out = capsys.readouterr().out
        assert "does not exist" in out

    def test_lists_supported_files(self, cp, tmp_path):
        capco = tmp_path / "capco"
        _file(capco, "a.pdf", "pdf content")
        _file(capco, "b.docx", "docx content")
        _file(capco, "c.md", "# Notes")
        docs = cp["list_capco_docs"]()
        names = {d["name"] for d in docs}
        assert names == {"a.pdf", "b.docx", "c.md"}

    def test_ignores_unsupported_extensions(self, cp, tmp_path):
        capco = tmp_path / "capco"
        _file(capco, "image.png", "png")
        _file(capco, "script.sh", "#!/bin/bash")
        _file(capco, "data.json", "{}")
        docs = cp["list_capco_docs"]()
        assert docs == []

    def test_sorted_newest_first(self, cp, tmp_path):
        capco = tmp_path / "capco"
        _file(capco, "old.txt", "old", age_days=30)
        time.sleep(0.1)
        _file(capco, "new.txt", "new")
        docs = cp["list_capco_docs"]()
        assert docs[0]["name"] == "new.txt"
        assert docs[1]["name"] == "old.txt"

    def test_walks_subdirectories(self, cp, tmp_path):
        capco = tmp_path / "capco"
        _file(capco / "sub", "nested.pdf", "nested")
        docs = cp["list_capco_docs"]()
        assert len(docs) == 1
        assert docs[0]["name"] == "nested.pdf"

    def test_mixed_fresh_and_stale(self, cp, tmp_path):
        capco = tmp_path / "capco"
        _file(capco, "fresh.pdf", "f")
        _file(capco, "stale.pdf", "s", age_days=100)
        docs = cp["list_capco_docs"]()
        stale_count = sum(1 for d in docs if d["is_stale"])
        fresh_count = sum(1 for d in docs if not d["is_stale"])
        assert stale_count == 1
        assert fresh_count == 1


# ── print_readiness_checklist ──────────────────────────────────────────────


class TestReadinessChecklist:
    def test_prints_header(self, cp, capsys):
        cp["print_readiness_checklist"]([])
        out = capsys.readouterr().out
        assert "CAPCO Preparation - Readiness Checklist" in out
        assert "Total documents found: 0" in out

    def test_prints_stale_docs(self, cp, capsys):
        docs = [
            {
                "name": "old.pdf",
                "modified": datetime.now(),
                "days_since_modified": 100,
                "size_kb": 5.0,
                "is_stale": True,
            }
        ]
        cp["print_readiness_checklist"](docs)
        out = capsys.readouterr().out
        assert "Stale Documents" in out
        assert "old.pdf" in out

    def test_prints_fresh_docs(self, cp, capsys):
        docs = [
            {
                "name": "new.pdf",
                "modified": datetime.now(),
                "days_since_modified": 5,
                "size_kb": 3.0,
                "is_stale": False,
            }
        ]
        cp["print_readiness_checklist"](docs)
        out = capsys.readouterr().out
        assert "Fresh Documents" in out
        assert "new.pdf" in out

    def test_checklist_items(self, cp, capsys):
        cp["print_readiness_checklist"]([])
        out = capsys.readouterr().out
        assert "Readiness Checklist" in out
        # When no docs, the "All required" item should show ❌
        assert "❌" in out

    def test_checkmark_when_docs_exist(self, cp, capsys):
        docs = [
            {
                "name": "ok.pdf",
                "modified": datetime.now(),
                "days_since_modified": 1,
                "size_kb": 2.0,
                "is_stale": False,
            }
        ]
        cp["print_readiness_checklist"](docs)
        out = capsys.readouterr().out
        assert "All required CAPCO documents are added" in out

    def test_limits_fresh_display_to_10(self, cp, capsys):
        docs = [
            {
                "name": f"doc{i}.pdf",
                "modified": datetime.now(),
                "days_since_modified": 1,
                "size_kb": 1.0,
                "is_stale": False,
            }
            for i in range(15)
        ]
        cp["print_readiness_checklist"](docs)
        out = capsys.readouterr().out
        assert "more" in out

    def test_next_steps_with_stale(self, cp, capsys):
        docs = [
            {
                "name": "old.pdf",
                "modified": datetime.now(),
                "days_since_modified": 100,
                "size_kb": 1.0,
                "is_stale": True,
            }
        ]
        cp["print_readiness_checklist"](docs)
        out = capsys.readouterr().out
        assert "stale" in out.lower()


# ── main ──────────────────────────────────────────────────────────────────


class TestMain:
    def test_empty_dir_exits_1(self, cp, capsys):
        with pytest.raises(SystemExit) as exc_info:
            cp["main"]()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "Total documents found: 0" in out

    def test_stale_docs_exits_1(self, cp, tmp_path, capsys):
        capco = tmp_path / "capco"
        _file(capco, "stale.pdf", "old", age_days=100)
        with pytest.raises(SystemExit) as exc_info:
            cp["main"]()
        assert exc_info.value.code == 1

    def test_all_fresh_exits_0(self, cp, tmp_path, capsys):
        capco = tmp_path / "capco"
        _file(capco, "fresh.pdf", "new")
        with pytest.raises(SystemExit) as exc_info:
            cp["main"]()
        assert exc_info.value.code == 0

    def test_mixed_exits_1(self, cp, tmp_path, capsys):
        capco = tmp_path / "capco"
        _file(capco, "fresh.pdf", "new")
        _file(capco, "stale.pdf", "old", age_days=100)
        with pytest.raises(SystemExit) as exc_info:
            cp["main"]()
        assert exc_info.value.code == 1


# ── CLI subprocess tests ──────────────────────────────────────────────────


class TestCLI:
    def test_runs_and_reports(self):
        result = subprocess.run(
            [sys.executable, str(CAPCO_PREP_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Will exit 1 because chromatin/Capco likely doesn't exist
        assert "CAPCO Preparation" in result.stdout or "does not exist" in result.stdout
