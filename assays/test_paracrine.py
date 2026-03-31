"""Tests for effectors/paracrine — lateral inhibition for feedback memories."""
from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "effectors" / "paracrine"
    loader = SourceFileLoader("paracrine", str(module_path))
    spec = importlib.util.spec_from_loader("paracrine", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_memory(name: str, body: str, description: str = "") -> dict:
    return {
        "file": f"feedback_{name}.md",
        "name": name,
        "description": description,
        "body": body,
        "full_text": f"{name} {description} {body}".lower(),
    }


# ── Unit tests: cluster_by_axis ──────────────────────────────────────────


class TestClusterByAxis:
    def test_empty_memories(self):
        mod = _load_module()
        assert mod.cluster_by_axis([]) == {}

    def test_single_memory_single_axis(self):
        mod = _load_module()
        mem = _make_memory(" terse-mode", "Be terse and concise in all responses.")
        clusters = mod.cluster_by_axis([mem])
        assert "verbosity" in clusters
        assert len(clusters["verbosity"]) == 1

    def test_memory_matches_multiple_axes(self):
        mod = _load_module()
        mem = _make_memory(
            "fast-careful",
            "Be fast and act immediately, but also verify and check your work carefully.",
        )
        clusters = mod.cluster_by_axis([mem])
        assert "speed_vs_quality" in clusters
        assert len(clusters["speed_vs_quality"]) == 1

    def test_no_matching_axis(self):
        mod = _load_module()
        mem = _make_memory("random", "Eat lunch at noon today.")
        clusters = mod.cluster_by_axis([mem])
        # May or may not match; key is it shouldn't crash
        assert isinstance(clusters, dict)

    def test_autonomy_keywords(self):
        mod = _load_module()
        mem = _make_memory("auto", "Just do it autonomously without asking.")
        clusters = mod.cluster_by_axis([mem])
        assert "autonomy" in clusters

    def test_routing_keywords(self):
        mod = _load_module()
        mem = _make_memory("router", "Use sonnet for simple tasks, opus for complex ones.")
        clusters = mod.cluster_by_axis([mem])
        assert "routing" in clusters


# ── Unit tests: detect_tensions ──────────────────────────────────────────


class TestDetectTensions:
    def test_no_tensions_single_side(self):
        mod = _load_module()
        mem = _make_memory("go", "Just do it autonomously without asking anyone.")
        clusters = mod.cluster_by_axis([mem])
        tensions = mod.detect_tensions(clusters)
        assert tensions == []

    def test_autonomy_tension(self):
        mod = _load_module()
        do_it = _make_memory("act", "Just do it, stop asking for permission, act and report.")
        hold = _make_memory("gate", "Hold and use judgment, calibrate before acting, confirm first.")
        clusters = mod.cluster_by_axis([do_it, hold])
        tensions = mod.detect_tensions(clusters)
        assert len(tensions) >= 1
        assert tensions[0]["axis"] == "autonomy"
        assert tensions[0]["label_a"] == "act immediately"
        assert tensions[0]["label_b"] == "gate on judgment"

    def test_speed_vs_quality_tension(self):
        mod = _load_module()
        fast = _make_memory("fast", "Reply immediately, be quick and fast about it.")
        careful = _make_memory("slow", "Verify and validate, research before acting, be thorough.")
        clusters = mod.cluster_by_axis([fast, careful])
        tensions = mod.detect_tensions(clusters)
        speed_tensions = [t for t in tensions if t["axis"] == "speed_vs_quality"]
        assert len(speed_tensions) == 1

    def test_capture_vs_flow_tension(self):
        mod = _load_module()
        capture = _make_memory("save", "Capture and save everything, remember all context.")
        flow = _make_memory("flow", "Protect flow state and thread, don't cut energy.")
        clusters = mod.cluster_by_axis([capture, flow])
        tensions = mod.detect_tensions(clusters)
        cap_tensions = [t for t in tensions if t["axis"] == "capture_vs_flow"]
        assert len(cap_tensions) == 1

    def test_empty_clusters(self):
        mod = _load_module()
        assert mod.detect_tensions({}) == []

    def test_tension_count(self):
        mod = _load_module()
        do_it = _make_memory("act", "Just do it, stop asking for permission, act and report.")
        hold = _make_memory("gate", "Hold and use judgment, calibrate before acting, confirm first.")
        clusters = mod.cluster_by_axis([do_it, hold])
        tensions = mod.detect_tensions(clusters)
        assert tensions[0]["count"] == 2


# ── Unit tests: load_feedback_memories ───────────────────────────────────


class TestLoadFeedbackMemories:
    def test_empty_dir(self, monkeypatch, tmp_path):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        assert mod.load_feedback_memories() == []

    def test_loads_with_frontmatter(self, monkeypatch, tmp_path):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        content = "---\nname: test-fb\ndescription: A test feedback\n---\nSome body text"
        (mem_dir / "feedback_test.md").write_text(content)
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        result = mod.load_feedback_memories()
        assert len(result) == 1
        assert result[0]["name"] == "test-fb"
        assert result[0]["description"] == "A test feedback"
        assert "Some body text" in result[0]["body"]

    def test_loads_without_frontmatter(self, monkeypatch, tmp_path):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "feedback_plain.md").write_text("Just plain text without frontmatter.")
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        result = mod.load_feedback_memories()
        assert len(result) == 1
        assert result[0]["name"] == "feedback_plain"

    def test_handles_broken_yaml(self, monkeypatch, tmp_path):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        content = "---\n: invalid yaml {{\n---\nbody here"
        (mem_dir / "feedback_broken.md").write_text(content)
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        result = mod.load_feedback_memories()
        assert len(result) == 1
        # Should gracefully handle broken YAML
        assert "body here" in result[0]["body"]


# ── Unit tests: reconcile_tension ────────────────────────────────────────


class TestReconcileTension:
    def test_returns_llm_output(self, monkeypatch):
        mod = _load_module()
        tension = {
            "axis": "autonomy",
            "pull_a": ["feedback_act.md"],
            "pull_b": ["feedback_gate.md"],
            "label_a": "act immediately",
            "label_b": "gate on judgment",
            "count": 2,
        }
        memories = [
            _make_memory("act", "Just do it autonomously."),
            _make_memory("gate", "Hold and confirm first."),
        ]

        mock_result = MagicMock()
        mock_result.stdout = "FALSE POSITIVE: both refer to different contexts"
        mock_result.stderr = ""
        monkeypatch.setattr(
            mod.subprocess, "run",
            lambda *a, **kw: mock_result,
        )
        result = mod.reconcile_tension(tension, memories)
        assert "FALSE POSITIVE" in result

    def test_handles_timeout(self, monkeypatch):
        mod = _load_module()
        tension = {
            "axis": "speed_vs_quality",
            "pull_a": ["feedback_fast.md"],
            "pull_b": ["feedback_careful.md"],
            "label_a": "act fast",
            "label_b": "verify first",
            "count": 2,
        }
        memories = [_make_memory("fast", "Be fast."), _make_memory("careful", "Be thorough.")]

        import subprocess as sp
        monkeypatch.setattr(
            mod.subprocess, "run",
            side_effect := sp.TimeoutExpired("cmd", 60),
        )
        # Need to re-raise, not use side_effect — let's patch differently
        monkeypatch.setattr(
            mod.subprocess, "run",
            MagicMock(side_effect=sp.TimeoutExpired("channel", 60)),
        )
        result = mod.reconcile_tension(tension, memories)
        assert "ERROR" in result


# ── Integration: main with mocks ─────────────────────────────────────────


class TestMain:
    def test_main_shows_clusters(self, monkeypatch, tmp_path, capsys):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "feedback_test.md").write_text(
            "---\nname: terse\n---\nBe concise and terse."
        )
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog"]))
        mod.main()
        captured = capsys.readouterr()
        assert "Loaded 1 feedback memories" in captured.out

    def test_main_cluster_flag(self, monkeypatch, tmp_path, capsys):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "feedback_test.md").write_text(
            "---\nname: terse\n---\nBe concise and terse."
        )
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog", "--cluster"]))
        mod.main()
        captured = capsys.readouterr()
        assert "verbosity" in captured.out

    def test_main_json_output(self, monkeypatch, tmp_path, capsys):
        mod = _load_module()
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "feedback_test.md").write_text(
            "---\nname: terse\n---\nBe concise and terse."
        )
        monkeypatch.setattr(mod, "MEMORY_DIR", mem_dir)
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog", "--json"]))
        mod.main()
        import json
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total" in data
        assert "clusters" in data
        assert "tensions" in data
        assert data["total"] == 1
