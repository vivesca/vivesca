from __future__ import annotations
"""Tests for gemmation — background agent job queue."""

from pathlib import Path

import pytest
import yaml


class TestLoadQueue:
    def test_empty_file(self, tmp_path):
        from metabolon.organelles.gemmation import _load_queue
        q = tmp_path / "queue.yaml"
        q.write_text("")
        assert _load_queue(q) == []

    def test_nonexistent_file(self, tmp_path):
        from metabolon.organelles.gemmation import _load_queue
        assert _load_queue(tmp_path / "nope.yaml") == []

    def test_loads_tasks(self, tmp_path):
        from metabolon.organelles.gemmation import _load_queue
        q = tmp_path / "queue.yaml"
        q.write_text(yaml.dump({"tasks": [{"name": "test", "prompt": "do stuff"}]}))
        tasks = _load_queue(q)
        assert len(tasks) == 1
        assert tasks[0]["name"] == "test"


class TestSaveQueue:
    def test_roundtrip(self, tmp_path):
        from metabolon.organelles.gemmation import _load_queue, _save_queue
        q = tmp_path / "queue.yaml"
        tasks = [{"name": "task1", "prompt": "hello"}]
        _save_queue(tasks, q)
        loaded = _load_queue(q)
        assert len(loaded) == 1
        assert loaded[0]["name"] == "task1"

    def test_creates_parent_dirs(self, tmp_path):
        from metabolon.organelles.gemmation import _save_queue
        q = tmp_path / "sub" / "dir" / "queue.yaml"
        _save_queue([{"name": "t"}], q)
        assert q.exists()


class TestFindTask:
    def test_finds_by_name(self):
        from metabolon.organelles.gemmation import _find_task
        tasks = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        assert _find_task(tasks, "b")["name"] == "b"

    def test_raises_on_missing(self):
        from metabolon.organelles.gemmation import _find_task
        with pytest.raises(ValueError, match="not found"):
            _find_task([{"name": "a"}], "z")


class TestListTasks:
    def test_empty_queue(self, tmp_path):
        from metabolon.organelles.gemmation import list_tasks
        q = tmp_path / "queue.yaml"
        q.write_text("")
        assert "No tasks" in list_tasks(q)

    def test_formats_tasks(self, tmp_path):
        from metabolon.organelles.gemmation import list_tasks
        q = tmp_path / "queue.yaml"
        q.write_text(yaml.dump({"tasks": [
            {"name": "audit", "backend": "goose", "timeout": 300, "schedule": "0 6 * * *"},
        ]}))
        output = list_tasks(q)
        assert "audit" in output
        assert "goose" in output


class TestPrependCoaching:
    def test_no_file(self, tmp_path):
        from metabolon.organelles.gemmation import _prepend_coaching
        import metabolon.organelles.gemmation as gem
        from unittest.mock import patch
        with patch.object(gem, "_COACHING_NOTES", tmp_path / "nope.md"):
            assert _prepend_coaching("do stuff") == "do stuff"

    def test_prepends_coaching(self, tmp_path):
        from metabolon.organelles.gemmation import _prepend_coaching
        import metabolon.organelles.gemmation as gem
        from unittest.mock import patch
        coaching = tmp_path / "coaching.md"
        coaching.write_text("---\nfrontmatter\n---\nDon't hallucinate.")
        with patch.object(gem, "_COACHING_NOTES", coaching):
            result = _prepend_coaching("do stuff")
        assert "Don't hallucinate" in result
        assert "do stuff" in result


class TestBuildCmd:
    def test_goose_backend(self):
        from metabolon.organelles.gemmation import _build_cmd
        task = {"name": "t", "prompt": "hello", "backend": "goose"}
        cmd = _build_cmd(task, Path("/tmp/out"))
        assert cmd[0] == "goose"
        assert "run" in cmd

    def test_codex_backend(self):
        from metabolon.organelles.gemmation import _build_cmd
        task = {"name": "t", "prompt": "hello", "backend": "codex"}
        cmd = _build_cmd(task, Path("/tmp/out"))
        assert cmd[0] == "codex"

    def test_unknown_raises(self):
        from metabolon.organelles.gemmation import _build_cmd
        with pytest.raises(ValueError, match="Unknown backend"):
            _build_cmd({"name": "t", "prompt": "x", "backend": "nope"}, Path("/tmp"))
