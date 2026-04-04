from __future__ import annotations

"""Tests for complement — convergent detection organelle."""

import json
from unittest.mock import patch

import pytest


class TestAssembleMac:
    def test_no_hits_when_clean(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac

        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"),
            patch("metabolon.organelles.complement.recall_infections", return_value=[]),
        ):
            hits = assemble_mac()
        assert hits == []

    def test_infection_only(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac

        infections = [{"tool": "broken_tool", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"),
            patch("metabolon.organelles.complement.recall_infections", return_value=infections),
        ):
            hits = assemble_mac()
        assert len(hits) == 1
        assert hits[0]["convergent"] is False
        assert hits[0]["infection_count"] == 1

    def test_convergent_detection(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac

        priming = {"broken_tool": 3}
        priming_path = tmp_path / "priming.json"
        priming_path.write_text(json.dumps(priming))
        infections = [{"tool": "broken_tool", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", priming_path),
            patch("metabolon.organelles.complement.recall_infections", return_value=infections),
        ):
            hits = assemble_mac()
        convergent_hits = [h for h in hits if h["key"] == "broken_tool"]
        assert len(convergent_hits) == 1
        assert convergent_hits[0]["convergent"] is True
        assert convergent_hits[0]["probe_consecutive_fails"] == 3

    def test_suppressed_keys(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac

        infections = [{"tool": "chromatin", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"),
            patch("metabolon.organelles.complement.recall_infections", return_value=infections),
        ):
            hits = assemble_mac()
        chromatin_hits = [h for h in hits if h["key"] == "chromatin"]
        assert len(chromatin_hits) == 1
        assert chromatin_hits[0]["resolution"] == "suppress"

    def test_healed_infections_excluded(self, tmp_path):
        from metabolon.organelles.complement import assemble_mac

        infections = [{"tool": "healed_tool", "healed": True, "ts": "2026-03-30T10:00:00"}]
        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"),
            patch("metabolon.organelles.complement.recall_infections", return_value=infections),
        ):
            hits = assemble_mac()
        assert all(h["key"] != "healed_tool" for h in hits)


class TestResolve:
    def test_quiescent_when_clean(self, tmp_path):
        from metabolon.organelles.complement import resolve

        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"),
            patch("metabolon.organelles.complement.recall_infections", return_value=[]),
            patch("metabolon.organelles.complement.record_event"),
            patch("metabolon.organelles.complement.log"),
        ):
            result = resolve()
        assert result["status"] == "quiescent"

    def test_active_with_hits(self, tmp_path):
        from metabolon.organelles.complement import resolve

        infections = [{"tool": "real_problem", "healed": False, "ts": "2026-03-30T10:00:00"}]
        with (
            patch("metabolon.organelles.complement._PRIMING_PATH", tmp_path / "priming.json"),
            patch("metabolon.organelles.complement.recall_infections", return_value=infections),
            patch("metabolon.organelles.complement.record_event"),
            patch("metabolon.organelles.complement.log"),
        ):
            result = resolve()
        assert result["status"] == "active"
        assert result["hits"] >= 1


class TestCoverageSummary:
    def test_empty_project_returns_zero_coverage(self, tmp_path):
        """When no metabolon directory exists, coverage is 0."""
        from metabolon.organelles.complement import coverage_summary

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 0
        assert result["covered_modules"] == 0
        assert result["coverage_ratio"] == 0.0
        assert result["modules"] == []

    def test_single_module_with_test(self, tmp_path):
        """A module with a corresponding test file is counted as covered."""
        from metabolon.organelles.complement import coverage_summary

        # Create metabolon/subdir/module.py
        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "module.py").write_text("# module\n", encoding="utf-8")

        # Create assays/test_module.py
        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_module.py").write_text("# test\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 1
        assert result["covered_modules"] == 1
        assert result["coverage_ratio"] == 1.0

    def test_single_module_without_test(self, tmp_path):
        """A module without a corresponding test file is counted as uncovered."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "module.py").write_text("# module\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 1
        assert result["covered_modules"] == 0
        assert result["coverage_ratio"] == 0.0

    def test_ignores_init_py(self, tmp_path):
        """__init__.py files are not counted as modules."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "__init__.py").write_text("# init\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 0

    def test_ignores_private_files(self, tmp_path):
        """Files starting with _ (except __init__.py) are ignored."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "_private.py").write_text("# private\n", encoding="utf-8")
        (metabolon_sub / "public.py").write_text("# public\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 1
        assert result["modules"][0]["name"] == "public"

    def test_secondary_test_pattern(self, tmp_path):
        """Test files with pattern test_{subdir}_{module}.py also count."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "sortase"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "validator.py").write_text("# validator\n", encoding="utf-8")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_sortase_validator.py").write_text("# test\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 1
        assert result["covered_modules"] == 1
        module = result["modules"][0]
        assert module["has_test"] is True
        assert module["test_file"] == "test_sortase_validator.py"

    def test_multiple_modules_mixed_coverage(self, tmp_path):
        """Multiple modules with partial coverage."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "alpha.py").write_text("# alpha\n", encoding="utf-8")
        (metabolon_sub / "beta.py").write_text("# beta\n", encoding="utf-8")
        (metabolon_sub / "gamma.py").write_text("# gamma\n", encoding="utf-8")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_alpha.py").write_text("# test\n", encoding="utf-8")
        (assays_dir / "test_beta.py").write_text("# test\n", encoding="utf-8")
        # gamma has no test

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 3
        assert result["covered_modules"] == 2
        assert result["coverage_ratio"] == pytest.approx(2 / 3, rel=0.01)

    def test_ignores_dot_directories(self, tmp_path):
        """Directories starting with . are ignored."""
        from metabolon.organelles.complement import coverage_summary

        # Create .hidden directory with module
        hidden_dir = tmp_path / "metabolon" / ".hidden"
        hidden_dir.mkdir(parents=True)
        (hidden_dir / "secret.py").write_text("# secret\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 0

    def test_module_info_structure(self, tmp_path):
        """Each module has the expected dict structure."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "module.py").write_text("# module\n", encoding="utf-8")

        result = coverage_summary(project_root=tmp_path)
        assert len(result["modules"]) == 1
        mod = result["modules"][0]
        assert "module" in mod
        assert "name" in mod
        assert "has_test" in mod
        assert "test_file" in mod
        assert mod["module"] == "subdir/module.py"
        assert mod["name"] == "module"
        assert mod["has_test"] is False
        assert mod["test_file"] is None

    def test_no_assays_directory(self, tmp_path):
        """Works correctly when assays directory doesn't exist."""
        from metabolon.organelles.complement import coverage_summary

        metabolon_sub = tmp_path / "metabolon" / "subdir"
        metabolon_sub.mkdir(parents=True)
        (metabolon_sub / "module.py").write_text("# module\n", encoding="utf-8")

        # No assays directory created
        result = coverage_summary(project_root=tmp_path)
        assert result["total_modules"] == 1
        assert result["covered_modules"] == 0
