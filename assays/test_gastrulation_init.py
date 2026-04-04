from __future__ import annotations

"""Tests for metabolon/gastrulation/init.py."""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.gastrulation.init import (
    _to_module,
    scaffold_project,
)


class TestToModule:
    """Tests for _to_module helper."""

    def test_converts_hyphens_to_underscores(self) -> None:
        """Should replace hyphens with underscores."""
        assert _to_module("my-project") == "my_project"

    def test_leaves_underscores_unchanged(self) -> None:
        """Should not modify existing underscores."""
        assert _to_module("my_project") == "my_project"

    def test_handles_multiple_hyphens(self) -> None:
        """Should handle multiple hyphens."""
        assert _to_module("my-cool-project") == "my_cool_project"

    def test_no_hyphens(self) -> None:
        """Should leave names without hyphens unchanged."""
        assert _to_module("simple") == "simple"


class TestScaffoldProject:
    """Tests for scaffold_project function."""

    def _mock_env(self) -> MagicMock:
        """Create a mock Jinja2 environment."""
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "# generated content"
        mock_env.get_template.return_value = mock_template
        return mock_env

    def test_creates_directory_structure(self, tmp_path: Path) -> None:
        """Should create all required directories."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        src = target / "src" / "test_project"
        assert src.is_dir()
        assert (src / "enzymes").is_dir()
        assert (src / "codons").is_dir()
        assert (src / "resources").is_dir()
        assert (src / "morphology").is_dir()
        assert (target / "assays").is_dir()

    def test_creates_init_files(self, tmp_path: Path) -> None:
        """Should create __init__.py files in all packages."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        src = target / "src" / "test_project"
        for pkg_dir in [
            src,
            src / "enzymes",
            src / "codons",
            src / "resources",
            src / "morphology",
        ]:
            assert (pkg_dir / "__init__.py").exists()

    def test_raises_on_non_empty_directory(self, tmp_path: Path) -> None:
        """Should raise if target exists and is non-empty."""
        import click

        target = tmp_path / "existing"
        target.mkdir()
        (target / "file.txt").write_text("content")

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            with pytest.raises(click.ClickException, match="already exists and is not empty"):
                scaffold_project(
                    name="test-project",
                    target=target,
                    description="A test project",
                )

    def test_allows_empty_directory(self, tmp_path: Path) -> None:
        """Should allow target that exists but is empty."""
        target = tmp_path / "empty_dir"
        target.mkdir()

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            result = scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        assert result == target

    def test_renders_templates_with_context(self, tmp_path: Path) -> None:
        """Should render templates with correct context."""
        target = tmp_path / "new_project"
        mock_env = self._mock_env()

        with patch("metabolon.gastrulation.init._env", mock_env):
            scaffold_project(
                name="my-server",
                target=target,
                description="My MCP server",
            )

        # Check get_template calls
        template_calls = mock_env.get_template.call_args_list
        template_names = [c[0][0] for c in template_calls]

        expected_templates = [
            "project/pyproject.toml.j2",
            "project/server.py.j2",
            "project/__init__.py.j2",
            "project/__main__.py.j2",
            "project/test_handshake.py.j2",
        ]

        for expected in expected_templates:
            assert expected in template_names, f"Missing template: {expected}"

    def test_passes_correct_context(self, tmp_path: Path) -> None:
        """Should pass name, module, and description to templates."""
        target = tmp_path / "new_project"
        mock_env = self._mock_env()

        with patch("metabolon.gastrulation.init._env", mock_env):
            scaffold_project(
                name="my-cool-server",
                target=target,
                description="A cool MCP server",
            )

        # Check render context
        render_call = mock_env.get_template.return_value.render.call_args
        ctx = render_call[1] if render_call[1] else render_call[0][0]

        assert ctx["name"] == "my-cool-server"
        assert ctx["module"] == "my_cool_server"
        assert ctx["description"] == "A cool MCP server"

    def test_creates_pyproject_toml(self, tmp_path: Path) -> None:
        """Should create pyproject.toml."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        assert (target / "pyproject.toml").exists()

    def test_creates_server_py(self, tmp_path: Path) -> None:
        """Should create server.py."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        src = target / "src" / "test_project"
        assert (src / "server.py").exists()

    def test_creates_main_py(self, tmp_path: Path) -> None:
        """Should create __main__.py."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        src = target / "src" / "test_project"
        assert (src / "__main__.py").exists()

    def test_creates_handshake_test(self, tmp_path: Path) -> None:
        """Should create test_handshake.py."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        assert (target / "assays" / "test_handshake.py").exists()

    def test_returns_target_path(self, tmp_path: Path) -> None:
        """Should return the target path."""
        target = tmp_path / "new_project"

        with patch("metabolon.gastrulation.init._env", self._mock_env()):
            result = scaffold_project(
                name="test-project",
                target=target,
                description="A test project",
            )

        assert result == target


class TestScaffoldProjectIntegration:
    """Integration tests with actual templates."""

    def test_full_scaffold_with_real_templates(self, tmp_path: Path) -> None:
        """Should create a complete project with real templates."""
        target = tmp_path / "real_project"

        result = scaffold_project(
            name="weather-server",
            target=target,
            description="Weather MCP server",
        )

        assert result == target

        # Check directory structure
        src = target / "src" / "weather_server"
        assert src.is_dir()

        # Check files have actual content (not empty)
        pyproject = target / "pyproject.toml"
        content = pyproject.read_text()
        assert "weather-server" in content
        assert "Weather MCP server" in content

        server = src / "server.py"
        server_content = server.read_text()
        assert len(server_content) > 0

        # Check __init__.py has content (uses project name, not module name)
        init = src / "__init__.py"
        init_content = init.read_text()
        assert "weather-server" in init_content  # Template uses {{ name }} not {{ module }}
