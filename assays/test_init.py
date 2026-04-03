"""Tests for metabolon.gastrulation.init."""
from __future__ import annotations

import click
import pytest
from pathlib import Path

from metabolon.gastrulation.init import _to_module, scaffold_project


# ---------------------------------------------------------------------------
# _to_module
# ---------------------------------------------------------------------------

class TestToModule:
    def test_hyphens_to_underscores(self):
        assert _to_module("my-cool-project") == "my_cool_project"

    def test_no_hyphens_unchanged(self):
        assert _to_module("simple") == "simple"

    def test_multiple_hyphens(self):
        assert _to_module("a-b-c-d") == "a_b_c_d"

    def test_already_underscored(self):
        assert _to_module("already_fine") == "already_fine"


# ---------------------------------------------------------------------------
# scaffold_project
# ---------------------------------------------------------------------------

class TestScaffoldProject:
    def test_creates_directory_tree(self, tmp_path: Path):
        target = tmp_path / "my-server"
        scaffold_project("my-server", target, "A test server")
        assert (target / "src" / "my_server" / "enzymes").is_dir()
        assert (target / "src" / "my_server" / "codons").is_dir()
        assert (target / "src" / "my_server" / "resources").is_dir()
        assert (target / "src" / "my_server" / "morphology").is_dir()
        assert (target / "assays").is_dir()

    def test_creates_init_py_files(self, tmp_path: Path):
        target = tmp_path / "my-server"
        scaffold_project("my-server", target, "A test server")
        src = target / "src" / "my_server"
        for pkg in [src, src / "enzymes", src / "codons", src / "resources", src / "morphology"]:
            assert (pkg / "__init__.py").exists(), f"Missing {pkg / '__init__.py'}"

    def test_renders_pyproject_toml(self, tmp_path: Path):
        target = tmp_path / "demo-app"
        scaffold_project("demo-app", target, "Demo description")
        content = (target / "pyproject.toml").read_text()
        assert 'name = "demo-app"' in content
        assert 'description = "Demo description"' in content

    def test_renders_server_py(self, tmp_path: Path):
        target = tmp_path / "demo-app"
        scaffold_project("demo-app", target, "Demo description")
        content = (target / "src" / "demo_app" / "server.py").read_text()
        assert "demo_app" in content
        assert "demo-app" in content

    def test_renders_init_with_version(self, tmp_path: Path):
        target = tmp_path / "demo-app"
        scaffold_project("demo-app", target, "Demo description")
        content = (target / "src" / "demo_app" / "__init__.py").read_text()
        assert 'demo-app' in content
        assert "Demo description" in content
        assert '__version__ = "0.1.0"' in content

    def test_renders_main_py(self, tmp_path: Path):
        target = tmp_path / "my-srv"
        scaffold_project("my-srv", target, "Desc")
        content = (target / "src" / "my_srv" / "__main__.py").read_text()
        assert "my_srv" in content

    def test_renders_test_handshake(self, tmp_path: Path):
        target = tmp_path / "my-srv"
        scaffold_project("my-srv", target, "Desc")
        content = (target / "assays" / "test_handshake.py").read_text()
        assert "my_srv" in content
        assert "my-srv" in content

    def test_returns_target_path(self, tmp_path: Path):
        target = tmp_path / "proj"
        result = scaffold_project("proj", target, "Desc")
        assert result == target

    def test_non_empty_target_raises(self, tmp_path: Path):
        target = tmp_path / "existing"
        target.mkdir()
        (target / "file.txt").write_text("occupied")
        with pytest.raises(click.ClickException, match="already exists and is not empty"):
            scaffold_project("proj", target, "Desc")

    def test_empty_existing_target_ok(self, tmp_path: Path):
        target = tmp_path / "existing"
        target.mkdir()
        # Empty dir should be fine
        result = scaffold_project("proj", target, "Desc")
        assert (result / "pyproject.toml").exists()
